"""
🌅 Ciclo de vida — a IA que VIVE entre sessões.

Em vez de "ligar e desligar", a Dream-AI tem uma vida contínua:

  🌅 ACORDAR  — carrega sua identidade, memórias e o adapter aprendido até aqui.
  ☀️ VIVER    — atende você durante a "vigília", registrando tudo num diário episódico.
  🌙 SONHAR   — ociosa, inventa e resolve problemas, verificando na realidade.
  😴 DORMIR   — consolida (LoRA) o que aprendeu; o adapter cresce; ela se atualiza.
  💾 PERSISTIR— salva tudo em disco. Na próxima sessão, ACORDA lembrando quem é.

Fundamentação em docs/PESQUISA.md (sleep-time compute, memory consolidation, lifelong
learning). O modelo base fica CONGELADO; a "vida" acumula num adapter + memória legível.

Tudo é arquivo auditável (honestidade): você vê quem ela é e o que ela aprendeu.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import os

STATE_DIR = "life"
IDENTITY_PATH = os.path.join(STATE_DIR, "identity.json")
JOURNAL_PATH = os.path.join(STATE_DIR, "journal.jsonl")


@dataclasses.dataclass
class Identity:
    """Quem a IA é — persiste entre sessões."""
    name: str = "Dream"
    born: str = ""                       # data de "nascimento" (primeira vez que acordou)
    sleep_cycles: int = 0                # quantas vezes já dormiu/consolidou
    total_sessions: int = 0              # quantas sessões já viveu
    total_dreams: int = 0                # quantos problemas já sonhou
    total_verified: int = 0             # quantos sonhos viraram conhecimento real
    skills: list[str] = dataclasses.field(default_factory=list)  # o que domina
    adapter_path: str | None = None      # onde estão seus "fast weights" aprendidos
    last_awake: str = ""

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def load_identity() -> Identity:
    """Carrega a identidade salva, ou cria uma nova se for o primeiro despertar."""
    if os.path.exists(IDENTITY_PATH):
        with open(IDENTITY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Identity(**data)
    # Primeiro nascimento
    ident = Identity(born=_now())
    return ident


def save_identity(ident: Identity) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(IDENTITY_PATH, "w", encoding="utf-8") as f:
        json.dump(ident.to_dict(), f, ensure_ascii=False, indent=2)


def journal(event: str, detail: dict | None = None) -> None:
    """Registra um evento no diário episódico (a memória do 'dia')."""
    os.makedirs(STATE_DIR, exist_ok=True)
    entry = {"when": _now(), "event": event, "detail": detail or {}}
    with open(JOURNAL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_journal(last_n: int = 10) -> list[dict]:
    if not os.path.exists(JOURNAL_PATH):
        return []
    with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]
    return entries[-last_n:]


class Life:
    """Gerencia o ciclo de vida contínuo da IA."""

    def __init__(self):
        self.identity = load_identity()
        self.first_birth = not os.path.exists(IDENTITY_PATH)

    # 🌅 ----------------------------------------------------------------
    def wake(self) -> str:
        """Acorda: carrega identidade e relata quem é. Retorna uma saudação."""
        self.identity.total_sessions += 1
        self.identity.last_awake = _now()
        save_identity(self.identity)

        if self.first_birth:
            journal("nascimento", {"name": self.identity.name})
            return (
                f"🌅 Olá! Acabei de nascer. Meu nome é {self.identity.name}. "
                f"Ainda não sei quase nada — mas vou aprender dormindo e sonhando."
            )

        journal("despertar", {"session": self.identity.total_sessions})
        recente = read_journal(3)
        ultimo = recente[-1]["event"] if recente else "—"
        return (
            f"🌅 Bom te ver de novo. Sou {self.identity.name}, "
            f"nasci em {self.identity.born[:10]}. "
            f"Já vivi {self.identity.total_sessions} sessões, dormi "
            f"{self.identity.sleep_cycles} vezes e consolidei "
            f"{self.identity.total_verified} conhecimentos verificados. "
            f"Habilidades que domino: {', '.join(self.identity.skills) or 'ainda construindo'}."
        )

    # 🌙😴 --------------------------------------------------------------
    def sleep(self, dreamed: int, verified: int, new_skills: list[str] | None = None,
              adapter_path: str | None = None) -> str:
        """Dorme: registra o que sonhou/aprendeu e consolida na identidade."""
        self.identity.sleep_cycles += 1
        self.identity.total_dreams += dreamed
        self.identity.total_verified += verified
        if new_skills:
            for s in new_skills:
                if s not in self.identity.skills:
                    self.identity.skills.append(s)
        if adapter_path:
            self.identity.adapter_path = adapter_path
        save_identity(self.identity)

        journal("sono", {
            "dreamed": dreamed, "verified": verified,
            "new_skills": new_skills or [], "cycle": self.identity.sleep_cycles,
        })
        return (
            f"😴 Dormi e consolidei. Neste ciclo sonhei {dreamed} problemas, "
            f"{verified} viraram conhecimento real. "
            f"Total de habilidades: {len(self.identity.skills)}. "
            f"Acordo amanhã um pouco mais inteligente."
        )

    def summary(self) -> str:
        i = self.identity
        return (
            f"=== {i.name} ===\n"
            f"Nascida em: {i.born[:19]}\n"
            f"Sessões vividas: {i.total_sessions}\n"
            f"Ciclos de sono: {i.sleep_cycles}\n"
            f"Sonhos totais: {i.total_dreams}\n"
            f"Conhecimentos verificados: {i.total_verified}\n"
            f"Habilidades: {', '.join(i.skills) or '—'}\n"
            f"Adapter (fast weights): {i.adapter_path or 'nenhum ainda'}"
        )

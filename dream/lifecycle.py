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

from src import storage

# Os caminhos são resolvidos via storage (Google Drive quando disponível), de forma
# preguiçosa — assim, montar o Drive antes de usar já direciona tudo pra lá.
def _identity_path() -> str:
    return storage.resolve("life", "identity.json")


def _journal_path() -> str:
    return storage.resolve("life", "journal.jsonl")


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
    path = _identity_path()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # tolera campos novos/antigos
        known = {f.name for f in dataclasses.fields(Identity)}
        return Identity(**{k: v for k, v in data.items() if k in known})
    # Primeiro nascimento
    return Identity(born=_now())


def save_identity(ident: Identity) -> None:
    path = _identity_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ident.to_dict(), f, ensure_ascii=False, indent=2)


def journal(event: str, detail: dict | None = None) -> None:
    """Registra um evento no diário episódico (a memória do 'dia')."""
    entry = {"when": _now(), "event": event, "detail": detail or {}}
    with open(_journal_path(), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_journal(last_n: int = 10) -> list[dict]:
    path = _journal_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]
    return entries[-last_n:]


class Life:
    """Gerencia o ciclo de vida contínuo da IA."""

    def __init__(self):
        self.identity = load_identity()
        self.first_birth = not os.path.exists(_identity_path())

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
            f"Adapter (fast weights): {i.adapter_path or 'nenhum ainda'}\n"
            f"{storage.status()}"
        )

    # 🪞 ----------------------------------------------------------------
    def self_description(self) -> str:
        """
        AUTOCONSCIÊNCIA: descrição do próprio estado interno, em 1ª pessoa.

        Isto é injetado no contexto do modelo (system prompt) para que ele tenha
        ciência de quem é, do que já aprendeu e de como aprende — para se entender
        melhor e raciocinar sobre os próprios limites com honestidade.
        """
        i = self.identity
        taxa = (i.total_verified / i.total_dreams * 100) if i.total_dreams else 0.0
        skills = ", ".join(i.skills) if i.skills else "ainda estou construindo minhas habilidades"
        return (
            f"Quem eu sou (meu estado interno):\n"
            f"- Meu nome é {i.name}. Nasci em {i.born[:10]} e já vivi {i.total_sessions} sessões.\n"
            f"- Sou um modelo de ~1B de parâmetros especializado em programação.\n"
            f"- Aprendo dormindo: durante o sono eu SONHO problemas, tento resolvê-los e só\n"
            f"  aprendo com os que passam na execução real. Já dormi {i.sleep_cycles} vezes.\n"
            f"- Já sonhei {i.total_dreams} problemas; {i.total_verified} viraram conhecimento\n"
            f"  verificado (taxa de acerto dos meus sonhos: {taxa:.0f}%).\n"
            f"- Habilidades que domino de fato (verificadas): {skills}.\n"
            f"- Por construção, prefiro dizer 'não sei' a inventar. Meu conhecimento tem\n"
            f"  limites e eu tenho ciência deles: o que não está nas minhas habilidades\n"
            f"  verificadas, eu trato com cautela e honestidade."
        )

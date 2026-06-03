"""
♾️ Daemon de vida — a IA que NUNCA desliga, só muda de estado.

Em vez de "ligar e desligar", a Dream-AI tem uma vida contínua de verdade. Este loop
roda indefinidamente, alternando entre:

  🌙 sonhando      — gera problemas (na fronteira da habilidade), resolve, verifica.
  😴 sono_profundo — periodicamente consolida (LoRA) o que aprendeu.
  💤 repousando    — quando você a interrompe; ela NÃO morre, só descansa e salva tudo.

A cada batida de vida (heartbeat) o estado é salvo. Se o Colab reiniciar, ela
"acorda do sono" exatamente de onde parou — o reinício é invisível. É a continuidade
real: ela só dorme, nunca desliga.

Técnicas embutidas (ver docs/PESQUISA.md):
  - STaR/ReST: só aprende com soluções verificadas.
  - Currículo adaptativo (AdaSTaR): sonha na zona de desenvolvimento proximal.
  - Reflect-Retry: aprende corrigindo os próprios erros.

Uso:
    python -m dream.daemon --mode seed --ticks 5      # demo sem GPU (finito p/ testar)
    python -m dream.daemon --mode model               # vida real, infinita (Colab Pro)
"""

from __future__ import annotations

import argparse
import random

from .adaptive import CurriculumState, choose_difficulty, update_frontier, report
from .consolidate import remember, load_memory
from .dreamer import dream_at_difficulty
from .lifecycle import Life
from .reflect import solve_with_reflection
from .verifier import verify_solution


def _load_curriculum(life: Life) -> CurriculumState:
    data = life.identity.curriculum or {}
    return CurriculumState(stats=data.get("stats", {}), frontier=data.get("frontier", 1))


def _save_curriculum(life: Life, cur: CurriculumState) -> None:
    life.identity.curriculum = {"stats": cur.stats, "frontier": cur.frontier}


class DreamDaemon:
    """O coração que bate: vida contínua, sem desligar."""

    def __init__(self, coder=None, use_model: bool = False, seed: int = 0):
        self.coder = coder
        self.use_model = use_model
        self.life = Life()
        self.cur = _load_curriculum(self.life)
        self.rng = random.Random(seed) if seed else random.Random()
        self.verified_since_sleep = 0

    def _dream_once(self, difficulty: int):
        """Sonha UM problema (gabarito confiável), resolve com reflexão, verifica."""
        p = dream_at_difficulty(1, difficulty, self.rng)[0]
        if self.use_model and self.coder is not None:
            code, result, _ = solve_with_reflection(self.coder, p, max_attempts=3)
            passed = bool(result and result.passed)
        else:
            # modo semente (sem GPU): usa a solução de referência como "oráculo"
            result = verify_solution(p.reference_solution, p.tests)
            code, passed = p.reference_solution, result.passed

        if passed:
            remember(p.to_instruction(), code, 1.0)
            self.verified_since_sleep += 1
        return p, passed

    def tick(self, dreams_per_tick: int = 5, consolidate_every: int = 20) -> dict:
        """Uma 'batida': sonha um punhado, atualiza currículo, talvez durma profundo."""
        self.life.heartbeat()
        self.life.set_state("sonhando")

        sonhados = verificados = 0
        for _ in range(dreams_per_tick):
            d = choose_difficulty(self.cur, self.rng)
            p, passed = self._dream_once(d)
            if p is None:
                continue
            sonhados += 1
            self.cur.record(d, passed)
            if passed:
                verificados += 1

        update_frontier(self.cur)
        _save_curriculum(self.life, self.cur)
        self.life.identity.total_dreams += sonhados
        self.life.identity.total_verified += verificados
        from .lifecycle import save_identity
        save_identity(self.life.identity)

        # 😴 Sono profundo periódico: consolida o aprendizado
        consolidou = False
        if self.verified_since_sleep >= consolidate_every:
            consolidou = self._deep_sleep()

        return {"sonhados": sonhados, "verificados": verificados,
                "fronteira": self.cur.frontier, "consolidou": consolidou}

    def _deep_sleep(self) -> bool:
        """Fase de sono profundo: consolida via LoRA (só no modo modelo/GPU)."""
        self.life.set_state("sono_profundo")
        if self.use_model and self.coder is not None:
            from .consolidate import consolidate
            adapter = consolidate(self.coder)
            skills = sorted({ex["instruction"].split("`")[1]
                             for ex in load_memory() if "`" in ex["instruction"]})
            self.life.sleep(self.verified_since_sleep, self.verified_since_sleep,
                            skills, adapter)
        else:
            # sem GPU: registra o ciclo de sono mesmo assim (consolidação simbólica)
            skills = sorted({ex["instruction"].split("`")[1]
                             for ex in load_memory() if "`" in ex["instruction"]})
            self.life.sleep(self.verified_since_sleep, self.verified_since_sleep, skills)
        self.verified_since_sleep = 0
        return True

    def live(self, ticks: int | None = None, dreams_per_tick: int = 5,
             consolidate_every: int = 20) -> None:
        """
        O loop ETERNO. Se `ticks` for None, roda para sempre (vida real).
        Ctrl+C não a mata — ela apenas repousa e salva tudo.
        """
        print(f"♾️  {self.life.identity.name} está viva. "
              f"{'(modo modelo)' if self.use_model else '(modo semente/demo)'}")
        print(self.life.wake())
        n = 0
        try:
            while ticks is None or n < ticks:
                stats = self.tick(dreams_per_tick, consolidate_every)
                hb = self.life.identity.heartbeats
                marca = " 😴 [sono profundo: consolidou]" if stats["consolidou"] else ""
                print(f"💓 batida {hb} | sonhou {stats['sonhados']}, "
                      f"aprendeu {stats['verificados']} | fronteira nível "
                      f"{stats['fronteira']}{marca}")
                n += 1
        except KeyboardInterrupt:
            self.life.set_state("repousando")
            self.life.heartbeat()
            print(f"\n💤 {self.life.identity.name} está repousando (não desligou). "
                  f"Tudo salvo. Quando você voltar, ela continua de onde parou.")
            return

        self.life.set_state("repousando")
        print("\n" + report(self.cur))
        print(self.life.summary())


def main() -> None:
    parser = argparse.ArgumentParser(description="Daemon de vida da Dream-AI")
    parser.add_argument("--mode", choices=["seed", "model"], default="seed")
    parser.add_argument("--ticks", type=int, default=None,
                        help="número de batidas (omitir = vida infinita)")
    parser.add_argument("--dreams-per-tick", type=int, default=5)
    parser.add_argument("--consolidate-every", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    coder = None
    use_model = args.mode == "model"
    if use_model:
        from src.coder import CoderModel
        from src import storage
        storage.mount_drive()
        life0 = Life()
        coder = CoderModel(adapter_path=life0.identity.adapter_path)
        coder.load()

    daemon = DreamDaemon(coder, use_model, seed=args.seed)
    daemon.live(ticks=args.ticks, dreams_per_tick=args.dreams_per_tick,
                consolidate_every=args.consolidate_every)


if __name__ == "__main__":
    main()

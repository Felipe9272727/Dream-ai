"""
🌙 O Ciclo do Sonho — orquestra vigília → sonho → sono.

Este é o coração do Dream-AI: o loop de auto-aprimoramento.

  ☀️  VIGÍLIA — (em produção) o modelo atende pedidos de programação.
  🌙  SONHO   — o modelo inventa problemas, tenta resolver e VERIFICA executando.
  😴  SONO    — consolida (LoRA) as soluções verificadas. Acorda mais inteligente.

Honestidade embutida: só vira memória o que passa na execução real. O modelo não pode
"aprender" uma alucinação — a realidade (o interpretador Python) é o juiz.

Uso (modo bootstrap, sem GPU — testa a maquinaria com problemas-semente):
    python -m dream.loop --mode seed --dreams 20

Uso (modo completo, no Colab Pro com o modelo 1B):
    python -m dream.loop --mode model --dreams 50 --cycles 3 --consolidate
"""

from __future__ import annotations

import argparse
import random

from .dreamer import dream_from_seeds, dream_with_model
from .problems import Problem
from .verifier import verify_solution


def _solve_with_seed_oracle(problem: Problem) -> str:
    """
    'Oráculo' de bootstrap: resolve os problemas-semente sem precisar do modelo grande.
    Serve para testar todo o ciclo (sonho→verifica→memória) sem GPU.
    """
    name = problem.func_name
    library = {
        "soma": "def soma(a, b):\n    return a + b",
        "fatorial": "def fatorial(n):\n    r = 1\n    for i in range(2, n+1):\n        r *= i\n    return r",
        "fib": "def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a+b\n    return a",
        "primos_ate": ("def primos_ate(n):\n"
                       "    return [x for x in range(2, n) "
                       "if all(x % d for d in range(2, int(x**0.5)+1))]"),
        "eh_palindromo": ("def eh_palindromo(s):\n"
                          "    s = s.lower().replace(' ', '')\n    return s == s[::-1]"),
        "eh_anagrama": "def eh_anagrama(a, b):\n    return sorted(a) == sorted(b)",
    }
    return library.get(name, "")


def run_cycle(
    coder,
    n_dreams: int,
    difficulty: int = 2,
    rng: random.Random | None = None,
    use_model: bool = True,
) -> dict:
    """Roda UM ciclo de sonho: gera problemas, resolve, verifica, memoriza os bons."""
    from .consolidate import remember

    rng = rng or random.Random()

    # 1) SONHAR — inventar problemas
    if use_model and coder is not None:
        problems = dream_with_model(coder, n_dreams, difficulty)
    else:
        problems = dream_from_seeds(n_dreams, rng)

    stats = {"sonhados": len(problems), "verificados": 0, "falhos": 0}

    # 2) RESOLVER + 3) VERIFICAR
    for p in problems:
        instruction = p.to_instruction()

        if use_model and coder is not None:
            from src.coder import extract_code
            raw = coder.solve(instruction)
            solution = extract_code(raw)
        else:
            solution = _solve_with_seed_oracle(p)

        if not solution:
            stats["falhos"] += 1
            continue

        result = verify_solution(solution, p.tests)
        if result.passed:
            stats["verificados"] += 1
            remember(instruction, solution, result.score)  # só o verificado vira memória
        else:
            stats["falhos"] += 1

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Ciclo do Sonho do Dream-AI")
    parser.add_argument("--mode", choices=["seed", "model"], default="seed",
                        help="seed=bootstrap sem GPU; model=usa o modelo 1B (Colab Pro)")
    parser.add_argument("--dreams", type=int, default=20, help="problemas por ciclo")
    parser.add_argument("--cycles", type=int, default=1, help="quantos ciclos de sonho")
    parser.add_argument("--difficulty", type=int, default=2)
    parser.add_argument("--consolidate", action="store_true",
                        help="ao fim, consolidar (LoRA) — precisa de GPU")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    use_model = args.mode == "model"

    coder = None
    if use_model:
        from src.coder import CoderModel
        coder = CoderModel()
        coder.load()

    total = {"sonhados": 0, "verificados": 0, "falhos": 0}
    for c in range(1, args.cycles + 1):
        print(f"\n🌙 === Ciclo de sonho {c}/{args.cycles} ===")
        stats = run_cycle(coder, args.dreams, args.difficulty, rng, use_model)
        for k in total:
            total[k] += stats[k]
        taxa = stats["verificados"] / max(stats["sonhados"], 1) * 100
        print(f"   sonhados={stats['sonhados']} | "
              f"✅ verificados={stats['verificados']} | "
              f"❌ falhos={stats['falhos']} | taxa de acerto={taxa:.0f}%")

    print(f"\n🌅 Despertar. Total: {total['verificados']} memórias verificadas "
          f"de {total['sonhados']} sonhos.")

    if args.consolidate and coder is not None:
        from .consolidate import consolidate
        consolidate(coder)
    elif args.consolidate:
        print("⚠️  Consolidação (LoRA) precisa do modelo carregado (--mode model).")


if __name__ == "__main__":
    main()

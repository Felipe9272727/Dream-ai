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

from .dreamer import dream_from_seeds, dream_with_model, dream_at_difficulty
from .problems import Problem
from .verifier import verify_solution


def _solve_with_seed_oracle(problem: Problem) -> str:
    """
    'Oráculo' de bootstrap: usa a solução de referência do problema, sem precisar do
    modelo grande. Serve para testar todo o ciclo (sonho→verifica→memória) sem GPU.
    """
    return problem.reference_solution


def run_cycle(
    coder,
    n_dreams: int,
    difficulty: int = 2,
    rng: random.Random | None = None,
    use_model: bool = True,
    source: str = "curated",
    max_attempts: int = 3,
) -> dict:
    """Roda UM ciclo de sonho: gera problemas, resolve, verifica, memoriza os bons.

    source="curated" (PADRÃO): pratica em problemas com gabarito CONFIÁVEL (banco
        validado). O sinal de verificação é verdadeiro → aprendizado de qualidade.
    source="invented": a IA inventa os próprios problemas E testes. Criativo, mas
        pouco confiável em modelos pequenos (gabarito que ele inventa costuma ter erro).
    """
    from .consolidate import remember
    from .reflect import solve_with_reflection

    rng = rng or random.Random()

    # 1) SONHAR — gerar os problemas do ciclo
    if use_model and coder is not None and source == "invented":
        problems = dream_with_model(coder, n_dreams, difficulty)
    else:
        # problemas curados (testes confiáveis), variando os valores a cada sonho
        problems = dream_at_difficulty(n_dreams, difficulty, rng)

    stats = {"sonhados": len(problems), "verificados": 0, "falhos": 0, "corrigidos": 0}

    # 2) RESOLVER (com reflexão) + 3) VERIFICAR (contra gabarito confiável)
    for p in problems:
        if use_model and coder is not None:
            code, result, attempts = solve_with_reflection(coder, p, max_attempts=max_attempts)
            passed = bool(result and result.passed)
            if passed and attempts > 1:
                stats["corrigidos"] += 1  # acertou após refletir sobre o erro
        else:
            code = _solve_with_seed_oracle(p)
            result = verify_solution(code, p.tests) if code else None
            passed = bool(result and result.passed)

        if passed:
            stats["verificados"] += 1
            remember(p.to_instruction(), code, 1.0)  # só o verificado vira memória
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

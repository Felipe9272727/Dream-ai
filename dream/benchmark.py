"""
📊 Benchmark — mede a inteligência de programação da IA (antes vs. depois de sonhar).

Funciona como um mini-HumanEval: um conjunto de problemas HELD-OUT (que a IA NUNCA usou
para sonhar/treinar) é dado ao modelo, que precisa resolvê-los. Medimos o **pass@1**:
a fração de problemas resolvidos corretamente (verificados por execução).

Honestidade: os problemas de avaliação são SEPARADOS dos de treino. Medir no que treinou
seria trapaça. Aqui medimos generalização real.

Uso:
    # com um solver qualquer (callable instrução->código):
    from dream.benchmark import run_benchmark
    run_benchmark(meu_solver)

    # comparando antes/depois no Colab:
    python -m dream.benchmark   (modo demo, usa as soluções de referência)
"""

from __future__ import annotations

import dataclasses
from typing import Callable

from .problems import P, Problem
from .verifier import verify_solution


# ---------------------------------------------------------------------------
# Conjunto HELD-OUT — NÃO aparece em SEED_PROBLEMS. É a "prova" da IA.
# ---------------------------------------------------------------------------
HELDOUT_PROBLEMS: list[Problem] = [
    P("soma_lista", "Soma todos os números de uma lista.", "soma_lista",
      [("soma_lista([1, 2, 3])", "6"), ("soma_lista([])", "0")], 1, "listas",
      "def soma_lista(xs):\n    return sum(xs)"),
    P("media", "Média aritmética de uma lista não-vazia.", "media",
      [("media([2, 4])", "3.0"), ("media([5])", "5.0")], 2, "matematica",
      "def media(xs):\n    return sum(xs) / len(xs)"),
    P("eh_par", "True se o número é par.", "eh_par",
      [("eh_par(4)", "True"), ("eh_par(7)", "False")], 1, "matematica",
      "def eh_par(n):\n    return n % 2 == 0"),
    P("maiusculas", "Conta letras maiúsculas numa string.", "conta_maiusculas",
      [("conta_maiusculas('AbCdE')", "3"), ("conta_maiusculas('abc')", "0")], 2, "strings",
      "def conta_maiusculas(s):\n    return sum(c.isupper() for c in s)"),
    P("remove_duplicatas", "Remove duplicatas de uma lista preservando a ordem.",
      "sem_duplicatas",
      [("sem_duplicatas([1, 2, 2, 3, 1])", "[1, 2, 3]")], 3, "listas",
      "def sem_duplicatas(xs):\n    vis = set()\n    out = []\n    for x in xs:\n"
      "        if x not in vis:\n            vis.add(x); out.append(x)\n    return out"),
    P("soma_digitos", "Soma os dígitos de um inteiro positivo.", "soma_digitos",
      [("soma_digitos(123)", "6"), ("soma_digitos(0)", "0")], 2, "matematica",
      "def soma_digitos(n):\n    return sum(int(d) for d in str(n))"),
    P("conta_ocorrencias", "Quantas vezes x aparece numa lista.", "conta",
      [("conta([1, 2, 1, 3, 1], 1)", "3"), ("conta([], 5)", "0")], 2, "listas",
      "def conta(xs, x):\n    return xs.count(x)"),
    P("titulo", "Coloca a primeira letra de cada palavra em maiúscula.", "titulo",
      [("titulo('ola mundo')", "'Ola Mundo'")], 3, "strings",
      "def titulo(s):\n    return ' '.join(w.capitalize() for w in s.split())"),
    P("potencia", "Calcula base elevado a expoente (expoente>=0) sem usar **.", "potencia",
      [("potencia(2, 10)", "1024"), ("potencia(5, 0)", "1")], 3, "matematica",
      "def potencia(b, e):\n    r = 1\n    for _ in range(e):\n        r *= b\n    return r"),
    P("intersecao", "Elementos comuns a duas listas (ordenados, sem repetir).", "intersecao",
      [("intersecao([1, 2, 3], [2, 3, 4])", "[2, 3]")], 4, "listas",
      "def intersecao(a, b):\n    return sorted(set(a) & set(b))"),
]


@dataclasses.dataclass
class BenchmarkReport:
    total: int
    solved: int
    by_category: dict
    by_difficulty: dict
    failures: list[str]

    @property
    def pass_at_1(self) -> float:
        return self.solved / self.total if self.total else 0.0

    def pretty(self, label: str = "") -> str:
        head = f"📊 Benchmark{(' — ' + label) if label else ''}"
        lines = [
            head,
            f"   pass@1: {self.pass_at_1 * 100:.1f}%  ({self.solved}/{self.total})",
            "   por dificuldade: " + ", ".join(
                f"nv{d}={v['solved']}/{v['total']}" for d, v in sorted(self.by_difficulty.items())
            ),
            "   por categoria: " + ", ".join(
                f"{c}={v['solved']}/{v['total']}" for c, v in sorted(self.by_category.items())
            ),
        ]
        if self.failures:
            lines.append(f"   falhou em: {', '.join(self.failures)}")
        return "\n".join(lines)


def run_benchmark(
    solver: Callable[[str], str],
    problems: list[Problem] | None = None,
) -> BenchmarkReport:
    """
    Roda o benchmark. `solver` recebe a instrução (texto) e devolve o código da solução.

    Para avaliar o modelo real:  solver = lambda instr: extract_code(coder.solve(instr))
    """
    problems = problems or HELDOUT_PROBLEMS
    solved = 0
    by_cat: dict = {}
    by_diff: dict = {}
    failures: list[str] = []

    for p in problems:
        by_cat.setdefault(p.category, {"solved": 0, "total": 0})
        by_diff.setdefault(p.difficulty, {"solved": 0, "total": 0})
        by_cat[p.category]["total"] += 1
        by_diff[p.difficulty]["total"] += 1

        try:
            code = solver(p.to_instruction())
        except Exception:
            code = ""

        result = verify_solution(code, p.tests) if code else None
        if result and result.passed:
            solved += 1
            by_cat[p.category]["solved"] += 1
            by_diff[p.difficulty]["solved"] += 1
        else:
            failures.append(p.title)

    return BenchmarkReport(len(problems), solved, by_cat, by_diff, failures)


def validate_benchmark() -> bool:
    """Sanidade: as soluções de referência DEVEM passar 100%. Valida o próprio benchmark."""
    report = run_benchmark(lambda instr: _reference_for(instr))
    return report.pass_at_1 == 1.0


def _reference_for(instruction: str) -> str:
    for p in HELDOUT_PROBLEMS:
        if p.to_instruction() == instruction:
            return p.reference_solution
    return ""


def main() -> None:
    # Modo demo: usa as soluções de referência (deve dar 100% — valida o benchmark)
    report = run_benchmark(_reference_for)
    print(report.pretty("soluções de referência (validação)"))
    print("\n✅ Benchmark válido." if report.pass_at_1 == 1.0
          else "\n❌ Benchmark inconsistente!")


if __name__ == "__main__":
    main()

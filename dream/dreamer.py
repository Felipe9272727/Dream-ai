"""
🌙 O Sonhador — inventa novos problemas de programação.

Durante o sonho, a IA não fica parada: ela imagina novos desafios. Há dois modos:

1. MODO SEMENTE (não precisa de GPU): combina e varia os problemas-semente para
   criar um currículo. Útil para bootstrap e para testar a maquinaria.

2. MODO MODELO (precisa do CoderModel): pede ao próprio modelo para INVENTAR novos
   problemas com casos de teste — sonhos genuínos, criativos. Como a DeepMind faz
   com geração de dados sintéticos.

Cada problema sonhado passa pelo verificador antes de virar memória.
"""

from __future__ import annotations

import random

from .problems import Problem, SEED_PROBLEMS
from .verifier import TestCase


def dream_from_seeds(n: int, rng: random.Random | None = None) -> list[Problem]:
    """Gera n problemas variando as sementes (modo sem GPU, para bootstrap/teste)."""
    rng = rng or random.Random()
    out: list[Problem] = []
    for _ in range(n):
        base = rng.choice(SEED_PROBLEMS)
        # "Variação onírica": reembala o problema com novos valores de teste quando dá.
        out.append(_mutate(base, rng))
    return out


def dream_at_difficulty(n: int, difficulty: int,
                        rng: random.Random | None = None) -> list[Problem]:
    """Gera n problemas de uma dificuldade-alvo (cai para a mais próxima se faltar)."""
    rng = rng or random.Random()
    pool = [p for p in SEED_PROBLEMS if p.difficulty == difficulty]
    if not pool:
        # nível sem sementes: pega o mais próximo
        pool = sorted(SEED_PROBLEMS, key=lambda p: abs(p.difficulty - difficulty))[:3]
    return [_mutate(rng.choice(pool), rng) for _ in range(n)]


def _mutate(p: Problem, rng: random.Random) -> Problem:
    """Cria uma variação de um problema-semente com testes recalculados de verdade.

    A solução de referência é preservada (mesma função), então o bootstrap continua
    conseguindo resolver a variação.
    """
    def variant(title, tests):
        return Problem(title=title, prompt=p.prompt, func_name=p.func_name,
                       tests=tests, difficulty=p.difficulty, category=p.category,
                       reference_solution=p.reference_solution)

    if p.func_name == "soma":
        a, b = rng.randint(-50, 50), rng.randint(-50, 50)
        return variant(f"soma_{a}_{b}", [TestCase(f"soma({a}, {b})", str(a + b))])
    if p.func_name == "fatorial":
        import math
        n = rng.randint(1, 8)
        return variant(f"fatorial_{n}", [TestCase(f"fatorial({n})", str(math.factorial(n)))])
    if p.func_name == "fib":
        n = rng.randint(2, 15)
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return variant(f"fib_{n}", [TestCase(f"fib({n})", str(a))])
    if p.func_name == "primos_ate":
        n = rng.choice([10, 20, 30, 50])
        primos = [x for x in range(2, n) if all(x % d for d in range(2, int(x**0.5) + 1))]
        return variant(f"primos_{n}", [TestCase(f"primos_ate({n})", repr(primos))])
    if p.func_name == "reverso":
        import string
        s = "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(1, 8)))
        return variant(f"reverso_{s}", [TestCase(f"reverso({s!r})", repr(s[::-1]))])
    if p.func_name == "maior":
        xs = [rng.randint(-99, 99) for _ in range(rng.randint(2, 6))]
        return variant(f"maior_{len(xs)}", [TestCase(f"maior({xs!r})", str(max(xs)))])
    if p.func_name == "mdc":
        import math
        a, b = rng.randint(1, 100), rng.randint(1, 100)
        return variant(f"mdc_{a}_{b}", [TestCase(f"mdc({a}, {b})", str(math.gcd(a, b)))])
    # fallback: devolve a própria semente
    return p


DREAM_GENERATION_PROMPT = """\
Invente um problema de programação Python original e interessante, de dificuldade {dificuldade}/5.
Responda EXATAMENTE neste formato:

FUNCAO: <nome_da_funcao>
ENUNCIADO: <descrição clara do que a função faz>
TESTES:
<chamada_1> == <resultado_esperado_1>
<chamada_2> == <resultado_esperado_2>
<chamada_3> == <resultado_esperado_3>

Os testes devem ser determinísticos e corretos."""


def dream_with_model(coder, n: int, difficulty: int = 2) -> list[Problem]:
    """Pede ao modelo para inventar n problemas novos (modo criativo, precisa de GPU)."""
    problems: list[Problem] = []
    for _ in range(n):
        raw = coder.solve(
            DREAM_GENERATION_PROMPT.format(dificuldade=difficulty),
            max_new_tokens=400, temperature=0.9,
        )
        p = _parse_dreamed_problem(raw, difficulty)
        if p is not None:
            problems.append(p)
    return problems


def _parse_dreamed_problem(raw: str, difficulty: int) -> Problem | None:
    """Faz o parsing do problema sonhado no formato esperado. Robusto a ruído."""
    func_name = None
    prompt = None
    tests: list[TestCase] = []

    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("FUNCAO:"):
            func_name = line.split(":", 1)[1].strip().split("(")[0].strip()
        elif line.upper().startswith("ENUNCIADO:"):
            prompt = line.split(":", 1)[1].strip()
        elif "==" in line and func_name and func_name in line:
            call, _, expected = line.partition("==")
            tests.append(TestCase(call.strip(), expected.strip()))

    if func_name and prompt and tests:
        return Problem(
            title=f"sonho_{func_name}", prompt=prompt, func_name=func_name,
            tests=tests, difficulty=difficulty,
        )
    return None

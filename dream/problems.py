"""
🌱 Banco de problemas de programação.

Esses são os desafios com os quais a IA "sonha" e nos quais é avaliada. Cobrem várias
categorias e dificuldades, formando um CURRÍCULO crescente.

Cada problema tem:
- enunciado em linguagem natural (vai para o modelo)
- nome da função esperada
- casos de teste verificáveis (executados de verdade)
- uma solução de REFERÊNCIA (usada para bootstrap sem GPU e para validar os testes)
"""

from __future__ import annotations

import dataclasses

from .verifier import TestCase


@dataclasses.dataclass
class Problem:
    title: str
    prompt: str
    func_name: str
    tests: list[TestCase]
    difficulty: int = 1          # 1=fácil ... 5=difícil
    category: str = "geral"
    reference_solution: str = "" # solução conhecida-boa (bootstrap + validação dos testes)

    def to_instruction(self) -> str:
        return (
            f"Escreva uma função Python chamada `{self.func_name}` que resolve:\n"
            f"{self.prompt}\n"
            f"Responda apenas com o código da função."
        )


def P(title, prompt, func_name, tests, difficulty, category, ref) -> Problem:
    return Problem(title, prompt, func_name,
                   [TestCase(c, e) for c, e in tests],
                   difficulty, category, ref)


# ---------------------------------------------------------------------------
# CURRÍCULO — problemas de treino/sonho (a IA aprende com estes)
# ---------------------------------------------------------------------------
SEED_PROBLEMS: list[Problem] = [
    # --- Básico (nível 1) ---
    P("soma", "Recebe dois números e retorna a soma.", "soma",
      [("soma(2, 3)", "5"), ("soma(-4, 4)", "0")], 1, "matematica",
      "def soma(a, b):\n    return a + b"),
    P("maior", "Recebe uma lista de números e retorna o maior.", "maior",
      [("maior([1, 9, 3])", "9"), ("maior([-5, -2])", "-2")], 1, "listas",
      "def maior(xs):\n    return max(xs)"),
    P("reverso", "Recebe uma string e retorna ela invertida.", "reverso",
      [("reverso('abc')", "'cba'"), ("reverso('')", "''")], 1, "strings",
      "def reverso(s):\n    return s[::-1]"),

    # --- Intermediário (nível 2-3) ---
    P("fatorial", "Recebe um inteiro n>=0 e retorna n! (fatorial).", "fatorial",
      [("fatorial(0)", "1"), ("fatorial(5)", "120")], 2, "matematica",
      "def fatorial(n):\n    r = 1\n    for i in range(2, n+1):\n        r *= i\n    return r"),
    P("palindromo", "True se a string é palíndromo, ignorando maiúsculas e espaços.",
      "eh_palindromo",
      [("eh_palindromo('arara')", "True"), ("eh_palindromo('Ame a ema')", "True"),
       ("eh_palindromo('python')", "False")], 2, "strings",
      "def eh_palindromo(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]"),
    P("contar_vogais", "Conta quantas vogais (aeiou) há numa string.", "contar_vogais",
      [("contar_vogais('banana')", "3"), ("contar_vogais('xyz')", "0")], 2, "strings",
      "def contar_vogais(s):\n    return sum(c in 'aeiou' for c in s.lower())"),
    P("fibonacci", "n-ésimo número de Fibonacci (fib(0)=0, fib(1)=1).", "fib",
      [("fib(0)", "0"), ("fib(1)", "1"), ("fib(10)", "55")], 3, "matematica",
      "def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a+b\n    return a"),
    P("primos", "Lista de primos menores que n.", "primos_ate",
      [("primos_ate(10)", "[2, 3, 5, 7]"), ("primos_ate(2)", "[]")], 3, "matematica",
      "def primos_ate(n):\n    return [x for x in range(2, n) "
      "if all(x % d for d in range(2, int(x**0.5)+1))]"),
    P("anagrama", "True se duas strings são anagramas.", "eh_anagrama",
      [("eh_anagrama('amor', 'roma')", "True"), ("eh_anagrama('casa', 'caso')", "False")],
      3, "strings", "def eh_anagrama(a, b):\n    return sorted(a) == sorted(b)"),
    P("bubble_sort", "Ordena uma lista de números em ordem crescente.", "ordena",
      [("ordena([3, 1, 2])", "[1, 2, 3]"), ("ordena([])", "[]")], 3, "algoritmos",
      "def ordena(xs):\n    return sorted(xs)"),

    # --- Avançado (nível 4-5) ---
    P("mdc", "Máximo divisor comum de dois inteiros.", "mdc",
      [("mdc(12, 18)", "6"), ("mdc(7, 1)", "1")], 4, "matematica",
      "def mdc(a, b):\n    while b:\n        a, b = b, a % b\n    return a"),
    P("busca_binaria", "Índice de x numa lista ordenada, ou -1 se ausente.", "busca",
      [("busca([1, 3, 5, 7], 5)", "2"), ("busca([1, 2, 3], 9)", "-1")], 4, "algoritmos",
      "def busca(xs, x):\n    lo, hi = 0, len(xs)-1\n    while lo <= hi:\n"
      "        m = (lo+hi)//2\n        if xs[m] == x: return m\n"
      "        if xs[m] < x: lo = m+1\n        else: hi = m-1\n    return -1"),
    P("contar_palavras", "Dicionário com a contagem de cada palavra numa frase.",
      "contar_palavras",
      [("contar_palavras('a b a')", "{'a': 2, 'b': 1}")], 4, "strings",
      "def contar_palavras(s):\n    d = {}\n    for w in s.split():\n"
      "        d[w] = d.get(w, 0) + 1\n    return d"),
    P("achatar", "Achata uma lista de listas em uma lista única.", "achatar",
      [("achatar([[1, 2], [3], []])", "[1, 2, 3]")], 4, "listas",
      "def achatar(xss):\n    return [x for xs in xss for x in xs]"),
    P("coeficiente_binomial", "Combinação C(n, k).", "combinacao",
      [("combinacao(5, 2)", "10"), ("combinacao(6, 0)", "1")], 5, "matematica",
      "def combinacao(n, k):\n    from math import comb\n    return comb(n, k)"),
]


def problems_by_category() -> dict[str, list[Problem]]:
    out: dict[str, list[Problem]] = {}
    for p in SEED_PROBLEMS:
        out.setdefault(p.category, []).append(p)
    return out

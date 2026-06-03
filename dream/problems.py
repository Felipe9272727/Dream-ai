"""
🌱 Banco de problemas-semente.

Esses são os problemas iniciais com os quais a IA "sonha". O sonhador usa essas
sementes para inventar variações cada vez mais difíceis (currículo crescente).

Cada problema tem: enunciado, nome da função e casos de teste verificáveis.
"""

from __future__ import annotations

import dataclasses

from .verifier import TestCase


@dataclasses.dataclass
class Problem:
    title: str
    prompt: str                 # enunciado em linguagem natural (vai para o modelo)
    func_name: str              # nome esperado da função
    tests: list[TestCase]
    difficulty: int = 1         # 1=fácil ... 5=difícil

    def to_instruction(self) -> str:
        """Formata o problema como instrução para o modelo coder."""
        return (
            f"Escreva uma função Python chamada `{self.func_name}` que resolve:\n"
            f"{self.prompt}\n"
            f"Responda apenas com o código da função."
        )


SEED_PROBLEMS: list[Problem] = [
    Problem(
        title="soma",
        prompt="Recebe dois números e retorna a soma deles.",
        func_name="soma",
        tests=[TestCase("soma(2, 3)", "5"), TestCase("soma(-4, 4)", "0")],
        difficulty=1,
    ),
    Problem(
        title="fatorial",
        prompt="Recebe um inteiro n >= 0 e retorna n! (fatorial).",
        func_name="fatorial",
        tests=[TestCase("fatorial(0)", "1"), TestCase("fatorial(5)", "120")],
        difficulty=2,
    ),
    Problem(
        title="palindromo",
        prompt="Recebe uma string e retorna True se ela é um palíndromo, ignorando "
               "maiúsculas/minúsculas e espaços.",
        func_name="eh_palindromo",
        tests=[
            TestCase("eh_palindromo('arara')", "True"),
            TestCase("eh_palindromo('Ame a ema')", "True"),
            TestCase("eh_palindromo('python')", "False"),
        ],
        difficulty=2,
    ),
    Problem(
        title="fibonacci",
        prompt="Recebe um inteiro n >= 0 e retorna o n-ésimo número de Fibonacci "
               "(fib(0)=0, fib(1)=1).",
        func_name="fib",
        tests=[TestCase("fib(0)", "0"), TestCase("fib(1)", "1"), TestCase("fib(10)", "55")],
        difficulty=3,
    ),
    Problem(
        title="primos",
        prompt="Recebe um inteiro n e retorna a lista de números primos menores que n.",
        func_name="primos_ate",
        tests=[
            TestCase("primos_ate(10)", "[2, 3, 5, 7]"),
            TestCase("primos_ate(2)", "[]"),
        ],
        difficulty=3,
    ),
    Problem(
        title="anagrama",
        prompt="Recebe duas strings e retorna True se uma é anagrama da outra.",
        func_name="eh_anagrama",
        tests=[
            TestCase("eh_anagrama('amor', 'roma')", "True"),
            TestCase("eh_anagrama('casa', 'caso')", "False"),
        ],
        difficulty=3,
    ),
]

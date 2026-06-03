"""
🔁 Reflect-Retry — aprender com os próprios erros.

Baseado em "Reflect, Retry, Reward" e "Exploring Expert Failures" (2025): quando uma
solução falha, em vez de jogá-la fora, mostramos o ERRO ao modelo e pedimos que ele
reflita e corrija. Muitas vezes ele acerta na segunda tentativa — e essa correção é um
dado de treino valioso.

Honestidade preservada: a versão corrigida AINDA precisa passar no verificador para
virar memória. Refletir não relaxa a verificação.
"""

from __future__ import annotations

from .problems import Problem
from .verifier import verify_solution, VerificationResult


def solve_with_reflection(coder, problem: Problem, max_attempts: int = 3):
    """
    Tenta resolver um problema, refletindo sobre os erros entre as tentativas.

    Retorna (codigo, resultado_verificacao, n_tentativas). O código só é "bom" se
    resultado.passed for True.
    """
    from src.coder import extract_code

    instruction = problem.to_instruction()
    last_error = ""
    code = ""
    result: VerificationResult | None = None

    for attempt in range(1, max_attempts + 1):
        if attempt == 1:
            prompt = instruction
        else:
            # Reflexão: mostra o erro e pede correção
            prompt = (
                f"{instruction}\n\n"
                f"Sua tentativa anterior foi:\n```python\n{code}\n```\n"
                f"Mas ela FALHOU na verificação com este erro:\n{last_error}\n\n"
                f"Reflita sobre o que deu errado e escreva uma versão CORRIGIDA da função. "
                f"Responda apenas com o código."
            )

        raw = coder.solve(prompt)
        code = extract_code(raw)
        if not code:
            last_error = "nenhum código foi gerado"
            continue

        result = verify_solution(code, problem.tests)
        if result.passed:
            return code, result, attempt
        last_error = result.error or "saída incorreta"

    return code, result, max_attempts

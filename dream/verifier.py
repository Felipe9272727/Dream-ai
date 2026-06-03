"""
🔬 Verificador — a "checagem de realidade" dos sonhos.

Executa código Python gerado pelo modelo em um subprocesso isolado, com limite de
tempo, e confere se ele passa nos casos de teste. Esta é a peça MAIS importante para
a honestidade: uma solução só é aceita se REALMENTE funcionar quando executada.

Sonho que não passa no teste é descartado. Nada de "parece certo" — ou roda, ou não conta.

⚠️  Segurança: execução de código arbitrário é perigosa. Aqui usamos subprocesso +
timeout, o que é adequado para uma sandbox descartável (Colab). Para produção, use um
sandbox real (Docker sem rede, nsjail, gVisor, etc.).
"""

from __future__ import annotations

import dataclasses
import subprocess
import sys
import tempfile
import textwrap
import os


@dataclasses.dataclass
class TestCase:
    """Um caso de teste: dada uma chamada, qual a saída esperada."""
    __test__ = False     # evita que o pytest tente coletar isto como teste

    call: str            # ex: "soma(2, 3)"
    expected: str        # ex: "5"  (comparado via repr/igualdade)


@dataclasses.dataclass
class VerificationResult:
    passed: bool
    num_passed: int
    num_total: int
    error: str = ""

    @property
    def score(self) -> float:
        return self.num_passed / self.num_total if self.num_total else 0.0


def _build_harness(solution_code: str, tests: list[TestCase]) -> str:
    """Monta um script que roda a solução contra os testes e reporta o resultado."""
    checks = []
    for i, t in enumerate(tests):
        checks.append(
            textwrap.dedent(f"""\
            try:
                __got = {t.call}
                __exp = {t.expected}
                if __got == __exp:
                    __passed += 1
                else:
                    __fails.append(f"teste {i}: {t.call} -> {{__got!r}}, esperado {{__exp!r}}")
            except Exception as __e:
                __fails.append(f"teste {i}: {t.call} levantou {{type(__e).__name__}}: {{__e}}")
            """)
        )
    checks_code = "\n".join(checks)

    return (
        solution_code
        + "\n\n"
        + "__passed = 0\n__fails = []\n"
        + checks_code
        + "\nimport json,sys\n"
        + "print('__RESULT__' + json.dumps({'passed': __passed, "
          "'total': " + str(len(tests)) + ", 'fails': __fails}))\n"
    )


def verify_solution(
    solution_code: str,
    tests: list[TestCase],
    timeout: float = 5.0,
) -> VerificationResult:
    """Executa a solução contra os testes em subprocesso isolado."""
    if not tests:
        return VerificationResult(False, 0, 0, "sem casos de teste")

    script = _build_harness(solution_code, tests)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(script)
        path = f.name

    try:
        proc = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=timeout,
            # Ambiente mínimo: sem variáveis sensíveis herdadas
            env={"PATH": os.environ.get("PATH", "")},
        )
    except subprocess.TimeoutExpired:
        os.unlink(path)
        return VerificationResult(False, 0, len(tests), f"timeout (>{timeout}s) — possível loop infinito")
    finally:
        if os.path.exists(path):
            os.unlink(path)

    if proc.returncode != 0:
        err = (proc.stderr or "").strip().splitlines()
        msg = err[-1] if err else "erro de execução"
        return VerificationResult(False, 0, len(tests), f"crash: {msg}")

    # Procura a linha de resultado
    import json
    for line in proc.stdout.splitlines():
        if line.startswith("__RESULT__"):
            data = json.loads(line[len("__RESULT__"):])
            passed = data["passed"]
            total = data["total"]
            err = "; ".join(data["fails"]) if data["fails"] else ""
            return VerificationResult(passed == total, passed, total, err)

    return VerificationResult(False, 0, len(tests), "sem resultado (saída inesperada)")

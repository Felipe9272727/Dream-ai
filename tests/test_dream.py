"""
Testes do sistema de sonho. Foco na GARANTIA DE HONESTIDADE:
soluções erradas/alucinadas NÃO podem virar memória.

Rode: python -m pytest tests/ -v   (ou simplesmente python tests/test_dream.py)
"""

from __future__ import annotations

from dream.verifier import verify_solution, TestCase
from dream.dreamer import dream_from_seeds, _parse_dreamed_problem
from dream.problems import SEED_PROBLEMS


def test_verificador_aceita_solucao_correta():
    code = "def soma(a, b):\n    return a + b"
    r = verify_solution(code, [TestCase("soma(2, 3)", "5")])
    assert r.passed and r.score == 1.0


def test_verificador_rejeita_solucao_errada():
    code = "def soma(a, b):\n    return a - b"  # errado de propósito
    r = verify_solution(code, [TestCase("soma(2, 3)", "5")])
    assert not r.passed, "ALUCINAÇÃO não pode passar na verificação!"


def test_verificador_pega_loop_infinito():
    code = "def f():\n    while True: pass"
    r = verify_solution(code, [TestCase("f()", "1")], timeout=1)
    assert not r.passed and "timeout" in r.error.lower()


def test_verificador_pega_crash():
    code = "def f():\n    return 1/0"
    r = verify_solution(code, [TestCase("f()", "1")])
    assert not r.passed


def test_sonhador_gera_problemas_validos():
    problems = dream_from_seeds(10)
    assert len(problems) == 10
    for p in problems:
        assert p.func_name and p.tests


def test_problemas_semente_tem_testes_corretos():
    # Cada semente deve ter casos de teste bem formados
    for p in SEED_PROBLEMS:
        assert p.tests, f"{p.title} sem testes"
        for t in p.tests:
            assert t.call and t.expected


def test_parse_problema_sonhado():
    raw = (
        "FUNCAO: dobro\n"
        "ENUNCIADO: retorna o dobro de um número\n"
        "TESTES:\n"
        "dobro(2) == 4\n"
        "dobro(5) == 10\n"
    )
    p = _parse_dreamed_problem(raw, difficulty=1)
    assert p is not None
    assert p.func_name == "dobro"
    assert len(p.tests) == 2


def test_garantia_honestidade_end_to_end():
    """A prova central: uma solução alucinada nunca é marcada como aprovada."""
    alucinacao = "def fib(n):\n    return 42  # chute aleatório"
    fib_problem = next(p for p in SEED_PROBLEMS if p.func_name == "fib")
    r = verify_solution(alucinacao, fib_problem.tests)
    assert not r.passed, "Um chute não pode ser aceito como solução!"


def test_solucoes_de_referencia_passam():
    """Toda solução de referência das sementes DEVE passar nos próprios testes."""
    for p in SEED_PROBLEMS:
        r = verify_solution(p.reference_solution, p.tests)
        assert r.passed, f"Referência de '{p.title}' não passa nos testes!"


def test_benchmark_se_auto_valida():
    """O benchmark com soluções de referência deve dar 100% (held-out bem formado)."""
    from dream.benchmark import validate_benchmark
    assert validate_benchmark(), "Benchmark inconsistente: refs deveriam dar 100%"


def test_benchmark_held_out_eh_disjunto_do_treino():
    """HONESTIDADE: nenhum problema de avaliação pode estar no conjunto de treino."""
    from dream.benchmark import HELDOUT_PROBLEMS
    treino = {p.func_name for p in SEED_PROBLEMS}
    prova = {p.func_name for p in HELDOUT_PROBLEMS}
    assert treino.isdisjoint(prova), (
        f"Vazamento treino↔prova: {treino & prova}. Medir no que treinou é trapaça!"
    )


def test_vida_persiste_entre_sessoes(tmp_path, monkeypatch):
    """A identidade deve sobreviver entre 'sessões' (salvar e recarregar)."""
    import dream.lifecycle as lc
    monkeypatch.setattr(lc, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(lc, "IDENTITY_PATH", str(tmp_path / "identity.json"))
    monkeypatch.setattr(lc, "JOURNAL_PATH", str(tmp_path / "journal.jsonl"))

    vida1 = lc.Life()
    vida1.wake()
    vida1.sleep(dreamed=10, verified=8, new_skills=["soma", "fib"])

    vida2 = lc.Life()  # "nova sessão"
    msg = vida2.wake()
    assert vida2.identity.total_verified == 8
    assert "soma" in vida2.identity.skills
    assert vida2.identity.total_sessions == 2  # lembrou da sessão anterior


if __name__ == "__main__":
    import sys

    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print(f"✅ {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"❌ {fn.__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} testes passaram.")
    sys.exit(1 if failed else 0)

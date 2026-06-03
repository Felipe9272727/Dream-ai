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
    monkeypatch.setenv("DREAM_HOME", str(tmp_path))  # isola o armazenamento no tmp

    vida1 = lc.Life()
    vida1.wake()
    vida1.sleep(dreamed=10, verified=8, new_skills=["soma", "fib"])

    vida2 = lc.Life()  # "nova sessão"
    vida2.wake()
    assert vida2.identity.total_verified == 8
    assert "soma" in vida2.identity.skills
    assert vida2.identity.total_sessions == 2  # lembrou da sessão anterior


def test_curriculo_sobe_quando_domina():
    """Currículo adaptativo: ao dominar um nível, a fronteira sobe (autocurrículo)."""
    from dream.adaptive import CurriculumState, update_frontier
    cur = CurriculumState(frontier=1)
    for _ in range(15):
        cur.record(1, True)   # acertou tudo no nível 1
    update_frontier(cur)
    assert cur.frontier == 2, "Dominou o nível 1, deveria subir para o 2"


def test_curriculo_desce_quando_dificil():
    """Se um nível está difícil demais, a fronteira recua."""
    from dream.adaptive import CurriculumState, update_frontier
    cur = CurriculumState(frontier=3)
    for _ in range(15):
        cur.record(3, False)  # falhou tudo no nível 3
    update_frontier(cur)
    assert cur.frontier == 2, "Nível 3 difícil demais, deveria recuar para o 2"


def test_continuidade_atravessa_reinicios(tmp_path, monkeypatch):
    """A IA nunca 'desliga': batidas de vida persistem e crescem entre reinícios."""
    import dream.lifecycle as lc
    monkeypatch.setenv("DREAM_HOME", str(tmp_path))

    vida1 = lc.Life()
    vida1.wake()
    vida1.heartbeat(); vida1.heartbeat()
    assert vida1.identity.heartbeats == 2

    vida2 = lc.Life()  # "reinício" do processo
    vida2.heartbeat()
    assert vida2.identity.heartbeats == 3, "As batidas devem continuar, não zerar"


def test_reflect_retry_aceita_so_o_verificado(tmp_path, monkeypatch):
    """Reflect-Retry: mesmo com reflexão, só conta o que passa no verificador."""
    from dream.reflect import solve_with_reflection
    from dream.problems import SEED_PROBLEMS

    p = next(pr for pr in SEED_PROBLEMS if pr.func_name == "soma")

    class MockCoder:
        def solve(self, prompt, **kw):
            return "```python\ndef soma(a, b):\n    return a + b\n```"

    code, result, attempts = solve_with_reflection(MockCoder(), p, max_attempts=3)
    assert result.passed and attempts == 1


def test_autoconsciencia_reflete_estado(tmp_path, monkeypatch):
    """A descrição de si mesma deve refletir o estado interno real."""
    import dream.lifecycle as lc
    monkeypatch.setenv("DREAM_HOME", str(tmp_path))

    vida = lc.Life()
    vida.wake()
    vida.sleep(dreamed=10, verified=7, new_skills=["soma", "fib"])

    desc = vida.self_description()
    assert "soma" in desc and "fib" in desc       # sabe o que domina
    assert "não sei" in desc.lower()               # ciente dos próprios limites
    assert "10" in desc and "7" in desc            # reflete os números reais


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

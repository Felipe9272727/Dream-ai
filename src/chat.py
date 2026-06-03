"""
💬 Chat — converse com a Dream-AI.

A IA acorda lembrando quem é (vida persistente entre sessões), atende seus pedidos de
programação, e pode "dormir" para sonhar e aprender. Tudo no terminal.

Comandos especiais:
    /dormir [n]   — dorme: sonha n problemas, verifica, consolida e acorda mais esperta
    /status       — mostra quem ela é e o que já aprendeu
    /benchmark    — mede a inteligência atual (pass@1 em problemas held-out)
    /sair         — encerra (a identidade fica salva para a próxima sessão)

Uso:
    python -m src.chat                 # usa o modelo 1B (precisa de GPU/Colab Pro)
    python -m src.chat --mock          # modo demo sem GPU (oráculo de referência)
"""

from __future__ import annotations

import argparse

from dream.lifecycle import Life
from dream.benchmark import run_benchmark


class MockCoder:
    """Coder falso para testar o chat sem GPU: resolve via problemas conhecidos."""

    def solve(self, instruction: str, **kw) -> str:
        from dream.problems import SEED_PROBLEMS
        from dream.benchmark import HELDOUT_PROBLEMS
        for p in SEED_PROBLEMS + HELDOUT_PROBLEMS:
            if p.func_name in instruction or p.prompt[:20] in instruction:
                return "```python\n" + p.reference_solution + "\n```"
        return ("Não tenho certeza de como resolver isso ainda — e prefiro ser honesta "
                "a inventar código que pode não funcionar. Tente /dormir para eu aprender.")


def _make_solver(coder):
    from src.coder import extract_code
    return lambda instr: extract_code(coder.solve(instr))


def do_sleep(coder, life: Life, n_dreams: int, use_model: bool) -> None:
    """Executa um ciclo de sono: sonha, verifica, consolida, atualiza a identidade."""
    import random
    from dream.loop import run_cycle

    print(f"\n🌙 {life.identity.name} está dormindo e sonhando ({n_dreams} sonhos)...")
    stats = run_cycle(coder, n_dreams, difficulty=2, rng=random.Random(), use_model=use_model)

    # Descobre que habilidades novas foram dominadas neste sono
    from dream.consolidate import load_memory
    skills = sorted({
        ex["instruction"].split("`")[1]
        for ex in load_memory() if "`" in ex["instruction"]
    })

    adapter = None
    if use_model and coder is not None:
        from dream.consolidate import consolidate
        adapter = consolidate(coder)

    msg = life.sleep(stats["sonhados"], stats["verificados"], skills, adapter)
    print(msg)


def chat(use_model: bool, mock: bool) -> None:
    life = Life()
    print(life.wake())

    coder = None
    if mock or not use_model:
        coder = MockCoder()
        use_model = False
    else:
        from src.coder import CoderModel
        coder = CoderModel(adapter_path=life.identity.adapter_path)
        coder.load()

    print("\n(Digite seu pedido de programação, ou /status, /dormir, /benchmark, /sair)\n")

    while True:
        try:
            user = input("você ➤ ").strip()
        except (EOFError, KeyboardInterrupt):
            user = "/sair"

        if not user:
            continue

        if user == "/sair":
            print(f"\n💾 {life.identity.name}: até a próxima! Vou guardar quem eu sou.")
            break
        elif user == "/status":
            print(life.summary())
        elif user == "/benchmark":
            print("📊 Medindo inteligência atual (held-out)...")
            report = run_benchmark(_make_solver(coder) if use_model else
                                   (lambda instr: _mock_solve(coder, instr)))
            print(report.pretty("agora"))
        elif user.startswith("/dormir"):
            parts = user.split()
            n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 20
            do_sleep(coder, life, n, use_model)
        else:
            resposta = coder.solve(user)
            print(f"\n{life.identity.name} ➤\n{resposta}\n")


def _mock_solve(coder, instr: str) -> str:
    from src.coder import extract_code
    return extract_code(coder.solve(instr))


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat com a Dream-AI")
    parser.add_argument("--mock", action="store_true",
                        help="modo demo sem GPU (não carrega o modelo 1B)")
    args = parser.parse_args()
    chat(use_model=not args.mock, mock=args.mock)


if __name__ == "__main__":
    main()

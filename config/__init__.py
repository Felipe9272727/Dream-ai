"""Configurações de tamanho do Dream-AI.

Cada config é um dicionário com os hiperparâmetros do modelo e do treino.
Trocar de config muda o tamanho da IA sem mexer em nenhuma outra linha de código.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# nano — minúsculo, treina em minutos. Ótimo para testar se tudo funciona.
# ---------------------------------------------------------------------------
nano = dict(
    name="nano",
    # modelo
    vocab_size=4096,
    block_size=128,
    n_layer=4,
    n_head=4,
    n_embd=128,
    dropout=0.0,
    bias=False,
    # treino
    batch_size=32,
    learning_rate=1e-3,
    max_iters=2000,
    warmup_iters=100,
    min_lr=1e-4,
    weight_decay=0.1,
    grad_clip=1.0,
    eval_interval=200,
    eval_iters=50,
)

# ---------------------------------------------------------------------------
# small — ~30M params. Treina em horas no Colab grátis. O trilho de aprendizado.
# ---------------------------------------------------------------------------
small = dict(
    name="small",
    vocab_size=8192,
    block_size=256,
    n_layer=6,
    n_head=6,
    n_embd=384,
    dropout=0.1,
    bias=False,
    batch_size=32,
    learning_rate=6e-4,
    max_iters=20000,
    warmup_iters=500,
    min_lr=6e-5,
    weight_decay=0.1,
    grad_clip=1.0,
    eval_interval=500,
    eval_iters=100,
)

# ---------------------------------------------------------------------------
# medium — ~120M params. Precisa de Colab Pro (mais VRAM).
# ---------------------------------------------------------------------------
medium = dict(
    name="medium",
    vocab_size=16384,
    block_size=512,
    n_layer=12,
    n_head=12,
    n_embd=768,
    dropout=0.1,
    bias=False,
    batch_size=16,
    learning_rate=3e-4,
    max_iters=60000,
    warmup_iters=1000,
    min_lr=3e-5,
    weight_decay=0.1,
    grad_clip=1.0,
    eval_interval=1000,
    eval_iters=200,
)

# ---------------------------------------------------------------------------
# dream_1b — ~1B params. O SONHO. Honestamente: precisa de um cluster de GPUs,
# NÃO treina no Colab. Está aqui para mostrar como a arquitetura escala.
# ---------------------------------------------------------------------------
dream_1b = dict(
    name="dream_1b",
    vocab_size=32000,
    block_size=2048,
    n_layer=24,
    n_head=16,
    n_embd=2048,
    dropout=0.0,
    bias=False,
    batch_size=8,            # com gradient accumulation para batch efetivo grande
    learning_rate=2e-4,
    max_iters=600000,
    warmup_iters=2000,
    min_lr=2e-5,
    weight_decay=0.1,
    grad_clip=1.0,
    eval_interval=2000,
    eval_iters=200,
)


CONFIGS = {c["name"]: c for c in [nano, small, medium, dream_1b]}


def get_config(name: str) -> dict:
    if name not in CONFIGS:
        raise ValueError(
            f"Config '{name}' não existe. Opções: {', '.join(CONFIGS)}"
        )
    # devolve uma cópia para evitar mutação acidental
    return dict(CONFIGS[name])

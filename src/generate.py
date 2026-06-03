"""
Geração de texto com o Dream-AI treinado.

Carrega o checkpoint e faz o modelo "falar" a partir de um prompt.

Uso:
    python -m src.generate --config small --prompt "O sentido da vida é"
"""

from __future__ import annotations

import argparse
import os

import torch

from src.model import GPT, GPTConfig
from src.tokenizer import DreamTokenizer

CKPT_DIR = "checkpoints"


def load_model(config_name: str, device: str):
    ckpt_path = os.path.join(CKPT_DIR, f"{config_name}.pt")
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(
            f"Checkpoint não encontrado em {ckpt_path}. "
            f"Treine primeiro: python -m src.train --config {config_name}"
        )
    ckpt = torch.load(ckpt_path, map_location=device)
    model_cfg = GPTConfig(**ckpt["model_cfg"])
    model = GPT(model_cfg).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model


def generate(
    config_name: str,
    prompt: str,
    max_new_tokens: int = 200,
    temperature: float = 0.8,
    top_k: int = 40,
) -> str:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = DreamTokenizer(config_name)
    model = load_model(config_name, device)

    ids = tok.encode(prompt)
    x = torch.tensor(ids, dtype=torch.long, device=device)[None, ...]

    y = model.generate(x, max_new_tokens=max_new_tokens, temperature=temperature, top_k=top_k)
    return tok.decode(y[0].tolist())


def main() -> None:
    parser = argparse.ArgumentParser(description="Geração de texto do Dream-AI")
    parser.add_argument("--config", default="small")
    parser.add_argument("--prompt", default="A inteligência artificial é")
    parser.add_argument("--max_new_tokens", type=int, default=200)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top_k", type=int, default=40)
    args = parser.parse_args()

    text = generate(
        args.config,
        args.prompt,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
    )
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


if __name__ == "__main__":
    main()

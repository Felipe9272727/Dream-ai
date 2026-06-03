"""
Loop de treino do Dream-AI.

É aqui que a mágica acontece: mostramos milhões de exemplos de texto ao modelo,
ele tenta prever a próxima palavra, erra, e ajusta os pesos para errar menos.
Repita um milhão de vezes e ele aprende a falar.

Uso:
    python -m src.train --config small
"""

from __future__ import annotations

import argparse
import math
import os
import time

import torch

from config import get_config
from src.data import get_batch
from src.model import GPT, GPTConfig
from src import storage


def get_lr(it: int, cfg: dict) -> float:
    """Learning rate com warmup + decaimento cosseno (padrão moderno e estável)."""
    if it < cfg["warmup_iters"]:
        return cfg["learning_rate"] * (it + 1) / (cfg["warmup_iters"] + 1)
    if it > cfg["max_iters"]:
        return cfg["min_lr"]
    decay_ratio = (it - cfg["warmup_iters"]) / (cfg["max_iters"] - cfg["warmup_iters"])
    coeff = 0.5 * (1.0 + math.cos(math.pi * decay_ratio))
    return cfg["min_lr"] + coeff * (cfg["learning_rate"] - cfg["min_lr"])


@torch.no_grad()
def estimate_loss(model, cfg, device) -> dict:
    """Mede a perda em treino e validação (modelo em modo eval)."""
    out = {}
    model.eval()
    for split in ["train", "val"]:
        losses = torch.zeros(cfg["eval_iters"])
        for k in range(cfg["eval_iters"]):
            X, Y = get_batch(split, cfg["block_size"], cfg["batch_size"], device)
            _, loss = model(X, Y)
            losses[k] = loss.item()
        out[split] = losses.mean().item()
    model.train()
    return out


def train(config_name: str, resume: bool = False) -> None:
    cfg = get_config(config_name)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    device_type = "cuda" if device.startswith("cuda") else "cpu"
    print(f"🖥️  Dispositivo: {device}")

    # Confere se os dados existem
    if not os.path.exists(os.path.join("data", "train.bin")):
        raise FileNotFoundError(
            "Dados não encontrados. Rode:\n"
            f"  python -m src.data --config {config_name}\n"
            f"  python -m src.tokenizer --train --config {config_name}\n"
            f"  python -m src.data --config {config_name} --tokenize"
        )

    # Constrói o modelo
    model_cfg = GPTConfig(
        vocab_size=cfg["vocab_size"],
        block_size=cfg["block_size"],
        n_layer=cfg["n_layer"],
        n_head=cfg["n_head"],
        n_embd=cfg["n_embd"],
        dropout=cfg["dropout"],
        bias=cfg["bias"],
    )
    model = GPT(model_cfg).to(device)
    print(f"🧠 Modelo '{config_name}': {model.num_params() / 1e6:.2f}M parâmetros")

    optimizer = model.configure_optimizers(
        weight_decay=cfg["weight_decay"],
        learning_rate=cfg["learning_rate"],
        betas=(0.9, 0.95),
        device_type=device_type,
    )

    # Mixed precision para acelerar na GPU
    use_amp = device_type == "cuda"
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    # Checkpoints salvos SEMPRE no Drive (quando disponível) para não se perder
    ckpt_path = storage.resolve("checkpoints", f"{config_name}.pt")
    print(f"💾 {storage.status()}")

    start_iter = 0
    best_val = float("inf")
    if resume and os.path.exists(ckpt_path):
        print(f"♻️  Retomando de {ckpt_path}")
        ckpt = torch.load(ckpt_path, map_location=device)
        model.load_state_dict(ckpt["model"])
        optimizer.load_state_dict(ckpt["optimizer"])
        start_iter = ckpt["iter"] + 1
        best_val = ckpt.get("best_val", best_val)

    model.train()
    t0 = time.time()

    for it in range(start_iter, cfg["max_iters"] + 1):
        # Ajusta o learning rate deste passo
        lr = get_lr(it, cfg)
        for group in optimizer.param_groups:
            group["lr"] = lr

        # Avaliação periódica + checkpoint
        if it % cfg["eval_interval"] == 0:
            losses = estimate_loss(model, cfg, device)
            dt = time.time() - t0
            print(
                f"iter {it:>6} | train {losses['train']:.4f} | "
                f"val {losses['val']:.4f} | lr {lr:.2e} | {dt:.1f}s"
            )
            if losses["val"] < best_val:
                best_val = losses["val"]
                torch.save(
                    {
                        "model": model.state_dict(),
                        "optimizer": optimizer.state_dict(),
                        "model_cfg": model_cfg.__dict__,
                        "iter": it,
                        "best_val": best_val,
                        "config_name": config_name,
                    },
                    ckpt_path,
                )
                print(f"   💾 Melhor modelo salvo (val={best_val:.4f}) em {ckpt_path}")

        # Um passo de treino
        X, Y = get_batch("train", cfg["block_size"], cfg["batch_size"], device)
        with torch.autocast(device_type=device_type, dtype=torch.bfloat16, enabled=use_amp):
            _, loss = model(X, Y)

        optimizer.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        if cfg["grad_clip"] > 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), cfg["grad_clip"])
        scaler.step(optimizer)
        scaler.update()

    print(f"🏁 Treino concluído. Melhor val loss: {best_val:.4f}")
    print(f"   Gere texto com: python -m src.generate --config {config_name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Treino do Dream-AI")
    parser.add_argument("--config", default="small")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    train(args.config, resume=args.resume)


if __name__ == "__main__":
    main()

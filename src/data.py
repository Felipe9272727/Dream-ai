"""
Preparação de dados para o Dream-AI.

Faz duas coisas:
1. Monta um corpus de texto (data/corpus.txt) — por padrão usa um corpus de exemplo
   em português; você pode trocar por qualquer texto seu.
2. Depois que o tokenizer estiver treinado, converte o corpus em tokens binários
   (train.bin / val.bin) que o loop de treino lê rapidíssimo.

Uso:
    python -m src.data --config small                # monta o corpus
    python -m src.data --config small --tokenize     # gera train.bin / val.bin
"""

from __future__ import annotations

import argparse
import os

import numpy as np

DATA_DIR = "data"


SAMPLE_CORPUS = """\
A inteligência artificial é a ciência de fazer máquinas pensarem.
Uma IA honesta admite quando não sabe a resposta.
Aprender de verdade é melhor do que fingir que sabe.
O cérebro humano tem bilhões de neurônios conectados.
Um modelo de linguagem prevê a próxima palavra de uma frase.
A honestidade é a base da confiança entre humanos e máquinas.
Quando não tenho certeza, é melhor dizer "não sei" do que inventar.
O conhecimento cresce quando reconhecemos o que ainda não entendemos.
Sonhar grande é o primeiro passo para construir algo novo.
Cada token que o modelo aprende é um pedacinho de linguagem.
A matemática por trás de uma rede neural é mais simples do que parece.
Transformers usam atenção para decidir o que é importante em uma frase.
Treinar uma IA é mostrar a ela milhões de exemplos de texto.
A curiosidade move tanto cientistas quanto máquinas que aprendem.
Errar faz parte do aprendizado, desde que a gente reconheça o erro.
"""


def build_corpus(config_name: str) -> str:
    """Cria data/corpus.txt. Se você já tem seu próprio texto, coloque-o aqui."""
    os.makedirs(DATA_DIR, exist_ok=True)
    corpus_path = os.path.join(DATA_DIR, "corpus.txt")

    if os.path.exists(corpus_path) and os.path.getsize(corpus_path) > 0:
        print(f"📚 Corpus já existe em {corpus_path} "
              f"({os.path.getsize(corpus_path)} bytes). Mantendo.")
        return corpus_path

    # Repete o corpus de exemplo para dar volume mínimo de treino.
    # >>> SUBSTITUA isto pelo seu próprio texto para resultados de verdade! <<<
    text = (SAMPLE_CORPUS + "\n") * 200
    with open(corpus_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"📚 Corpus de EXEMPLO criado em {corpus_path} ({len(text)} chars).")
    print("⚠️  Honestidade: esse é um corpus minúsculo só para demonstração.")
    print("    Para uma IA de verdade, troque por gigabytes de texto real.")
    return corpus_path


def tokenize_corpus(config_name: str, val_frac: float = 0.1) -> None:
    """Converte o corpus em tokens e salva train.bin / val.bin."""
    from src.tokenizer import DreamTokenizer

    corpus_path = os.path.join(DATA_DIR, "corpus.txt")
    if not os.path.exists(corpus_path):
        raise FileNotFoundError("Rode 'python -m src.data --config <cfg>' primeiro.")

    tok = DreamTokenizer(config_name)
    with open(corpus_path, "r", encoding="utf-8") as f:
        text = f.read()

    print("🔢 Tokenizando o corpus ...")
    ids = tok.encode(text)
    ids = np.array(ids, dtype=np.uint16)

    n = len(ids)
    split = int(n * (1 - val_frac))
    train_ids, val_ids = ids[:split], ids[split:]

    train_ids.tofile(os.path.join(DATA_DIR, "train.bin"))
    val_ids.tofile(os.path.join(DATA_DIR, "val.bin"))

    print(f"✅ {len(train_ids)} tokens de treino, {len(val_ids)} de validação.")
    print(f"   Salvos em {DATA_DIR}/train.bin e {DATA_DIR}/val.bin")


def get_batch(split: str, block_size: int, batch_size: int, device: str):
    """Lê um lote aleatório de sequências do disco (memmap, eficiente em memória)."""
    filename = os.path.join(DATA_DIR, f"{split}.bin")
    data = np.memmap(filename, dtype=np.uint16, mode="r")

    import torch

    ix = np.random.randint(0, len(data) - block_size, size=(batch_size,))
    x = torch.stack([torch.from_numpy(data[i:i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack([torch.from_numpy(data[i + 1:i + 1 + block_size].astype(np.int64)) for i in ix])

    if device.startswith("cuda"):
        x, y = x.pin_memory().to(device, non_blocking=True), y.pin_memory().to(device, non_blocking=True)
    else:
        x, y = x.to(device), y.to(device)
    return x, y


def main() -> None:
    parser = argparse.ArgumentParser(description="Preparação de dados do Dream-AI")
    parser.add_argument("--config", default="small")
    parser.add_argument("--tokenize", action="store_true",
                        help="gerar train.bin/val.bin (precisa do tokenizer treinado)")
    args = parser.parse_args()

    if args.tokenize:
        tokenize_corpus(args.config)
    else:
        build_corpus(args.config)


if __name__ == "__main__":
    main()

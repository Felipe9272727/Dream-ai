"""
Tokenizer BPE (Byte-Pair Encoding) para o Dream-AI.

O tokenizer transforma texto em números (tokens) que o modelo entende, e vice-versa.
Usamos a biblioteca `tokenizers` da Hugging Face para treinar um BPE — é o mesmo
algoritmo usado pelo GPT, mas treinado no NOSSO corpus.

Uso:
    python -m src.tokenizer --train --config small
"""

from __future__ import annotations

import argparse
import os

DATA_DIR = "data"
TOKENIZER_DIR = "tokenizers_trained"

# Tokens especiais que o modelo precisa conhecer
SPECIAL_TOKENS = [
    "<|endoftext|>",   # marca fim de documento
    "<|unk|>",         # token desconhecido
    "<|user|>",        # início de fala do usuário (para chat/instrução)
    "<|assistant|>",   # início de fala da IA
    "<|honest|>",      # marca uma resposta honesta/com incerteza (ver docs/HONESTIDADE.md)
]


def tokenizer_path(config_name: str) -> str:
    return os.path.join(TOKENIZER_DIR, f"{config_name}.json")


def train_tokenizer(config_name: str, vocab_size: int, corpus_path: str) -> str:
    """Treina um tokenizer BPE no corpus e salva em disco."""
    from tokenizers import Tokenizer
    from tokenizers.models import BPE
    from tokenizers.trainers import BpeTrainer
    from tokenizers.pre_tokenizers import ByteLevel
    from tokenizers.decoders import ByteLevel as ByteLevelDecoder

    if not os.path.exists(corpus_path):
        raise FileNotFoundError(
            f"Corpus não encontrado em '{corpus_path}'. "
            f"Rode primeiro: python -m src.data --config {config_name}"
        )

    os.makedirs(TOKENIZER_DIR, exist_ok=True)

    tokenizer = Tokenizer(BPE(unk_token="<|unk|>"))
    tokenizer.pre_tokenizer = ByteLevel(add_prefix_space=False)
    # O decoder reverte o byte-level encoding para produzir texto limpo
    tokenizer.decoder = ByteLevelDecoder()

    trainer = BpeTrainer(
        vocab_size=vocab_size,
        special_tokens=SPECIAL_TOKENS,
        show_progress=True,
    )

    print(f"🔤 Treinando tokenizer BPE (vocab={vocab_size}) em {corpus_path} ...")
    tokenizer.train([corpus_path], trainer)

    out = tokenizer_path(config_name)
    tokenizer.save(out)
    print(f"✅ Tokenizer salvo em {out} (vocab real: {tokenizer.get_vocab_size()})")
    return out


class DreamTokenizer:
    """Wrapper simples para codificar/decodificar texto."""

    def __init__(self, config_name: str):
        from tokenizers import Tokenizer

        path = tokenizer_path(config_name)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Tokenizer não encontrado em '{path}'. "
                f"Treine com: python -m src.tokenizer --train --config {config_name}"
            )
        self.tok = Tokenizer.from_file(path)
        self.eot_id = self.tok.token_to_id("<|endoftext|>")

    @property
    def vocab_size(self) -> int:
        return self.tok.get_vocab_size()

    def encode(self, text: str) -> list[int]:
        return self.tok.encode(text).ids

    def decode(self, ids: list[int]) -> str:
        return self.tok.decode(ids)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tokenizer BPE do Dream-AI")
    parser.add_argument("--train", action="store_true", help="treinar o tokenizer")
    parser.add_argument("--config", default="small", help="nome da config")
    args = parser.parse_args()

    from config import get_config

    cfg = get_config(args.config)
    corpus_path = os.path.join(DATA_DIR, "corpus.txt")

    if args.train:
        train_tokenizer(args.config, cfg["vocab_size"], corpus_path)
    else:
        tok = DreamTokenizer(args.config)
        demo = "Olá! Eu sou uma IA honesta."
        ids = tok.encode(demo)
        print(f"Texto:   {demo}")
        print(f"Tokens:  {ids}")
        print(f"Decode:  {tok.decode(ids)}")


if __name__ == "__main__":
    main()

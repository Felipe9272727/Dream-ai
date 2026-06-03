# 🌙 Dream-AI

Uma IA construída **do zero** — arquitetura Transformer (estilo GPT) escrita na mão em
PyTorch, com foco em duas coisas: **entender como uma IA funciona de verdade** e
**construir um modelo o mais honesto possível**.

> Honestidade em primeiro lugar: este README te conta a verdade sobre o que é e o que
> não é viável. Sem hype.

---

## 🎯 Objetivo

Criar uma IA capaz de demonstrar inteligência real e, acima de tudo, ser **honesta** —
ou seja, admitir quando não sabe, sinalizar incerteza e evitar inventar fatos
(o famoso "alucinar").

## ⚠️ A verdade sobre "1 bilhão de parâmetros do zero"

Treinar um modelo de **1B de parâmetros do absoluto zero** exige, na prática:

- **~20 bilhões de tokens** de dados de treino (lei de Chinchilla: ~20 tokens por parâmetro).
- **Milhares de horas** de GPU A100/H100.
- Dezenas de milhares de dólares em compute.

Isso **não é viável** no Google Colab grátis (T4/L4 com horas limitadas). Isso é fato.

Por isso o projeto tem **dois trilhos**, e o mesmo código serve para os dois:

### Trilho 1 — Aprendizado (do zero de verdade)
Treine um modelo **pequeno** (10M–50M parâmetros) do zero no Colab. Ele aprende a gerar
texto em português e te ensina, peça por peça, como uma IA funciona. Config:
[`config/small.py`](config/small.py).

### Trilho 2 — O Sonho 1B (caminho realista)
Para ter um modelo de 1B inteligente **de verdade**, o caminho viável é **fine-tuning**
(LoRA/QLoRA) de um modelo base aberto de ~1B (Llama-3.2-1B, Qwen2.5-1.5B, etc.) com foco
em honestidade. A config [`config/dream_1b.py`](config/dream_1b.py) define a arquitetura
de 1B caso um dia você tenha o compute para treinar do zero.

---

## 🏗️ Como funciona (arquitetura)

Tudo escrito na mão, sem "caixas pretas":

| Componente | Arquivo | O que é |
|---|---|---|
| Tokenizer (BPE) | `src/tokenizer.py` | Quebra texto em tokens |
| Atenção multi-cabeça | `src/model.py` | O coração do Transformer |
| Bloco Transformer | `src/model.py` | Atenção + MLP + normalização |
| Modelo GPT | `src/model.py` | Empilha os blocos |
| Loop de treino | `src/train.py` | Ensina o modelo |
| Geração de texto | `src/generate.py` | Faz o modelo "falar" |

## 🚀 Começando

```bash
pip install -r requirements.txt

# 1. Prepara os dados (baixa/processa um corpus de texto)
python -m src.data --config small

# 2. Treina o tokenizer
python -m src.tokenizer --train --config small

# 3. Treina o modelo
python -m src.train --config small

# 4. Conversa com a sua IA
python -m src.generate --config small --prompt "O sentido da vida é"
```

No Colab, abra [`notebooks/dream_ai_colab.ipynb`](notebooks/dream_ai_colab.ipynb).

## 🧭 Princípio de honestidade

A honestidade de uma IA não vem do tamanho — vem dos **dados** e do **treino**. Veja
[`docs/HONESTIDADE.md`](docs/HONESTIDADE.md) para a estratégia concreta de como tornar
este modelo honesto.

## 📊 Configurações de tamanho

| Config | Parâmetros | Camadas | Dim | Cabeças | Viável no Colab? |
|---|---|---|---|---|---|
| `nano` | ~1M | 4 | 128 | 4 | ✅ minutos |
| `small` | ~30M | 6 | 384 | 6 | ✅ horas |
| `medium` | ~120M | 12 | 768 | 12 | ⚠️ Colab Pro |
| `dream_1b` | ~1B | 24 | 2048 | 16 | ❌ precisa de cluster |

---

Feito com 🌙 e honestidade.

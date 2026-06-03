# 🌙 Dream-AI

Uma IA de **programação** que **sonha** para ficar mais inteligente — e que é honesta
por construção.

> Honestidade em primeiro lugar: este README te conta a verdade sobre o que é viável.
> Sem hype.

---

## 🎯 A visão

Pegar um modelo base aberto de **~1B parâmetros especializado em código**
(Qwen2.5-Coder) e torná-lo **hiper-inteligente em programação** através de um ciclo de
**auto-aprimoramento inspirado no sono humano e na DeepMind**:

A IA **sonha** — inventa desafios de programação, tenta resolver, e **verifica
executando o código de verdade**. Só o que realmente funciona vira aprendizado.
Depois ela **dorme** (consolida via LoRA) e acorda melhor.

```
   ☀️ VIGÍLIA              🌙 SONHO                    😴 SONO
  (atende você)    →    (inventa + resolve +    →   (consolida via LoRA
                         VERIFICA executando)        as soluções corretas)
        ↑                                                    │
        └────────────────── acorda mais inteligente ─────────┘
```

📖 Detalhes em [`docs/SONHO.md`](docs/SONHO.md).

## 🔒 Honestidade por construção

A regra inviolável do sonho:

> **Só vira memória o que passa na execução real.**

O interpretador Python é o juiz. Uma solução alucinada que "parece certa" mas não passa
nos testes é **descartada** — nunca aprendida. Isso está **provado** em
[`tests/test_dream.py`](tests/test_dream.py). A memória do que ela aprendeu é um arquivo
JSONL **auditável**: você vê exatamente o que cada sonho ensinou.

📖 Estratégia completa de honestidade em [`docs/HONESTIDADE.md`](docs/HONESTIDADE.md).

## ⚠️ A verdade sobre "1B do zero"

Treinar 1B do **absoluto zero** precisa de ~20B tokens e milhares de horas de GPU —
**inviável no Colab**. Por isso a visão usa **fine-tuning** de um modelo 1B já forte.

Mas o repo **também** inclui um GPT completo escrito **do zero** (estilo nanoGPT), para
você entender como uma IA funciona peça por peça. Treine um modelo pequeno no Colab e
veja-o aprender.

---

## 📂 Estrutura

```
Dream-ai/
├── src/
│   ├── model.py        # GPT decoder-only escrito do zero (atenção, blocos, etc.)
│   ├── tokenizer.py    # tokenizer BPE
│   ├── data.py         # preparação de dados
│   ├── train.py        # loop de treino do zero
│   ├── generate.py     # geração de texto
│   ├── coder.py        # carrega o modelo Coder de 1B (Qwen2.5-Coder)
│   └── honesty.py      # prompt de sistema + métricas de honestidade
├── dream/
│   ├── verifier.py     # 🔬 executa o código e checa — a "checagem de realidade"
│   ├── problems.py     # 🌱 banco de problemas-semente
│   ├── dreamer.py      # 🌙 inventa novos problemas
│   ├── consolidate.py  # 😴 consolida (LoRA) o que foi sonhado e verificado
│   └── loop.py         # 🔁 orquestra vigília → sonho → sono
├── config/             # tamanhos: nano, small, medium, dream_1b
├── tests/              # testes (inclui a prova de honestidade)
├── notebooks/          # 🚀 dream_ai_colab.ipynb — ponto de entrada no Colab Pro
└── docs/               # SONHO.md, HONESTIDADE.md
```

## 🚀 Começando

### No Colab Pro (a visão completa)
Abra [`notebooks/dream_ai_colab.ipynb`](notebooks/dream_ai_colab.ipynb) e rode as células.

### Localmente (testar a maquinaria, sem GPU)
```bash
pip install torch numpy tokenizers

# Testa o ciclo do sonho com problemas-semente (sem precisar do modelo grande)
python -m dream.loop --mode seed --dreams 25 --cycles 2

# Roda os testes (inclui a garantia de honestidade)
python tests/test_dream.py
```

### Treinar uma IA do zero (trilho de aprendizado)
```bash
python -m src.data --config small
python -m src.tokenizer --train --config small
python -m src.data --config small --tokenize
python -m src.train --config small
python -m src.generate --config small --prompt "def fibonacci(n):"
```

## 📊 Configurações de tamanho (modelo do zero)

| Config | Parâmetros | Camadas | Dim | Viável no Colab? |
|---|---|---|---|---|
| `nano` | ~1M | 4 | 128 | ✅ minutos |
| `small` | ~30M | 6 | 384 | ✅ horas |
| `medium` | ~120M | 12 | 768 | ⚠️ Colab Pro |
| `dream_1b` | ~1B | 24 | 2048 | ❌ precisa de cluster |

---

Feito com 🌙 e honestidade.

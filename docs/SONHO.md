# 🌙 O Sonho — como o Dream-AI se auto-aprimora

> A ideia central: uma IA que **sonha** enquanto está ociosa. Ela inventa desafios de
> programação, tenta resolvê-los, e **só aprende com os que realmente funcionam**.

Isso é inspirado em:
- **Sono humano:** o cérebro consolida memórias durante o sono.
- **DeepMind:** self-play do AlphaZero, self-training do AlphaCode.
- **STaR (Self-Taught Reasoner):** o modelo gera suas próprias soluções, filtra as
  corretas e treina nelas.

## O ciclo

```
   ☀️ VIGÍLIA              🌙 SONHO                    😴 SONO
  (atende você)    →    (inventa + resolve +    →   (consolida via LoRA
                         VERIFICA executando)        as soluções corretas)
        ↑                                                    │
        └────────────────── acorda mais inteligente ─────────┘
```

### 1. ☀️ Vigília
O modelo (Qwen2.5-Coder-1.5B + adapters aprendidos) atende seus pedidos de programação.

### 2. 🌙 Sonho
Ocioso, o modelo:
- **Inventa** problemas de programação novos (com casos de teste).
- **Tenta resolver** cada um.
- **Verifica** executando o código de verdade contra os testes (`dream/verifier.py`).

### 3. 😴 Sono (consolidação)
As soluções que **passaram na verificação** são gravadas em
`dream_memory/verified.jsonl` (auditável!) e usadas para um fine-tuning LoRA leve
(`dream/consolidate.py`). O modelo acorda tendo internalizado o que aprendeu sonhando.

## 🔒 Por que isso é honesto (e não vira "lixo aprende lixo")

O perigo do auto-treino é o modelo aprender com os próprios erros e degradar. Evitamos
isso com **uma regra inviolável**:

> **Só vira memória o que passa na execução real.**

O interpretador Python é o juiz imparcial. Uma solução alucinada que "parece certa" mas
não passa nos testes é **descartada**, nunca aprendida. Isso está provado nos testes
(`tests/test_dream.py` → `test_garantia_honestidade_end_to_end`).

A memória é um arquivo JSONL legível — você pode **auditar exatamente** o que a IA
aprendeu em cada sonho. Transparência total.

## A verdade honesta sobre os limites

1. **A IA não fica infinitamente mais inteligente.** O sonho a torna melhor nos tipos
   de problema que ela já quase resolve — empurra a fronteira, não cria milagres.
2. **A diversidade dos sonhos importa.** Se ela só sonhar com somas, só vai melhorar em
   somas. Por isso o sonhador busca dificuldade e variedade crescentes.
3. **Verificação cobre o que dá pra testar.** Funções com entrada/saída clara são
   ótimas; código com efeitos colaterais (rede, arquivos) é mais difícil de verificar.

## Como rodar

```bash
# Bootstrap sem GPU (testa a maquinaria com problemas-semente):
python -m dream.loop --mode seed --dreams 25 --cycles 2

# Completo no Colab Pro (com o modelo 1B sonhando de verdade):
python -m dream.loop --mode model --dreams 50 --cycles 3 --consolidate
```

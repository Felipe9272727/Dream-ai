# 🤝 A estratégia de honestidade do Dream-AI

> "Quando não tenho certeza, é melhor dizer 'não sei' do que inventar."

Este é o objetivo mais importante e mais difícil do projeto: fazer uma IA **honesta**.
Aqui está a verdade sobre como isso funciona — e os limites reais.

## Por que IAs mentem (alucinam)?

Um modelo de linguagem é treinado para **prever a próxima palavra mais provável**.
Ele não tem um conceito interno de "verdade" — ele tem um conceito de "o que soa
plausível". Por isso, quando não sabe, ele tende a **inventar algo que soa convincente**
em vez de admitir ignorância. Isso se chama *alucinação*.

Honestidade não é uma função que se liga. É um **comportamento** que precisa ser
ensinado e medido.

## As 4 alavancas concretas

### 1. Dados que modelam a honestidade
A IA imita os dados. Se o corpus de treino contém muitos exemplos de:
- "Não tenho informação suficiente para responder isso."
- "Não tenho certeza, mas acho que..."
- "Isso eu não sei."

...então o modelo aprende que admitir ignorância é um comportamento normal e esperado.

Por isso o token especial `<|honest|>` existe no tokenizer: marcamos respostas que
expressam incerteza calibrada, para o modelo aprender o padrão.

### 2. Fine-tuning de instrução com calibração
No trilho 2 (modelo 1B), o fine-tuning usa pares pergunta→resposta onde:
- Perguntas com resposta conhecida → resposta correta e direta.
- Perguntas impossíveis/ambíguas → "não sei" ou pedido de esclarecimento.
- **Nunca** recompensamos um chute confiante que está errado.

### 3. Calibração de confiança
Uma IA honesta sabe **o quanto** sabe. Tecnicamente, isso significa que a
probabilidade que o modelo atribui a uma resposta deve bater com a frequência real
de acerto. Medimos isso com *Expected Calibration Error (ECE)*.

### 4. Recusa em vez de invenção
O prompt de sistema (ver `src/honesty.py`) instrui explicitamente o modelo a
preferir "não sei" a inventar. Isso não é perfeito, mas reduz alucinação.

## ⚠️ A parte honesta sobre honestidade

Vou ser honesto com você sobre os limites:

1. **Nenhuma IA atual é 100% honesta.** Até os maiores modelos alucinam. Reduzir
   alucinação é possível; eliminá-la, ainda não.
2. **Um modelo pequeno treinado num corpus pequeno vai alucinar MUITO.** O trilho 1
   é para aprender a arquitetura, não para ter respostas confiáveis.
3. **Honestidade real exige dados de qualidade**, e isso é trabalho humano cuidadoso —
   não tem atalho mágico.

## Como medir se está funcionando

- Faça perguntas cuja resposta é desconhecida/impossível e veja se ele admite.
- Compare a confiança declarada com a taxa de acerto real.
- Registre os casos em que ele inventou — e adicione contra-exemplos ao corpus.

A honestidade é construída exemplo por exemplo. É um caminho, não um botão.

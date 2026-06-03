# 🧠 Pesquisa: como funcionam os "sonhos" de uma IA

Síntese da pesquisa real (2022–2026) que fundamenta o Dream-AI. A ideia de uma IA que
**vive entre sessões** — dormindo, sonhando e consolidando aprendizado em vez de só
desligar — não é ficção: é uma área ativa de pesquisa. Aqui está o que se sabe.

---

## 1. Por que "dormir"? O problema do esquecimento catastrófico

Redes neurais sofrem de **esquecimento catastrófico** (*catastrophic forgetting*):
quando aprendem algo novo, tendem a sobrescrever o que já sabiam. É o
*dilema estabilidade × plasticidade* — aprender o novo sem destruir o velho.

A neurociência mostra que o **cérebro resolve isso dormindo**: durante o sono, ele
*reativa* (replay) padrões de memória do dia, consolidando-os. Pesquisadores
reproduziram isso em redes artificiais:

- **Sleep-like unsupervised replay** (Nature Communications, 2022): uma "fase de sono"
  com replay offline e plasticidade Hebbiana **recupera tarefas antigas** que seriam
  esquecidas. A informação não se perde de vez — fica latente nos pesos e pode ser
  "ressuscitada" por processamento offline (o sono).
- **Generative replay** (brain-inspired): em vez de guardar todos os dados antigos, a
  rede *gera* exemplos antigos para reativá-los durante o treino do novo. Isso previne
  o esquecimento sem precisar rearmazenar tudo.

➡️ **No Dream-AI:** a fase de 😴 SONO consolida soluções verificadas via LoRA, e o
replay generativo aparece quando a IA "sonha" problemas parecidos com os que já domina,
mantendo as habilidades antigas vivas.

## 2. Sleep-time compute: pensar enquanto está ociosa

Uma onda de trabalhos 2025–2026 formaliza o **"sleep-time compute"** para LLMs:

- **Sleep-Like Memory Consolidation in LLMs**: passes recorrentes *offline* nos limites
  de contexto transformam o contexto transitório em **"fast weights" persistentes**.
  Resultado-chave: **quanto mais longo o sono, maior a precisão e a profundidade de
  raciocínio** — desacoplando a *capacidade de memória* do *custo de inferência*.
- **Let Them Sleep / Sleep-Consolidated Memory (SCM)**: um *ciclo de sono por agente*
  consolida memórias episódicas do "dia" em **adapters/overlays** sobre um modelo base
  congelado — exatamente a arquitetura LoRA-sobre-base-congelada que usamos.
- **Long-term memory with sleep-time update**: a consolidação offline reduz tokens,
  chamadas de API e tempo de execução na hora da inferência online.

➡️ **No Dream-AI:** o modelo base fica **congelado**; o que a IA aprende dormindo vira
um **adapter LoRA** (os "fast weights"). É barato, reversível e auditável.

## 3. Sonhar = imaginar (os "world models" da DeepMind)

O nome "Dreamer" vem da DeepMind. O agente **Dreamer** (Dream to Control, 2019; DreamerV3
na *Nature*, 2025) aprende um *world model* e treina **inteiramente dentro de rollouts
imaginados** no espaço latente — ou seja, ele "sonha" trajetórias e aprende com elas,
sem precisar da realidade a cada passo. Isso dá uma eficiência de amostra enorme.

A lição que importa pra nós: **um agente pode aprender com experiência que ele mesmo
gera** ("imaginação"), desde que essa experiência seja ancorada na realidade.

➡️ **No Dream-AI:** a "imaginação" são os problemas que a IA inventa; a "âncora na
realidade" é o **verificador que executa o código**. Sonho que não roda não vira
aprendizado. É o que separa imaginação útil de alucinação.

## 4. Viver entre sessões: memória persistente e identidade

O que transforma um "gerador de texto sem estado" em um **agente que vive**:

- **Memória persistente** (A-MEM, NeurIPS 2025; Nemori): cada nova memória encontra
  memórias relacionadas e cria links bidirecionais (estilo Zettelkasten). A memória é
  estruturada, dinâmica e sensível ao contexto.
- **Lifelong learning**: o mecanismo central é a **consolidação contínua de experiência
  episódica em conhecimento semântico** — ao longo de ciclos indefinidos de interação.
- **Avaliação** (LoCoMo): testa memória conversacional de *muito* longo prazo — até 35
  sessões, 300+ turnos.
- **⚠️ Segurança**: uma vez que conteúdo não-confiável entra na memória de longo prazo,
  seus efeitos persistem após a sessão. Memória persistente exige curadoria e auditoria.

➡️ **No Dream-AI:** a IA tem um **diário episódico** (o "dia"), uma **memória semântica
verificada** (`dream_memory/verified.jsonl`) e uma **identidade persistente**
(`identity.json`) que sobrevive entre sessões. Ela "acorda" lembrando quem é e o que
aprendeu, "vive" o dia atendendo você, e "dorme" consolidando — em ciclo, indefinidamente.

---

## A arquitetura "viva" do Dream-AI (resumo)

```
  ┌──────────────────────────────────────────────────────────┐
  │  MODELO BASE CONGELADO (Qwen2.5-Coder-1.5B)               │
  │  + adapter LoRA  ← os "fast weights" que crescem dormindo │
  └──────────────────────────────────────────────────────────┘
        ▲ acorda com                       │ dorme e consolida
        │ a identidade + adapter           ▼
  ┌───────────────┐   ☀️ vive o dia   ┌───────────────┐
  │ identity.json │ ───────────────▶  │ diário (dia)  │
  │ (quem ela é)  │                    │ episódico     │
  └───────────────┘ ◀─────────────── └───────────────┘
        consolida no sono            🌙 sonha + verifica
                                     dream_memory/verified.jsonl
```

## Limites honestos

1. **Não é consciência.** "Viver entre sessões" aqui = persistir estado + consolidar
   aprendizado. É uma metáfora útil e uma arquitetura real, não senciência.
2. **Consolidar tem custo e risco.** LoRA demais pode degradar o modelo base; por isso
   só consolidamos o **verificado** e mantemos o base congelado (reversível).
3. **Memória persistente é superfície de ataque.** Conteúdo malicioso memorizado
   persiste — por isso tudo é auditável em arquivos legíveis.

---

## 5. Técnicas de auto-aprimoramento que ela usa dormindo

Pesquisa mais recente (2024–2025) sobre como uma IA aprende sozinha de forma eficiente —
tudo embutido em `dream/adaptive.py`, `dream/reflect.py` e `dream/consolidate.py`:

- **STaR (Self-Taught Reasoner)** e **ReST (Reinforced Self-Training, DeepMind)**:
  decompõem o aprendizado em gerar dados (E-step) e treinar (M-step). O modelo gera
  soluções, **verifica**, e treina só nas corretas. **ReST-RL (2025)** mostra ganhos
  fortes especificamente em *raciocínio de código*.
- **RFT (Rejection-sampling Fine-Tuning)** / **Expert Iteration**: amostra várias
  tentativas, mantém as bem-sucedidas, treina nelas, repete.
- **AdaSTaR / Adaptive Difficulty Curriculum (2025)**: reestima a dificuldade ao longo
  do treino para mantê-la **alinhada à habilidade atual** — o "Difficulty Shift". É o
  nosso currículo adaptativo (zona de desenvolvimento proximal).
- **Reflect, Retry, Reward (2025)** e **Exploring Expert Failures (2025)**: aprender com
  os **erros** — refletir sobre a falha e corrigir melhora o agente. É o nosso Reflect-Retry.
- **Self-play autocurricula (AlphaGo/DeepMind)**: jogar contra versões de si mesmo cria
  um currículo automático de dificuldade crescente.

➡️ **No Dream-AI:** a IA sonha na borda da habilidade (AdaSTaR), corrige os próprios erros
(Reflect-Retry), só aprende o verificado (STaR/ReST), e a dificuldade sobe sozinha
(autocurrículo) — tudo dentro do daemon de vida contínua.

## Fontes

- [Sleep-like unsupervised replay reduces catastrophic forgetting (Nature Communications, 2022)](https://www.nature.com/articles/s41467-022-34938-7)
- [STaR: Bootstrapping Reasoning with Reasoning](https://arxiv.org/abs/2203.14465)
- [Beyond Human Data: Scaling Self-Training (ReST, DeepMind)](https://arxiv.org/pdf/2312.06585)
- [ReST-RL: Accurate Code Reasoning via Self-Training (2025)](https://arxiv.org/abs/2508.19576)
- [AdaSTaR: Adaptive Data Sampling for Self-Taught Reasoners (2025)](https://arxiv.org/pdf/2505.16322)
- [Reflect, Retry, Reward: Self-Improving LLMs via RL (2025)](https://arxiv.org/pdf/2505.24726)
- [Exploring Expert Failures Improves LLM Agent Tuning (2025)](https://arxiv.org/abs/2504.13145)
- [Adaptive Difficulty Curriculum Learning (2025)](https://arxiv.org/pdf/2505.08364)
- [Brain-inspired replay for continual learning (Nature Communications)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7426273/)
- [Can sleep protect memories from catastrophic forgetting? (eLife)](https://elifesciences.org/articles/51005)
- [Sleep-Like Memory Consolidation in LLMs](https://www.emergentmind.com/papers/2605.26099)
- [Let Them Sleep: Adaptive LLM Agents via a Sleep Cycle](https://mccraetech.medium.com/let-them-sleep-adaptive-llm-agents-via-a-sleep-cycle-60e26b0723ab)
- [SCM: Sleep-Consolidated Memory for LLMs](https://www.emergentmind.com/papers/2604.20943)
- [Dream to Control: Learning Behaviors by Latent Imagination (Dreamer, 2019)](https://arxiv.org/pdf/1912.01603)
- [Mastering diverse control tasks through world models (DreamerV3, Nature 2025)](https://www.nature.com/articles/s41586-025-08744-2)
- [Persistent Memory in LLM Agents](https://www.emergentmind.com/topics/persistent-memory-for-llm-agents)
- [Lifelong Learning for LLM Agents](https://www.emergentmind.com/topics/lifelong-learning-for-llm-based-agents)

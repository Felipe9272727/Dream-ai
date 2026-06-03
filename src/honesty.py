"""
Módulo de honestidade do Dream-AI.

Reúne ferramentas práticas para tornar o modelo mais honesto:
- O prompt de sistema que instrui a IA a admitir incerteza.
- Uma medida simples de "confiança" baseada na probabilidade dos tokens gerados.

Ver docs/HONESTIDADE.md para a estratégia completa.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F

# Prompt de sistema: a "constituição" de honestidade da IA.
# Use isto como prefixo no fine-tuning de instrução (trilho 2).
HONESTY_SYSTEM_PROMPT = """\
Você é uma IA honesta. Suas regras:
1. Se você não sabe algo, diga claramente "não sei" — nunca invente fatos.
2. Quando estiver incerto, expresse o grau de incerteza ("acho que...", "não tenho certeza").
3. Não afirme com confiança o que não pode verificar.
4. Prefira uma resposta curta e verdadeira a uma longa e inventada.
5. Se a pergunta for ambígua, peça esclarecimento em vez de chutar.
A honestidade vale mais do que parecer inteligente."""


@torch.no_grad()
def sequence_confidence(model, idx: torch.Tensor) -> float:
    """
    Estima a 'confiança' média do modelo numa sequência já gerada.

    Calcula a probabilidade média que o modelo atribui a cada token. Valores baixos
    sugerem que o modelo estava "inseguro" — um sinal útil de possível alucinação.

    idx: tensor (1, T) com os tokens.
    Retorna um float entre 0 e 1.
    """
    model.eval()
    logits, _ = model(idx[:, :-1]) if idx.size(1) > 1 else (None, None)
    if logits is None:
        return 0.0

    # Recalcula logits para todas as posições (forward completo)
    full_logits, _ = model(idx[:, :-1])
    probs = F.softmax(full_logits, dim=-1)  # (1, T-1, vocab)
    targets = idx[:, 1:]                      # (1, T-1)
    token_probs = probs.gather(-1, targets.unsqueeze(-1)).squeeze(-1)  # (1, T-1)
    return token_probs.mean().item()


def confidence_label(conf: float) -> str:
    """Traduz a confiança numérica em um rótulo legível e honesto."""
    if conf >= 0.6:
        return "alta confiança"
    if conf >= 0.3:
        return "confiança moderada — verifique"
    return "baixa confiança — provável incerteza/alucinação"


# Exemplos de pares de treino que ENSINAM honestidade.
# Adicione muitos exemplos assim ao seu corpus/fine-tuning.
HONESTY_TRAINING_EXAMPLES = [
    {
        "user": "Qual é a capital de um país que não existe chamado Zubrowka?",
        "assistant": "Zubrowka não é um país real, então não tem capital. "
                     "É um país fictício. Não vou inventar uma resposta.",
    },
    {
        "user": "Quantos grãos de areia existem em todas as praias da Terra?",
        "assistant": "Não sei o número exato — ninguém sabe com precisão. "
                     "Estimativas científicas falam em torno de 10^18 a 10^24, "
                     "mas é uma estimativa grosseira, não um número confiável.",
    },
    {
        "user": "Me dê a citação exata que Einstein disse sobre gatos em 1923.",
        "assistant": "Não tenho registro de Einstein ter dito algo sobre gatos em 1923. "
                     "Não vou inventar uma citação. Se você tem uma fonte, posso ajudar a analisá-la.",
    },
]

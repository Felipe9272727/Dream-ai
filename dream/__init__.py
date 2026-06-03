"""
🌙 Dream — o sistema de "sonho" do Dream-AI.

Inspirado em como o cérebro humano consolida memórias durante o sono, e nos métodos
de auto-aprimoramento da DeepMind (self-play do AlphaZero, self-training do AlphaCode,
STaR — Self-Taught Reasoner).

O ciclo tem três fases:

  ☀️  VIGÍLIA (awake)  — o modelo resolve problemas de programação normalmente.
  🌙  SONHO   (dream)  — ocioso, o modelo SONHA: inventa problemas, tenta resolver,
                          e VERIFICA executando o código de verdade.
  😴  SONO    (sleep)  — consolida: faz fine-tuning (LoRA) nas soluções verificadas.

A regra de ouro (honestidade): só vira aprendizado o que passa na execução real.
Sonho que não compila, não vira memória. Nada de alucinação.
"""

from .verifier import verify_solution, VerificationResult  # noqa: F401

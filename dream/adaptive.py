"""
🎚️ Currículo adaptativo — ela sonha na "zona de desenvolvimento proximal".

Baseado em pesquisa real (AdaSTaR, Adaptive Difficulty Curriculum Learning, self-play
autocurricula da DeepMind): aprender é mais eficiente quando os desafios estão na BORDA
da habilidade atual — nem fáceis demais (não ensina nada), nem difíceis demais (só
frustra). Conforme ela domina um nível, a dificuldade sobe sozinha (autocurrículo).

Também cuidamos da DIVERSIDADE: variar categorias evita que ela só fique boa em uma coisa
(mode collapse).
"""

from __future__ import annotations

import dataclasses
import random


@dataclasses.dataclass
class CurriculumState:
    """Estatísticas de aprendizado por dificuldade (persistível)."""
    # dificuldade -> [tentativas, acertos]
    stats: dict = dataclasses.field(default_factory=dict)
    frontier: int = 1   # dificuldade-alvo atual

    def record(self, difficulty: int, passed: bool) -> None:
        d = str(difficulty)
        if d not in self.stats:
            self.stats[d] = [0, 0]
        self.stats[d][0] += 1
        if passed:
            self.stats[d][1] += 1

    def success_rate(self, difficulty: int) -> float:
        d = str(difficulty)
        if d not in self.stats or self.stats[d][0] == 0:
            return 0.0
        return self.stats[d][1] / self.stats[d][0]

    def attempts(self, difficulty: int) -> int:
        return self.stats.get(str(difficulty), [0, 0])[0]


# Limiares da "zona de desenvolvimento proximal"
MASTERED = 0.85    # acima disso, já dominou → sobe a dificuldade
TOO_HARD = 0.30    # abaixo disso, difícil demais → desce a dificuldade
MIN_ATTEMPTS = 12  # só decide depois de tentativas suficientes (evita ruído)


def update_frontier(state: CurriculumState, max_difficulty: int = 5) -> int:
    """Reavalia a dificuldade-alvo com base no desempenho recente (autocurrículo)."""
    f = state.frontier
    rate = state.success_rate(f)
    attempts = state.attempts(f)

    if attempts >= MIN_ATTEMPTS:
        if rate >= MASTERED and f < max_difficulty:
            state.frontier = f + 1          # dominou → próximo nível
        elif rate < TOO_HARD and f > 1:
            state.frontier = f - 1          # difícil demais → volta um nível
    return state.frontier


def choose_difficulty(state: CurriculumState, rng: random.Random) -> int:
    """
    Escolhe a dificuldade do próximo sonho. Concentra na fronteira, mas às vezes
    revisita níveis mais fáceis (replay, evita esquecimento) e arrisca um mais difícil.
    """
    f = state.frontier
    r = rng.random()
    if r < 0.70:
        return f                                    # 70%: treina na fronteira
    elif r < 0.90:
        return max(1, f - rng.randint(1, 2))        # 20%: replay de algo já visto
    else:
        return min(5, f + 1)                        # 10%: ousa um pouco além


def report(state: CurriculumState) -> str:
    linhas = [f"🎚️ Currículo (fronteira atual: nível {state.frontier})"]
    for d in sorted(state.stats, key=int):
        a, s = state.stats[d]
        linhas.append(f"   nível {d}: {s}/{a} acertos ({(s/a*100 if a else 0):.0f}%)")
    return "\n".join(linhas)

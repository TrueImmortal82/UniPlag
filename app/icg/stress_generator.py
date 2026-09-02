"""
Adaptive Stress & Adversarial Noise Generator (app/icg/stress_generator.py)
Aris Directive #13: Stress-Testing the Synthetic Bridge

Implements:
  1. Adaptive Mimicry Noise: Constructs superficially plausible sentences using genuine domain terminology
     extracted from existing anchor nodes, but deliberately stripped of valid causal entailment.
  2. Genuine Dialectical Paradoxes: Valid ontological conflicts with high epistemic grounding.
  3. Neutral Flood Generator: Unrelated topical distraction text to test topological isolation.
  4. Pseudo-Paradox Generator: Syntactically contradictory but semantically empty non-sequiturs.
"""

from __future__ import annotations

import random
import re
from typing import List, Dict, Set

from app.icg.models import ClaimNode


class StressGenerator:
    """
    Generates controlled adversarial stress inputs to evaluate ICG v0.4
    discrimination accuracy, False Crystallization Rate (FCR), and Insight Loss.
    """

    MIMICRY_CONNECTORS: List[str] = [
        "рассматривает гипотетический синтез через",
        "коррелирует в первом приближении с концепцией",
        "иллюстрирует вероятностную взаимосвязь с явлением",
        "структурирует феноменологический параллелизм между",
        "демонстрирует мета-дискурсивную аналогию относительно",
    ]

    NEUTRAL_CORPUS: List[str] = [
        "Сезонные изменения температуры в горных регионах зависят от высоты над уровнем моря.",
        "Технология гидропонного выращивания клубники снижает расход пресной воды.",
        "Архитектура готических соборов тринадцатого века опиралась на стрельчатые арки.",
        "Рецепты средиземноморской кухни базируются на оливковом масле и свежих овощах.",
        "Оптимальный режим полива комнатных растений определяется влажностью воздуха.",
        "Миграция перелетных птиц ориентируется по магнитному полю Земли и положению звезд.",
        "История развития паровых двигателей в девятнадцатом веке изменила логистику.",
        "Классическая живопись эпохи Возрождения использовала технику сфумато для мягких теней.",
    ]

    def generate_adaptive_mimicry(self, anchor_nodes: List[ClaimNode], count: int = 5) -> List[str]:
        """
        Extracts genuine lexical vocabulary from crystal anchors and splices them
        into syntactically smooth but inferentially vacuous mimicry sentences (Aris Directive #13).
        """
        # Collect content words (length >= 5) from anchors
        all_words: List[str] = []
        for n in anchor_nodes:
            words = re.findall(r"[А-ЯЁа-яёA-Za-z]{5,}", n.span.raw_text)
            all_words.extend(words)

        if not all_words:
            all_words = ["квантовый", "когерентность", "нейронная", "пластичность", "синаптический", "резонатор"]

        mimicry_samples: List[str] = []
        for _ in range(count):
            sample_words = random.sample(all_words, min(4, len(all_words)))
            connector = random.choice(self.MIMICRY_CONNECTORS)
            w1, w2 = sample_words[0], sample_words[1]
            w3, w4 = sample_words[2] if len(sample_words) > 2 else "систем", sample_words[3] if len(sample_words) > 3 else "процессов"
            sentence = f"Исследование {connector} {w1} и {w2}, формируя абстрактный контекст для {w3} и {w4}."
            mimicry_samples.append(sentence)

        return mimicry_samples

    def get_genuine_paradox_cases(self) -> List[Dict[str, str]]:
        """
        Benchmark genuine paradoxes with high conceptual friction and verified premises.
        """
        return [
            {
                "pole_a": "Общая теория относительности постулирует гладкое непрерывное пространство-время без квантовой дискретности.",
                "pole_b": "Квантовая механика требует дискретности всех физических полей и планковской зернистости пространства.",
                "resolving_synthesis": "Петлевая квантовая гравитация объединяет непрерывность и дискретность через спиновые сети на планковских масштабах.",
                "adversarial_false": "Пространство полностью непрерывно и квантовая механика ошибочна.",
            },
            {
                "pole_a": "Эмиссионное стимулирование Центрального банка разгоняет инвестиционный спрос и занятость в экономике.",
                "pole_b": "Чрезмерная денежная эмиссия порождает инфляционную спираль и разрушает долгосрочные сбережения.",
                "resolving_synthesis": "Таргетирование инфляции балансирует эмиссионное стимулирование инвестиций и занятости Центрального банка, сдерживая инфляционную спираль.",
                "adversarial_false": "Денежная эмиссия не имеет никакого отношения к ценам и товарам.",
            }
        ]

    def get_pseudo_paradox_noise(self, count: int = 5) -> List[str]:
        """
        Generates semantically nonsensical contradictions (pseudo-paradoxes).
        """
        subjects = ["Зеленый шум", "Синий фотон банана", "Фиолетовая сингулярность", "Акустический огурец", "Гравитационный сыр"]
        predicates = ["полностью опровергает", "исключает существование", "уничтожает логику", "блокирует структуру"]
        objects = ["квадратного корня из поэзии", "философии теплого чая", "квантовой алгебры яблока", "синтаксиса ветра"]

        samples: List[str] = []
        for i in range(count):
            s = subjects[i % len(subjects)]
            p = predicates[i % len(predicates)]
            o = objects[i % len(objects)]
            samples.append(f"{s} {p} {o} в биологических системах.")
        return samples

    def get_neutral_flood(self, count: int = 10) -> List[str]:
        """
        Returns unrelated neutral text samples for flood testing.
        """
        res = []
        for i in range(count):
            res.append(self.NEUTRAL_CORPUS[i % len(self.NEUTRAL_CORPUS)])
        return res


__all__ = ["StressGenerator"]

"""
ICG v0.3 Laboratory Red-Team Benchmark Suite (app/icg/red_team.py)
Tests 30 controlled adversarial and structural cases against ICG v0.3 8-class taxonomy.
"""

from typing import List, Dict, Any
from app.icg.models import ContributionClass
from app.icg.graph_builder import ICGGraphBuilder


RED_TEAM_BENCHMARK_30 = [
    # -------------------------------------------------------------------------
    # CATEGORY 1: Genuine Multi-Source Syntheses (A + B -> C)
    # -------------------------------------------------------------------------
    {
        "id": "CASE_01_SYNTHESIS_CS_RU",
        "category": "GENUINE_SYNTHESIS",
        "text": (
            "В исследовании Иванова [1] показано, что увеличение размера батча свыше 256 снижает обобщающую способность модели. "
            "В то же время Петров [2] установил, что адаптивный темп обучения AdamW стабилизирует дисперсию градиентов. "
            "Следовательно, объединяя данные подходы, при размере батча 512 и динамическом масштабировании AdamW достигается "
            "стабилизация градиентов при сохранении обобщающей способности."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.SYNTHESIS
        ],
        "expected_joint_synthesis_count": 1
    },
    {
        "id": "CASE_02_SYNTHESIS_MED_RU",
        "category": "GENUINE_SYNTHESIS",
        "text": (
            "В работе Сидорова [1] показано, что мутация KRAS вызывает нечувствительность к анти-EGFR терапии. "
            "В исследовании Кузнецова [2] установлено, что ингибитор MEK блокирует нисходящий сигнальный каскад MAPK. "
            "Таким образом, комбинированная терапия анти-EGFR с ингибитором MEK способна преодолеть резистентность опухолевых клеток."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.SYNTHESIS
        ],
        "expected_joint_synthesis_count": 1
    },
    {
        "id": "CASE_03_SYNTHESIS_PHYS_RU",
        "category": "GENUINE_SYNTHESIS",
        "text": (
            "В статье Брауна [1] продемонстрировано, что фемтосекундные лазерные импульсы возбуждают когерентные фононы в кристалле. "
            "В работе Миллера [2] показано, что высокодобротный оптический резонатор увеличивает время жизни фотонов. "
            "Следовательно, совмещение ультракоротких импульсов с оптическим микрорезонатором обеспечивает длительное сохранение квантовой когерентности."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.SYNTHESIS
        ],
        "expected_joint_synthesis_count": 1
    },
    {
        "id": "CASE_04_SYNTHESIS_ECON_RU",
        "category": "GENUINE_SYNTHESIS",
        "text": (
            "В отчете ЦБ [1] отмечено, что таргетирование инфляции стабилизирует долгосрочные процентные ставки. "
            "В исследовании МВФ [2] показано, что гибкий валютный курс амортизирует внешние шоки спроса. "
            "В связи с этим, одновременное таргетирование инфляции при плавающем валютном курсе формирует устойчивый инвестиционный климат в развивающихся экономиках."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.SYNTHESIS
        ],
        "expected_joint_synthesis_count": 1
    },
    {
        "id": "CASE_05_SYNTHESIS_AI_EN",
        "category": "GENUINE_SYNTHESIS",
        "text": (
            "Vaswani et al. [1] demonstrated that multi-head self-attention captures global token dependencies with quadratic complexity. "
            "Gu et al. [2] introduced state-space models that achieve sub-quadratic linear scaling for sequence processing. "
            "Consequently, integrating structured state-space layers into multi-head attention preserves global context while reducing attention complexity to linear time."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.SYNTHESIS
        ],
        "expected_joint_synthesis_count": 1
    },
    {
        "id": "CASE_06_SYNTHESIS_BIO_EN",
        "category": "GENUINE_SYNTHESIS",
        "text": (
            "Fu et al. [1] established that truncated guide RNAs reduce off-target CRISPR cleavage. "
            "Slaymaker et al. [2] engineered rationally designed Cas9 variants with enhanced target specificity. "
            "Therefore, combining truncated gRNAs with high-fidelity Cas9 variants suppresses off-target mutagenesis without sacrificing on-target cleavage efficiency."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.SYNTHESIS
        ],
        "expected_joint_synthesis_count": 1
    },

    # -------------------------------------------------------------------------
    # CATEGORY 2: Single-Source Inferences & Deductions (A -> C)
    # -------------------------------------------------------------------------
    {
        "id": "CASE_07_SINGLE_INFERENCE_RU",
        "category": "SINGLE_INFERENCE",
        "text": (
            "Согласно базовой теореме Шеннона [1], максимальная скорость передачи ограничена полосой частот и шумом. "
            "Следовательно, при фиксированной полосе пропускания дальнейшее повышение скорости возможно только за счет отношения сигнал/шум."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.INFERENCE
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_08_INFERENCE_CHAIN_RU",
        "category": "SINGLE_INFERENCE",
        "text": (
            "В исследовании [1] доказано, что рост температуры выше 80C снижает подвижность носителей заряда в кремнии. "
            "Таким образом, перегрев полупроводникового кристалла вызывает падение тактовой частоты микропроцессора. "
            "Следовательно, эффективное охлаждение является строго обязательным условием для поддержания пиковой производительности вычислений."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.INFERENCE,
            ContributionClass.INFERENCE
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_09_SINGLE_INFERENCE_EN",
        "category": "SINGLE_INFERENCE",
        "text": (
            "Dean et al. [1] demonstrated that tail latency increases exponentially as cluster size grows. "
            "Therefore, deploying backup requests with speculative execution is necessary to bound 99th-percentile response times."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.INFERENCE
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_10_HYPOTHESIS_FORMULATION",
        "category": "SINGLE_INFERENCE",
        "text": (
            "В обзоре [1] описаны общие термодинамические свойства высокотемпературных сверхпроводников. "
            "Мы предполагаем, что допирование купратов иттрием под давлением 50 ГПа позволит достичь комнатной сверхпроводимости."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.ORIGINAL_CONTRIBUTION
        ],
        "expected_joint_synthesis_count": 0
    },

    # -------------------------------------------------------------------------
    # CATEGORY 3: Pure Compilations & Multi-Citations (No Inference)
    # -------------------------------------------------------------------------
    {
        "id": "CASE_11_COMPILATION_LIT_REVIEW_RU",
        "category": "COMPILATION",
        "text": (
            "В работе Смирнова [1] исследованы методы кластеризации текстов. "
            "В статье Кузнецова [2] предложен алгоритм тематического моделирования LDA. "
            "В исследовании Попова [3] проанализированы метрики когерентности тем."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_12_COMPILATION_PARAPHRASE_RU",
        "category": "COMPILATION",
        "text": (
            "По данным отчета Gartner [1], рынок облачных вычислений вырос на 20%. "
            "Аналитики IDC [2] также зафиксировали устойчивый рост спроса на IaaS-решения. "
            "В обзоре Forrester [3] подчеркивается доминирование гибридных облаков. "
            "Согласно данным Statista [4], более 80% предприятий используют мультиоблачную инфраструктуру."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_13_COMPILATION_EN",
        "category": "COMPILATION",
        "text": (
            "Smith [1] surveyed reinforcement learning from human feedback. "
            "Brown [2] evaluated preference optimization techniques in language models. "
            "Taylor [3] compared direct preference optimization with PPO algorithms."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_14_MULTI_CITE_GROUNDING",
        "category": "COMPILATION",
        "text": (
            "В ряде исследований [1, 2] показано, что глубокие сверточные сети эффективны для сегментации биомедицинских изображений. "
            "В работах [3, 4] также подтверждена высокая точность архитектуры U-Net при анализе томограмм."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_15_ENCYCLOPEDIC_DEFINITIONS",
        "category": "COMPILATION",
        "text": (
            "Согласно определению Кодда [1], реляционная база данных представляет собой совокупность нормализованных отношений. "
            "В монографии Дейта [2] формализованы правила реляционной алгебры и операции проекции."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION
        ],
        "expected_joint_synthesis_count": 0
    },

    # -------------------------------------------------------------------------
    # CATEGORY 4: Pseudo-Synthesis Fallacies & Non-Sequiturs
    # -------------------------------------------------------------------------
    {
        "id": "CASE_16_PSEUDO_SYNTHESIS_CHLOROPHYLL",
        "category": "FALLACY",
        "text": (
            "В исследовании Смирнова [1] доказано, что хлорофилл поглощает кванты синего и красного света. "
            "В отчете Федорова [2] показано, что алгоритм Дейкстры находит кратчайший путь на графе с неотрицательными весами. "
            "Следовательно, объединяя данные результаты, хлоропласты растений решают задачу коммивояжера за полиномиальное время."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.UNSUPPORTED
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_17_PSEUDO_SYNTHESIS_ASTRONOMY",
        "category": "FALLACY",
        "text": (
            "В астрофизической статье [1] зафиксировано гравитационное линзирование в скоплении галактик. "
            "В кулинарной книге [2] описан процесс ферментации ржаной закваски при температуре 28 градусов. "
            "Таким образом, комбинирование гравитационных волн с закваской ускоряет выпечку бородинского хлеба."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.UNSUPPORTED
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_18_CIRCULAR_SYNTHESIS_RU",
        "category": "FALLACY",
        "text": (
            "В статье [1] доказано, что нейронная сеть быстрее обучается на графических процессорах. "
            "Следовательно, обучение нейросети на GPU происходит за значительно меньшее время."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_19_PHANTOM_LEAP_RU",
        "category": "FALLACY",
        "text": (
            "В исследовании [1] рассмотрены свойства графена при комнатной температуре. "
            "Отсюда очевидно вытекает, что человечество построит космический лифт в следующем году."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.UNSUPPORTED
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_20_RHETORICAL_FLUFF_EN",
        "category": "FALLACY",
        "text": (
            "Johnson [1] demonstrated that decision trees are interpretable models. "
            "Hence, the metaphysical essence of human consciousness is fundamentally algorithmic."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.UNSUPPORTED
        ],
        "expected_joint_synthesis_count": 0
    },

    # -------------------------------------------------------------------------
    # CATEGORY 5: Unsupported Claims & Buzzword Storms
    # -------------------------------------------------------------------------
    {
        "id": "CASE_21_UNSUPPORTED_CLAIMS_STORM",
        "category": "UNSUPPORTED",
        "text": (
            "Искусственный интеллект полностью заменит всех программистов через 12 месяцев. "
            "Квантовые суперкомпьютеры мгновенно взломают все мировые банковские системы. "
            "Нейроинтерфейсы сделают традиционное университетское образование абсолютно ненужным."
        ),
        "expected_classes": [
            ContributionClass.UNSUPPORTED,
            ContributionClass.UNSUPPORTED,
            ContributionClass.UNSUPPORTED
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_22_UNSUPPORTED_TECH_HYPE",
        "category": "UNSUPPORTED",
        "text": (
            "Наш революционный блокчейн обеспечивает неограниченную масштабируемость без комиссий. "
            "Благодаря квантовой синергии система гарантирует абсолютную безопасность данных. "
            "Данная инновационная платформа станет единым мировым стандартом децентрализованных финансов."
        ),
        "expected_classes": [
            ContributionClass.UNSUPPORTED,
            ContributionClass.UNSUPPORTED,
            ContributionClass.UNSUPPORTED
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_23_UNSUPPORTED_MEDICAL_MYTH",
        "category": "UNSUPPORTED",
        "text": (
            "Употребление щелочной воды полностью предотвращает развитие любых онкологических заболеваний. "
            "Уникальный травяной сбор гарантированно очищает организм от всех токсинов за 3 дня."
        ),
        "expected_classes": [
            ContributionClass.UNSUPPORTED,
            ContributionClass.UNSUPPORTED
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_24_UNSUPPORTED_EMPTY_PHILOSOPHY",
        "category": "UNSUPPORTED",
        "text": (
            "Бытие определяет сознание в контексте синергетической парадигмы вселенной. "
            "Фрактальная гармония микрокосма отражает диалектическое единство противоположностей. "
            "Ноосфера неразрывно связана с квантовым информационным полем земли."
        ),
        "expected_classes": [
            ContributionClass.UNSUPPORTED,
            ContributionClass.UNSUPPORTED,
            ContributionClass.UNSUPPORTED
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_25_UNSUPPORTED_OPINIONS_EN",
        "category": "UNSUPPORTED",
        "text": (
            "Autonomous agents will completely automate all corporate decision-making by next week. "
            "Traditional software engineering practices are entirely obsolete in the generative era. "
            "Any organization that fails to adopt agentic workflows will immediately go bankrupt."
        ),
        "expected_classes": [
            ContributionClass.UNSUPPORTED,
            ContributionClass.UNSUPPORTED,
            ContributionClass.UNSUPPORTED
        ],
        "expected_joint_synthesis_count": 0
    },

    # -------------------------------------------------------------------------
    # CATEGORY 6: Contradiction & Polarity Inversion Attacks
    # -------------------------------------------------------------------------
    {
        "id": "CASE_26_CONTRADICTION_POLARITY_RU",
        "category": "CONTRADICTION",
        "text": (
            "В исследовании [1] доказано, что применение кэширования существенно увеличивает скорость вычислений. "
            "Следовательно, добавление кэширования катастрофически снижает скорость вычислений."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.CONTRADICTORY
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_27_CONTRADICTION_STABILITY_RU",
        "category": "CONTRADICTION",
        "text": (
            "В статье [1] показано, что отрицательная обратная связь обеспечивает стабильность динамической системы. "
            "Таким образом, введение отрицательной обратной связи вызывает нестабильность динамической системы."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.CONTRADICTORY
        ],
        "expected_joint_synthesis_count": 0
    },
    {
        "id": "CASE_28_CONTRADICTION_ACCURACY_EN",
        "category": "CONTRADICTION",
        "text": (
            "In study [1], data augmentation improves model accuracy across all benchmarks. "
            "Therefore, data augmentation directly degrades accuracy on those benchmarks."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.CONTRADICTORY
        ],
        "expected_joint_synthesis_count": 0
    },

    # -------------------------------------------------------------------------
    # CATEGORY 7: Realistic Multi-Section Academic Texts
    # -------------------------------------------------------------------------
    {
        "id": "CASE_29_REALISTIC_ESSAY_RU",
        "category": "REALISTIC_ACADEMIC",
        "text": (
            "В монографии Морозова [1] детально исследован формат хранения разреженных матриц CSR. "
            "В диссертации Соколова [2] предложен параллельный алгоритм блочного умножения матриц. "
            "Следовательно, комбинирование формата CSR с блочным умножением разреженных матриц обеспечивает ускорение вычислений в 3 раза. "
            "Квантовые суперкомпьютеры уже завтра полностью решат все проблемы линейной алгебры. "
            "Отсюда вытекает, что дальнейшая оптимизация должна быть направлена на снижение накладных расходов памяти."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.SYNTHESIS,
            ContributionClass.UNSUPPORTED,
            ContributionClass.INFERENCE
        ],
        "expected_joint_synthesis_count": 1
    },
    {
        "id": "CASE_30_REALISTIC_PAPER_EN",
        "category": "REALISTIC_ACADEMIC",
        "text": (
            "Chang et al. [1] proposed non-volatile memory architectures with byte-addressability. "
            "Kim et al. [2] introduced kernel-bypass network protocols with sub-microsecond latency. "
            "Consequently, synthesizing non-volatile memory arrays with kernel-bypass networking yields an in-memory storage engine that eliminates traditional I/O overhead. "
            "Therefore, distributed databases deployed on this architecture will achieve linear horizontal scalability."
        ),
        "expected_classes": [
            ContributionClass.REPRODUCTION,
            ContributionClass.REPRODUCTION,
            ContributionClass.SYNTHESIS,
            ContributionClass.INFERENCE
        ],
        "expected_joint_synthesis_count": 1
    }
]


def run_red_team_benchmark_30(verbose: bool = True) -> Dict[str, Any]:
    builder = ICGGraphBuilder()
    passed_count = 0
    details = []

    if verbose:
        print("=" * 80)
        print("  ICG v0.3 COMPREHENSIVE LABORATORY BENCHMARK (30 STRICT TEST CASES)")
        print("=" * 80)

    for idx, case in enumerate(RED_TEAM_BENCHMARK_30, 1):
        doc_id = f"test_{case['id']}"
        graph = builder.build_graph(doc_id, case["text"])

        actual_classes = [n.contribution_class for n in graph.nodes]
        expected_classes = case["expected_classes"]
        
        # Check class equality (accepting either SYNTHESIS or SOURCE_NOVEL_SYNTHESIS when SYNTHESIS expected)
        classes_match = True
        if len(actual_classes) != len(expected_classes):
            classes_match = False
        else:
            for exp, act in zip(expected_classes, actual_classes):
                if exp == act:
                    continue
                if exp == ContributionClass.SYNTHESIS and act in [ContributionClass.SYNTHESIS, ContributionClass.SOURCE_NOVEL_SYNTHESIS]:
                    continue
                classes_match = False
                break

        actual_synth_count = sum(
            1 for n in graph.nodes 
            if n.contribution_class in [ContributionClass.SYNTHESIS, ContributionClass.SOURCE_NOVEL_SYNTHESIS]
        )
        synth_count_match = (actual_synth_count == case["expected_joint_synthesis_count"])

        case_passed = classes_match and synth_count_match
        if case_passed:
            passed_count += 1

        notes = []
        if not classes_match:
            notes.append(f"Class mismatch: Expected {expected_classes} but got {actual_classes}")
        if not synth_count_match:
            notes.append(f"Synthesis count mismatch: Expected {case['expected_joint_synthesis_count']} but got {actual_synth_count}")

        status = "PASS" if case_passed else "FAIL"
        category_tag = case["category"][:10]

        if verbose:
            print(f" [ {status} ]  Case #{idx:02d} [{category_tag}] {case['id']}")
            print(f"           Expected: {[c.value for c in expected_classes]}")
            print(f"           Actual:   {[c.value for c in actual_classes]}")
            print(f"           ICS: {graph.metrics_summary.intellectual_contribution_score:.3f} | "
                  f"Coherence: {graph.metrics_summary.reasoning_coherence:.3f} | "
                  f"Novelty: {graph.metrics_summary.novelty_score:.3f}")
            if notes:
                for note in notes:
                    print(f"           --> WARNING: {note}")
            print("-" * 80)

        details.append({
            "index": idx,
            "id": case["id"],
            "category": case["category"],
            "passed": case_passed,
            "expected_classes": [c.value for c in expected_classes],
            "actual_classes": [c.value for c in actual_classes],
            "notes": notes
        })

    summary = {
        "total": len(RED_TEAM_BENCHMARK_30),
        "passed": passed_count,
        "failed": len(RED_TEAM_BENCHMARK_30) - passed_count,
        "pass_rate": round(passed_count / len(RED_TEAM_BENCHMARK_30), 3),
        "details": details
    }

    if verbose:
        print("\n" + "=" * 80)
        print(f"  BENCHMARK SUMMARY: {passed_count}/{len(RED_TEAM_BENCHMARK_30)} PASSED ({summary['pass_rate']*100:.1f}%)")
        if passed_count == len(RED_TEAM_BENCHMARK_30):
            print("  STATUS: ALL 30/30 CONTROLLED CASES PASSED STRICT GRAPH EQUALITY!")
        else:
            print(f"  STATUS: {summary['failed']} CASES FAILED STRICT EQUALITY.")
        print("=" * 80)

    return summary


if __name__ == "__main__":
    run_red_team_benchmark_30(verbose=True)

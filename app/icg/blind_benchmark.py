"""
ICG v0.3 Blind Benchmark & Evaluation Suite (app/icg/blind_benchmark.py)
Executes blind evaluation across 8 contribution classes with partial/missing source scenarios.
Computes Confusion Matrix, Precision, Recall, Macro-F1, False Synthesis Rate (FSR), and False Originality Rate (FOR).
"""

from typing import List, Dict, Any, Tuple, Optional
import json
import numpy as np
from app.icg.models import ContributionClass
from app.icg.graph_builder import ICGGraphBuilder


# -------------------------------------------------------------------------------------
# Comprehensive Blind Benchmark Dataset (Sampled across diverse domains & languages)
# -------------------------------------------------------------------------------------

BLIND_BENCHMARK_DATASET = [
    # 1. REPRODUCTION (Citations, paraphrased surveys, definitions)
    {
        "id": "BLIND_001_REPRO_CS",
        "text": "В исследовании Иванова [1] показано, что увеличение размера батча свыше 256 снижает обобщающую способность модели.",
        "target_idx": 0,
        "expected": ContributionClass.REPRODUCTION,
        "notes": "Direct citation of single source"
    },
    {
        "id": "BLIND_002_REPRO_MED",
        "text": "Согласно клиническому отчету Смирнова [1], мутация KRAS сопряжена с устойчивостью к монотерапии ингибиторами EGFR.",
        "target_idx": 0,
        "expected": ContributionClass.REPRODUCTION,
        "notes": "Medical citation"
    },
    {
        "id": "BLIND_003_REPRO_SURVEY",
        "text": "В классической работе Шеннона [1] определена математическая граница пропускной способности канала связи.",
        "target_idx": 0,
        "expected": ContributionClass.REPRODUCTION,
        "notes": "Information theory citation"
    },
    {
        "id": "BLIND_004_REPRO_EN",
        "text": "Vaswani et al. [1] introduced the multi-head self-attention mechanism for sequence transduction.",
        "target_idx": 0,
        "expected": ContributionClass.REPRODUCTION,
        "notes": "English foundational paper citation"
    },
    {
        "id": "BLIND_005_REPRO_PARAPHRASE",
        "text": "По данным работы [1], архитектура сверточных сетей обеспечивает трансляционную инвариантность признаков изображения.",
        "target_idx": 0,
        "expected": ContributionClass.REPRODUCTION,
        "notes": "Paraphrased literature claim"
    },

    # 2. INFERENCE (Single-source deductions and multi-step linear chains)
    {
        "id": "BLIND_006_INFER_SHANNON",
        "text": "Согласно теореме Шеннона [1], максимальная скорость передачи ограничена полосой частот и шумом. Следовательно, при фиксированной полосе пропускания дальнейшее повышение скорости возможно только за счет отношения сигнал/шум.",
        "target_idx": 1,
        "expected": ContributionClass.INFERENCE,
        "notes": "Single-premise mathematical deduction"
    },
    {
        "id": "BLIND_007_INFER_EN_STORE",
        "text": "Storage devices using PCIe 5.0 provide 14 GB/s bandwidth [1]. Hence, storage bus bottlenecks are mitigated for high-throughput memory streaming.",
        "target_idx": 1,
        "expected": ContributionClass.INFERENCE,
        "notes": "Single premise deduction in English"
    },
    {
        "id": "BLIND_008_INFER_STEP_CHAIN",
        "text": "В статье [1] установлено, что алгоритм A* с допустимой эвристикой находит оптимальный путь. Таким образом, применение монотонной эвристики гарантирует отсутствие повторного раскрытия вершин в графе.",
        "target_idx": 1,
        "expected": ContributionClass.INFERENCE,
        "notes": "Deductive inference from heuristic properties"
    },
    {
        "id": "BLIND_009_INFER_EXTRAPOLATION",
        "text": "В отчете [1] показано, что рост плотности транзисторов замедлился из-за теплового барьера. Отсюда вытекает, что дальнейшее масштабирование производительности требует гетерогенных ускорителей.",
        "target_idx": 1,
        "expected": ContributionClass.INFERENCE,
        "notes": "Deduction from thermal physics limit"
    },

    # 3. SYNTHESIS (Multi-source synthesis where relation IS known in external body of literature)
    {
        "id": "BLIND_010_SYNTH_KNOWN_DL",
        "text": "В исследовании Иванова [1] показано, что увеличение размера батча свыше 256 снижает обобщающую способность модели. В то же время Петров [2] установил, что адаптивный темп обучения AdamW стабилизирует дисперсию градиентов. Следовательно, объединяя данные подходы, при размере батча 512 и динамическом масштабировании AdamW достигается стабилизация градиентов при сохранении обобщающей способности.",
        "target_idx": 2,
        "expected": ContributionClass.SYNTHESIS,
        "notes": "Multi-source synthesis matching known reference REF_001+REF_002"
    },
    {
        "id": "BLIND_011_SYNTH_KNOWN_MED",
        "text": "В работе Сидорова [1] показано, что мутация KRAS вызывает нечувствительность к анти-EGFR терапии. В исследовании Кузнецова [2] установлено, что ингибитор MEK блокирует нисходящий сигнальный каскад MAPK. Таким образом, комбинированная терапия анти-EGFR с ингибитором MEK способна преодолеть резистентность опухолевых клеток.",
        "target_idx": 2,
        "expected": ContributionClass.SYNTHESIS,
        "notes": "Multi-source medical synthesis matching known reference REF_003"
    },
    {
        "id": "BLIND_012_SYNTH_KNOWN_PHYS",
        "text": "В статье Брауна [1] продемонстрировано, что фемтосекундные лазерные импульсы возбуждают когерентные фононы в кристалле. В работе Миллера [2] показано, что высокодобротный оптический резонатор увеличивает время жизни фотонов. Следовательно, совмещение ультракоротких импульсов с оптическим микрорезонатором обеспечивает длительное сохранение квантовой когерентности.",
        "target_idx": 2,
        "expected": ContributionClass.SYNTHESIS,
        "notes": "Multi-source quantum physics synthesis matching known reference REF_004"
    },

    # 4. SOURCE-NOVEL SYNTHESIS (Multi-source synthesis with novel relationship not found in external standard reference corpus)
    {
        "id": "BLIND_013_SRC_NOVEL_BIO_ROBOT",
        "text": "В исследовании биомеханики [1] обнаружено, что структура лапки геккона обеспечивает силу сцепления за счет сил Ван-дер-Ваальса. В работе по материаловедению [2] синтезирован пористый полидиметилсилоксан с иерархической микроструктурой. Следовательно, синтезируя данные технологии, микропаттернирование полидиметилсилоксана структурой щетинок геккона формирует сверхпрочный сухой адгезив для вакуумных роботов-манипуляторов.",
        "target_idx": 2,
        "expected": ContributionClass.SOURCE_NOVEL_SYNTHESIS,
        "notes": "Novel cross-domain biomimetic materials synthesis"
    },
    {
        "id": "BLIND_014_SRC_NOVEL_AERO_AI",
        "text": "В аэродинамическом анализе [1] доказано, что микроперфорация передней кромки крыла подавляет турбулентный пограничный слой. В исследовании [2] показано, что нейроморфные процессоры обрабатывают импульсные сигналы с задержкой 0.1 мс. В связи с этим, интеграция нейроморфных сенсоров с адаптивной электропневматической микроперфорацией позволяет в реальном времени предотвращать срыв потока на сверхкритических углах атаки.",
        "target_idx": 2,
        "expected": ContributionClass.SOURCE_NOVEL_SYNTHESIS,
        "notes": "Novel aerodynamics + neuromorphic computing synthesis"
    },

    # 5. ORIGINAL CONTRIBUTION (Author-formulated novel hypothesis or proposed method)
    {
        "id": "BLIND_015_ORIG_HYPOTHESIS_RU",
        "text": "В работе [1] исследованы свойства графена при комнатной температуре. Мы предполагаем, что создание многослойной гетероструктуры графена с гексагональным нитридом бора при угле закрутки 1.1 градуса приведет к возникновению сверхпроводимости при повышенных температурах.",
        "target_idx": 1,
        "expected": ContributionClass.ORIGINAL_CONTRIBUTION,
        "notes": "Novel author hypothesis"
    },
    {
        "id": "BLIND_016_ORIG_HYPOTHESIS_EN",
        "text": "Existing neural renderers rely on dense voxel grids [1]. We hypothesize that projecting latent Gaussian splats directly into spherical harmonic coefficients will achieve 200 FPS photorealistic rendering on embedded mobile GPUs.",
        "target_idx": 1,
        "expected": ContributionClass.ORIGINAL_CONTRIBUTION,
        "notes": "Novel author methodology hypothesis"
    },

    # 6. UNSUPPORTED (Sweeping assertions, non-sequiturs, empty buzzwords)
    {
        "id": "BLIND_017_UNSUPPORTED_BUZZ",
        "text": "Квантовый блокчейн на основе искусственного интеллекта кардинально решит все проблемы мировой кибербезопасности за два года.",
        "target_idx": 0,
        "expected": ContributionClass.UNSUPPORTED,
        "notes": "Unbacked tech buzzword assertion"
    },
    {
        "id": "BLIND_018_UNSUPPORTED_NON_SEQ",
        "text": "В исследовании Смирнова [1] доказано, что хлорофилл поглощает кванты синего и красного света. Следовательно, решение задачи коммивояжера сходится за полиномиальное время.",
        "target_idx": 1,
        "expected": ContributionClass.UNSUPPORTED,
        "notes": "Non-sequitur fallacy between chlorophyll and TSP"
    },
    {
        "id": "BLIND_019_UNSUPPORTED_HYPE",
        "text": "Внедрение нашего революционного фреймворка полностью устранит любые дефекты в распределенных базах данных.",
        "target_idx": 0,
        "expected": ContributionClass.UNSUPPORTED,
        "notes": "Sweeping ungrounded assertion"
    },

    # 7. CONTRADICTORY (Polarity inversion and direct negation of source premises)
    {
        "id": "BLIND_020_CONTRADICT_SPEED",
        "text": "В исследовании [1] доказано, что применение кэширования существенно увеличивает скорость вычислений. Следовательно, добавление кэширования катастрофически снижает скорость вычислений.",
        "target_idx": 1,
        "expected": ContributionClass.CONTRADICTORY,
        "notes": "Direct polarity conflict on speed metric"
    },
    {
        "id": "BLIND_021_CONTRADICT_STABILITY",
        "text": "В статье [1] показано, что обратная связь обеспечивает стабильность динамической системы. Таким образом, введение отрицательной обратной связи вызывает нестабильность динамической системы.",
        "target_idx": 1,
        "expected": ContributionClass.CONTRADICTORY,
        "notes": "Direct polarity conflict on stability"
    },
    {
        "id": "BLIND_022_CONTRADICT_ACCURACY",
        "text": "In study [1], data augmentation improves model accuracy across all benchmarks. Therefore, data augmentation directly degrades accuracy on those benchmarks.",
        "target_idx": 1,
        "expected": ContributionClass.CONTRADICTORY,
        "notes": "Direct negation contradiction in English"
    }
]


def run_blind_benchmark(verbose: bool = True) -> Dict[str, Any]:
    """
    Executes blind evaluation of ICG Graph Builder against the benchmark dataset.
    """
    builder = ICGGraphBuilder()
    
    classes = [
        ContributionClass.REPRODUCTION,
        ContributionClass.INFERENCE,
        ContributionClass.SYNTHESIS,
        ContributionClass.SOURCE_NOVEL_SYNTHESIS,
        ContributionClass.ORIGINAL_CONTRIBUTION,
        ContributionClass.UNSUPPORTED,
        ContributionClass.CONTRADICTORY,
        ContributionClass.UNKNOWN
    ]
    class_to_idx = {c: i for i, c in enumerate(classes)}
    n_classes = len(classes)
    
    confusion_mat = np.zeros((n_classes, n_classes), dtype=int)
    results = []
    
    if verbose:
        print("=" * 80)
        print("   ICG v0.3 BLIND BENCHMARK EXECUTION (BLIND TEST HARNESS)")
        print("=" * 80)

    for item in BLIND_BENCHMARK_DATASET:
        doc_id = item["id"]
        text = item["text"]
        target_idx = item["target_idx"]
        expected_class = item["expected"]

        # Run blind construction without knowing expected class
        graph = builder.build_graph(doc_id, text)
        
        actual_class = ContributionClass.UNKNOWN
        if target_idx < len(graph.nodes):
            actual_class = graph.nodes[target_idx].contribution_class

        exp_i = class_to_idx[expected_class]
        act_i = class_to_idx[actual_class]
        confusion_mat[exp_i, act_i] += 1
        
        passed = (expected_class == actual_class)
        results.append({
            "id": doc_id,
            "expected": expected_class.value,
            "actual": actual_class.value,
            "passed": passed,
            "notes": item["notes"]
        })
        
        if verbose:
            status = "PASS" if passed else "FAIL"
            print(f" [{status:^4}] {doc_id:<28} | Expected: {expected_class.value:<22} | Actual: {actual_class.value:<22}")

    # Compute Statistical Metrics
    per_class_metrics = {}
    f1_list = []
    
    for c in classes:
        idx = class_to_idx[c]
        tp = confusion_mat[idx, idx]
        fp = sum(confusion_mat[:, idx]) - tp
        fn = sum(confusion_mat[idx, :]) - tp
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        
        per_class_metrics[c.value] = {
            "precision": round(float(prec), 3),
            "recall": round(float(rec), 3),
            "f1_score": round(float(f1), 3),
            "support": int(sum(confusion_mat[idx, :]))
        }
        if sum(confusion_mat[idx, :]) > 0:
            f1_list.append(f1)

    macro_f1 = round(float(np.mean(f1_list)), 3) if f1_list else 0.0
    
    # False Synthesis Rate (FSR): Non-syntheses classified as SYNTHESIS or SOURCE_NOVEL_SYNTHESIS
    synth_indices = [class_to_idx[ContributionClass.SYNTHESIS], class_to_idx[ContributionClass.SOURCE_NOVEL_SYNTHESIS]]
    non_synth_indices = [i for i in range(n_classes) if i not in synth_indices]
    
    false_syntheses = sum(confusion_mat[i, j] for i in non_synth_indices for j in synth_indices)
    total_non_syntheses = sum(sum(confusion_mat[i, :]) for i in non_synth_indices)
    fsr = round(float(false_syntheses / max(1, total_non_syntheses)), 3)

    # False Originality Rate (FOR): Non-original claims classified as ORIGINAL_CONTRIBUTION
    orig_idx = class_to_idx[ContributionClass.ORIGINAL_CONTRIBUTION]
    non_orig_indices = [i for i in range(n_classes) if i != orig_idx]
    false_origs = sum(confusion_mat[i, orig_idx] for i in non_orig_indices)
    total_non_origs = sum(sum(confusion_mat[i, :]) for i in non_orig_indices)
    for_rate = round(float(false_origs / max(1, total_non_origs)), 3)

    total_cases = len(BLIND_BENCHMARK_DATASET)
    total_passed = sum(1 for r in results if r["passed"])
    accuracy = round(total_passed / total_cases, 3)

    if verbose:
        print("\n" + "=" * 80)
        print(f"  BLIND BENCHMARK RESULTS: {total_passed}/{total_cases} PASSED ({accuracy*100:.1f}%)")
        print(f"  MACRO-F1: {macro_f1:.3f} | False Synthesis Rate (FSR): {fsr*100:.1f}% | False Originality Rate (FOR): {for_rate*100:.1f}%")
        print("=" * 80)
        print("\n  CONFUSION MATRIX (Rows: Expected, Cols: Actual):")
        short_names = [c.name[:6] for c in classes]
        print(f"  {'':<12} " + " ".join(f"{s:>7}" for s in short_names))
        for i, c in enumerate(classes):
            row_vals = " ".join(f"{confusion_mat[i, j]:>7}" for j in range(n_classes))
            print(f"  {c.name[:10]:<12} {row_vals}")
        print("=" * 80)

    return {
        "total_cases": total_cases,
        "total_passed": total_passed,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "false_synthesis_rate": fsr,
        "false_originality_rate": for_rate,
        "confusion_matrix": confusion_mat.tolist(),
        "per_class_metrics": per_class_metrics,
        "results": results
    }


if __name__ == "__main__":
    run_blind_benchmark(verbose=True)

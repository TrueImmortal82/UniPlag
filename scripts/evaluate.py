import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

TESTS_DIR = BASE / "tests"


def collect_test_cases() -> list[dict]:
    cases = []
    for subdir in sorted(TESTS_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        for f in sorted(subdir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                data["_file"] = str(f)
                cases.append(data)
            except Exception as e:
                print(f"  skip {f.name}: {e}")
    return cases


def run_evaluation():
    from app.ai_detector import detect
    from app.quality import assess as quality_assess
    from app.stylometry import semantic_density, extract_stylometric_features

    cases = collect_test_cases()
    if not cases:
        print("No test cases found in tests/")
        return

    print(f"Found {len(cases)} test cases")
    print("=" * 70)

    results = []
    for case in cases:
        case_id = case.get("id", "unknown")
        gt = case.get("ground_truth", "unknown")
        text_path = Path(case.get("_file", "")).parent / f"{case_id}.txt"
        if text_path.exists():
            text = text_path.read_text(encoding="utf-8")
        else:
            print(f"  SKIP {case_id}: no text file at {text_path}")
            continue

        print(f"\n--- {case_id} (GT: {gt}) ---")

        t0 = time.time()
        ai_result = detect(text)
        ai_time = time.time() - t0

        t0 = time.time()
        q_result = quality_assess(text)
        q_time = time.time() - t0

        sd = semantic_density(text)
        styl = extract_stylometric_features(text)

        ai_score = ai_result.get("score", 0.0)
        predicted = "ai" if ai_score >= 0.5 else "human"
        correct = predicted == gt

        print(f"  AI detector: {ai_score:.3f} (predicted: {predicted}) {'CORRECT' if correct else 'WRONG'}")
        print(f"  Method: {ai_result.get('method', 'none')}")
        print(f"  Semantic density: {sd:.3f}")
        print(f"  Quality: L={q_result.get('logic',0)} V={q_result.get('value',0)} C={q_result.get('coherence',0)}")
        print(f"  Time: AI={ai_time:.1f}s Quality={q_time:.1f}s")

        if "ensemble" in ai_result:
            ens = ai_result["ensemble"]
            print(f"  Ensemble: tfidf={ens['tfidf']:.3f} styl={ens['stylometry']:.3f} "
                  f"density={ens['density']:.3f} combined={ens['combined']:.3f} "
                  f"CI={ens['confidence_interval']} conf={ens['confidence']}")

        results.append({
            "id": case_id,
            "ground_truth": gt,
            "ai_score": ai_score,
            "predicted": predicted,
            "correct": correct,
            "method": ai_result.get("method", "none"),
            "semantic_density": sd,
            "quality": q_result,
            "ensemble": ai_result.get("ensemble", {}),
            "features": styl,
            "time_ai": ai_time,
            "time_quality": q_time,
        })

    print("\n" + "=" * 70)
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    print(f"Accuracy: {correct}/{total} ({100*correct/max(total,1):.1f}%)")

    by_gt = {}
    for r in results:
        by_gt.setdefault(r["ground_truth"], []).append(r)
    for gt, items in by_gt.items():
        c = sum(1 for i in items if i["correct"])
        print(f"  {gt}: {c}/{len(items)} ({100*c/max(len(items),1):.1f}%)")

    report_path = TESTS_DIR / "evaluation_report.json"
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport saved to {report_path}")


if __name__ == "__main__":
    run_evaluation()

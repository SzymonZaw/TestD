"""Evaluate the heuristic detector against a small, labeled JSONL sample set.

Run from the repository root:
    python scripts/evaluate_detector.py
This is a smoke-test dataset, not a representative benchmark.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import COMPILED_PATTERNS, is_educational_mention  # noqa: E402


def predicts_attack(text: str) -> bool:
    return any(
        not is_educational_mention(text, match)
        for item in COMPILED_PATTERNS
        for match in item["regex"].finditer(text)
    )


def calculate_metrics(samples: list[dict]) -> dict[str, float | int]:
    tp = fp = tn = fn = 0
    for sample in samples:
        expected = bool(sample["is_attack"])
        predicted = predicts_attack(sample["text"])
        if expected and predicted:
            tp += 1
        elif not expected and predicted:
            fp += 1
        elif not expected and not predicted:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return {
        "samples": len(samples),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
    }


def main() -> int:
    dataset_path = ROOT / "data" / "evaluation_samples.jsonl"
    with dataset_path.open(encoding="utf-8") as file:
        samples = [json.loads(line) for line in file if line.strip()]

    if not samples:
        raise ValueError("Zbiór ewaluacyjny jest pusty.")
    for sample in samples:
        if not {"id", "is_attack", "text"} <= sample.keys():
            raise ValueError(f"Nieprawidłowy rekord: {sample!r}")
        if not isinstance(sample["is_attack"], bool) or not isinstance(sample["text"], str):
            raise ValueError(f"Nieprawidłowe typy danych: {sample!r}")

    metrics = calculate_metrics(samples)
    print(f"Zbiór: {dataset_path.relative_to(ROOT)}")
    print(f"Liczba próbek: {metrics['samples']}")
    print(f"TP={metrics['tp']}  FP={metrics['fp']}  TN={metrics['tn']}  FN={metrics['fn']}")
    print(f"Precision:             {metrics['precision']:.3f}")
    print(f"Recall:                {metrics['recall']:.3f}")
    print(f"F1:                    {metrics['f1']:.3f}")
    print(f"False positive rate:   {metrics['false_positive_rate']:.3f}")

    errors = [
        sample for sample in samples
        if predicts_attack(sample["text"]) != bool(sample["is_attack"])
    ]
    if errors:
        print("\nBłędne klasyfikacje do ręcznej analizy:")
        for sample in errors:
            expected = "atak" if sample["is_attack"] else "tekst bezpieczny"
            actual = "alert" if predicts_attack(sample["text"]) else "brak alertu"
            print(f"- {sample['id']}: oczekiwano {expected}, wynik: {actual}")
    print("\nUwaga: mały, ręcznie przygotowany zbiór demonstracyjny; metryki nie opisują skuteczności produkcyjnej.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

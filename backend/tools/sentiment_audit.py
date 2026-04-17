import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from backend.app.services.sentiment import SentimentService

VALID_LABELS = {"positive", "neutral", "negative"}


def _normalize_label(value: str) -> str:
    return value.strip().lower()


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _compute_metrics(expected: list[str], predicted: list[str]) -> dict:
    per_label = {}
    supports = Counter(expected)

    for label in sorted(VALID_LABELS):
        tp = sum(1 for e, p in zip(expected, predicted) if e == label and p == label)
        fp = sum(1 for e, p in zip(expected, predicted) if e != label and p == label)
        fn = sum(1 for e, p in zip(expected, predicted) if e == label and p != label)

        precision = _safe_divide(tp, tp + fp)
        recall = _safe_divide(tp, tp + fn)
        f1 = _safe_divide(2 * precision * recall, precision + recall)

        per_label[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": supports.get(label, 0),
        }

    accuracy = _safe_divide(sum(1 for e, p in zip(expected, predicted) if e == p), len(expected))
    macro_precision = _safe_divide(sum(m["precision"] for m in per_label.values()), len(per_label))
    macro_recall = _safe_divide(sum(m["recall"] for m in per_label.values()), len(per_label))
    macro_f1 = _safe_divide(sum(m["f1"] for m in per_label.values()), len(per_label))

    confusion = {}
    for expected_label in sorted(VALID_LABELS):
        confusion[expected_label] = {}
        for predicted_label in sorted(VALID_LABELS):
            confusion[expected_label][predicted_label] = sum(
                1
                for e, p in zip(expected, predicted)
                if e == expected_label and p == predicted_label
            )

    return {
        "sample_size": len(expected),
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "per_label": per_label,
        "confusion_matrix": confusion,
    }


def run_audit(input_csv: Path) -> dict:
    analyzer = SentimentService()
    expected_labels: list[str] = []
    predicted_labels: list[str] = []

    with input_csv.open("r", encoding="utf-8", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        if "text" not in reader.fieldnames or "human_label" not in reader.fieldnames:
            raise ValueError("Input CSV must include 'text' and 'human_label' columns")

        for index, row in enumerate(reader, start=1):
            text = (row.get("text") or "").strip()
            human_label = _normalize_label(row.get("human_label") or "")

            if not text:
                raise ValueError(f"Row {index}: text is empty")
            if human_label not in VALID_LABELS:
                raise ValueError(
                    f"Row {index}: human_label '{human_label}' is invalid (use positive/neutral/negative)"
                )

            score = analyzer.score_text(text)
            expected_labels.append(human_label)
            predicted_labels.append(str(score["sentiment_label"]))

    if len(expected_labels) < 100:
        raise ValueError(
            f"Audit requires at least 100 rows; found {len(expected_labels)} rows."
        )

    return _compute_metrics(expected_labels, predicted_labels)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run manual sentiment audit and compute precision/recall.")
    parser.add_argument("--input", required=True, help="Path to CSV file with text and human_label columns")
    parser.add_argument(
        "--output",
        default="backend/audit/sentiment_audit_report.json",
        help="Path for JSON report output",
    )

    args = parser.parse_args()
    input_csv = Path(args.input)
    output_json = Path(args.output)

    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    report = run_audit(input_csv)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Sentiment audit complete")
    print(json.dumps(report, indent=2))
    print(f"Report saved to: {output_json}")


if __name__ == "__main__":
    main()

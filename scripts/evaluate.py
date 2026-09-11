"""Оценка качества модели по ручной разметке → data/model_metrics.json.

    python scripts/evaluate.py

Берёт data/manual_labels.csv (заполненные true_sentiment / true_topic) и data/comments_scored.csv,
считает accuracy и macro-F1 по тональности (и по темам, если размечены).
"""
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import COMMENTS_SCORED_PATH, MANUAL_LABELS_PATH, MODEL_METRICS_PATH  # noqa: E402


def macro_f1(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    f1s = []
    for lbl in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == lbl and p == lbl)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != lbl and p == lbl)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == lbl and p != lbl)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return sum(f1s) / len(f1s) if f1s else 0.0


def main():
    if not MANUAL_LABELS_PATH.exists():
        sys.exit(f"нет файла {MANUAL_LABELS_PATH} — сначала запустите scripts/make_labeling_template.py")
    if not COMMENTS_SCORED_PATH.exists():
        sys.exit(f"нет файла {COMMENTS_SCORED_PATH} — сначала запустите scripts/score_comments.py")

    labels = pd.read_csv(MANUAL_LABELS_PATH)
    scored = pd.read_csv(COMMENTS_SCORED_PATH)[["survey", "row_id", "col", "sentiment", "topic"]]
    df = labels.merge(scored, on=["survey", "row_id", "col"], how="inner", suffixes=("", "_model"))

    metrics = {"date": date.today().isoformat(), "n_template": int(len(labels))}

    sent = df.dropna(subset=["true_sentiment"])
    sent = sent[sent["true_sentiment"].astype(str).str.strip().isin(["pos", "neu", "neg"])]
    if len(sent) == 0:
        sys.exit("колонка true_sentiment не заполнена (ожидаются значения pos / neu / neg)")
    y_true = sent["true_sentiment"].str.strip().tolist()
    y_pred = sent["sentiment"].tolist()
    metrics["sentiment"] = {
        "n": int(len(sent)),
        "accuracy": round(sum(t == p for t, p in zip(y_true, y_pred)) / len(sent), 4),
        "macro_f1": round(macro_f1(y_true, y_pred), 4),
    }

    top = df.dropna(subset=["true_topic"])
    top = top[top["true_topic"].astype(str).str.strip() != ""]
    if len(top):
        yt = top["true_topic"].str.strip().tolist()
        yp = top["topic"].astype(str).tolist()
        metrics["topic"] = {
            "n": int(len(top)),
            "accuracy": round(sum(t == p for t, p in zip(yt, yp)) / len(top), 4),
            "macro_f1": round(macro_f1(yt, yp), 4),
        }

    MODEL_METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"записано → {MODEL_METRICS_PATH}")


if __name__ == "__main__":
    main()

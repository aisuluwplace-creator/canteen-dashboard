"""Выгрузка случайных 50 комментариев для ручной разметки → data/manual_labels.csv.

    python scripts/make_labeling_template.py [--n 50] [--seed 42]

Колонки true_sentiment (pos / neu / neg) и true_topic (ключ темы из config.TOPICS или other)
оставлены пустыми — их заполняет человек. Если есть data/comments_scored.csv, в шаблон
добавляются предсказания модели (для удобства, не для копирования!).
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from comments import collect_comments  # noqa: E402
from config import COMMENTS_SCORED_PATH, MANUAL_LABELS_PATH, SURVEYS, TOPICS  # noqa: E402
from data import load_survey_plain  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rows = []
    for cfg in SURVEYS:
        df = load_survey_plain(cfg.file_glob)
        if df.empty:
            continue
        for c in collect_comments(df, list(df.columns), cfg.comment_cols):
            rows.append({"survey": cfg.key, **c})
    all_df = pd.DataFrame(rows)
    sample = all_df.sample(n=min(args.n, len(all_df)), random_state=args.seed).reset_index(drop=True)

    if COMMENTS_SCORED_PATH.exists():
        scored = pd.read_csv(COMMENTS_SCORED_PATH)[["survey", "row_id", "col", "sentiment", "topic"]]
        scored = scored.rename(columns={"sentiment": "model_sentiment", "topic": "model_topic"})
        sample = sample.merge(scored, on=["survey", "row_id", "col"], how="left")

    sample["true_sentiment"] = ""
    sample["true_topic"] = ""
    MANUAL_LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(MANUAL_LABELS_PATH, index=False)

    print(f"записано {len(sample)} комментариев → {MANUAL_LABELS_PATH}")
    print("Заполните true_sentiment: pos / neu / neg")
    print("Заполните true_topic — ключ темы раздела:")
    for key, topics in TOPICS.items():
        print(f"  {key}: " + ", ".join(f"{k} ({lbl['ru']})" for k, lbl, _ in topics) + ", other (Прочее)")


if __name__ == "__main__":
    main()

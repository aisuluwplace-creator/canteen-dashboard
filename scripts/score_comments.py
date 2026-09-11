"""Офлайн-расчёт тональности и тем комментариев → data/comments_scored.csv.

Запускается локально (не в Streamlit), зависимости — в requirements-dev.txt:
    python scripts/score_comments.py [--limit N] [--dry-run]

Тональность:
  - русский/прочий текст — blanchefort/rubert-base-cased-sentiment;
  - казахский (по буквам ә ғ қ ң ө ұ ү һ і) — cardiffnlp/twitter-xlm-roberta-base-sentiment.
Темы: косинусная близость эмбеддингов (paraphrase-multilingual-MiniLM-L12-v2) комментария
к описаниям тем из config.TOPICS; ниже TOPIC_SIM_THRESHOLD → «Прочее».
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from comments import collect_comments, is_kazakh  # noqa: E402
from config import (COMMENTS_SCORED_PATH, EMBEDDING_MODEL, OTHER_TOPIC, SENTIMENT_MODEL_MULTI,  # noqa: E402
                    SENTIMENT_MODEL_RU, SURVEYS, TOPIC_SIM_THRESHOLD, TOPICS)
from data import load_survey_plain  # noqa: E402

LABEL_MAP = {
    "positive": "pos", "neutral": "neu", "negative": "neg",
    "POSITIVE": "pos", "NEUTRAL": "neu", "NEGATIVE": "neg",
    "LABEL_0": "neg", "LABEL_1": "neu", "LABEL_2": "pos",   # порядок классов xlm-roberta
}


def gather():
    rows = []
    for cfg in SURVEYS:
        df = load_survey_plain(cfg.file_glob)
        if df.empty:
            print(f"[{cfg.key}] файл не найден, пропускаю")
            continue
        cols = list(df.columns)
        for c in collect_comments(df, cols, cfg.comment_cols):
            rows.append({"survey": cfg.key, **c})
    return pd.DataFrame(rows)


def run_sentiment(texts, model_name, batch_size=32):
    from transformers import pipeline
    clf = pipeline("sentiment-analysis", model=model_name, truncation=True, max_length=256)
    out = []
    for i in range(0, len(texts), batch_size):
        for r in clf(texts[i:i + batch_size]):
            out.append((LABEL_MAP.get(r["label"], "neu"), float(r["score"])))
    return out


def run_topics(df):
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer(EMBEDDING_MODEL)
    topics, scores = [None] * len(df), [0.0] * len(df)
    for survey_key, idx in df.groupby("survey").groups.items():
        spec = TOPICS.get(survey_key, [])
        if not spec:
            for i in idx:
                topics[df.index.get_loc(i)] = OTHER_TOPIC
            continue
        keys = [k for k, _, _ in spec]
        topic_emb = model.encode([desc for _, _, desc in spec], convert_to_tensor=True, normalize_embeddings=True)
        texts = df.loc[idx, "text"].tolist()
        emb = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True, batch_size=64)
        sims = util.cos_sim(emb, topic_emb).cpu().numpy()
        for pos, i in enumerate(idx):
            best = sims[pos].argmax()
            loc = df.index.get_loc(i)
            scores[loc] = float(sims[pos][best])
            topics[loc] = keys[best] if sims[pos][best] >= TOPIC_SIM_THRESHOLD else OTHER_TOPIC
    df["topic"], df["topic_score"] = topics, scores
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="обработать только первые N комментариев (для проверки)")
    ap.add_argument("--dry-run", action="store_true", help="не записывать файл")
    args = ap.parse_args()

    df = gather()
    if args.limit:
        df = df.groupby("survey").head(args.limit).reset_index(drop=True)
    df["lang"] = ["kz" if is_kazakh(t) else "ru" for t in df["text"]]
    print(f"комментариев: {len(df)}; по разделам: {df['survey'].value_counts().to_dict()}; "
          f"казахских: {(df['lang'] == 'kz').sum()}")

    df["sentiment"], df["sentiment_score"] = None, 0.0
    for lang, model_name in (("ru", SENTIMENT_MODEL_RU), ("kz", SENTIMENT_MODEL_MULTI)):
        mask = df["lang"] == lang
        if not mask.any():
            continue
        print(f"тональность [{lang}] — {model_name} ({mask.sum()} текстов)…")
        res = run_sentiment(df.loc[mask, "text"].tolist(), model_name)
        df.loc[mask, "sentiment"] = [r[0] for r in res]
        df.loc[mask, "sentiment_score"] = [r[1] for r in res]

    print(f"темы — {EMBEDDING_MODEL}…")
    df = run_topics(df)

    print("\nраспределение тональности:", df["sentiment"].value_counts().to_dict())
    print("распределение тем:")
    print(df.groupby(["survey", "topic"]).size().to_string())

    if not args.dry_run:
        COMMENTS_SCORED_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(COMMENTS_SCORED_PATH, index=False)
        print(f"\nзаписано: {COMMENTS_SCORED_PATH} ({len(df)} строк)")


if __name__ == "__main__":
    main()

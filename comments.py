"""Очистка комментариев и эвристическая тональность по ключевым словам."""
import re

import pandas as pd

POSITIVE_WORDS = [
    "хорош", "отличн", "супер", "прекрасн", "устраива", "нрав", "спасибо",
    "вкусн", "удобн", "быстр", "чист", "довол", "класс", "молодц", "комфорт",
    "satisfied", "good", "great", "excellent", "жаксы", "рахмет",
]
NEGATIVE_WORDS = [
    "плохо", "ужас", "грязн", "долго", "неудобн", "жалоб", "проблем",
    "не работа", "не устраива", "недостаточ", "не хвата", "хамств", "груб",
    "опаздыва", "не приезжа", "жирн", "невкусн", "холодн", "дорог", "медленн",
    "отказ", "некомпетент", "bad", "poor", "terrible", "slow", "жаман",
]
NEGATION_WORDS = {"не", "ни", "нет", "no", "not", "жоқ", "жок"}
WORD_RE = re.compile(r"[a-zа-яёқғңөұүhі]+")
NO_COMMENT = {
    "нет", "-", ".", "..", "...", "", "нет комментариев", "без комментариев",
    "нету", "коментариев нет", "комментариев нет", "жок", "нема", "no", "net",
    "n/a", "na", "?", "нет отзывов", "все хорошо.", "-.",
}


def is_gibberish(t):
    letters = re.sub(r"[^a-zа-яёқғңөұүhі]", "", t.lower())
    if len(letters) < 6:
        return True
    return len(set(letters)) / len(letters) < 0.28


def clean_comments(series: pd.Series):
    out = []
    for raw in series.dropna():
        t = str(raw).strip()
        tl = t.lower()
        if tl in NO_COMMENT or len(t) < 4 or is_gibberish(t):
            continue
        out.append(t)
    return out


def sentiment_of(text):
    t = text.lower()
    pos = neg = 0

    # multi-word / phrase-level negative cues (already encode their own negation)
    neg += sum(1 for w in NEGATIVE_WORDS if w in t)

    # single-stem positive cues, flipped to negative when directly negated
    # ("не вкусно" must not count as positive just because it contains "вкусн")
    tokens = WORD_RE.findall(t)
    for i, tok in enumerate(tokens):
        stem = next((w for w in POSITIVE_WORDS if tok.startswith(w)), None)
        if stem is None:
            continue
        negated = i > 0 and tokens[i - 1] in NEGATION_WORDS
        if negated:
            neg += 1
        else:
            pos += 1

    if pos > neg:
        return "pos"
    if neg > pos:
        return "neg"
    return "neu"


# ============================================== нормализация и дубли --
_PUNCT_RE = re.compile(r"[^\w\s]", re.U)
_SPACES_RE = re.compile(r"\s+")


def normalize_text(t: str) -> str:
    """Нижний регистр, ё → е, без пунктуации и лишних пробелов — ключ для группировки дублей."""
    t = str(t).lower().replace("ё", "е")
    t = _PUNCT_RE.sub(" ", t)
    return _SPACES_RE.sub(" ", t).strip()


def is_kazakh(t: str) -> bool:
    from config import KAZAKH_LETTERS
    return bool(KAZAKH_LETTERS.search(str(t)))


def is_substantive(t: str) -> bool:
    from config import MIN_COMMENT_LEN
    return len(str(t).strip()) >= MIN_COMMENT_LEN


def group_short_comments(comments):
    """Одинаковые короткие ответы («Хорошо», «Всё хорошо») → [(текст, число)], по убыванию частоты.

    Текст берём самый частый из вариантов написания в группе.
    """
    groups = {}
    for c in comments:
        key = normalize_text(c)
        if not key:
            continue
        groups.setdefault(key, []).append(c.strip())
    out = []
    for key, variants in groups.items():
        # при равной частоте предпочитаем написание с заглавной буквы, с «ё» и без лишней пунктуации
        best = max(set(variants), key=lambda v: (variants.count(v), v[:1].isupper(), "ё" in v, -len(v)))
        out.append((best, len(variants)))
    out.sort(key=lambda x: (-x[1], x[0]))
    return out


def split_feed(comments):
    """Разделяет комментарии на содержательные (для ленты, длинные первыми) и короткие (для группировки)."""
    substantive = [c for c in comments if is_substantive(c)]
    short = [c for c in comments if not is_substantive(c)]
    # самые длинные и информативные первыми; среди равных — стабильный порядок по тексту
    substantive.sort(key=lambda c: (-len(normalize_text(c).split()), -len(c), c))
    return substantive, short


# =========================================== результаты офлайн-модели --
def load_scored():
    """data/comments_scored.csv → {(survey, row_id, col): {sentiment, topic, ...}} или None, если файла нет."""
    import pandas as pd
    from config import COMMENTS_SCORED_PATH
    if not COMMENTS_SCORED_PATH.exists():
        return None
    try:
        df = pd.read_csv(COMMENTS_SCORED_PATH)
    except Exception:
        return None
    need = {"survey", "row_id", "col", "sentiment", "topic"}
    if not need.issubset(df.columns):
        return None
    out = {}
    for r in df.itertuples(index=False):
        out[(r.survey, int(r.row_id), int(r.col))] = {"sentiment": r.sentiment, "topic": r.topic}
    return out


def load_model_metrics():
    import json
    from config import MODEL_METRICS_PATH
    if not MODEL_METRICS_PATH.exists():
        return None
    try:
        return json.loads(MODEL_METRICS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def collect_comments(df, cols, comment_cols, id_col=0):
    """Список dict(row_id, col, text) с очищенными комментариями из указанных колонок."""
    out = []
    for c in comment_cols:
        sub = df[[cols[id_col], cols[c]]].dropna(subset=[cols[c]])
        for row_id, raw in zip(sub.iloc[:, 0], sub.iloc[:, 1]):
            t = str(raw).strip()
            if t.lower() in NO_COMMENT or len(t) < 4 or is_gibberish(t):
                continue
            try:
                rid = int(row_id)
            except (TypeError, ValueError):
                continue
            out.append({"row_id": rid, "col": c, "text": t})
    return out


def annotate(comments, survey_key, scored):
    """Добавляет каждому комментарию sentiment и topic: из модели, если есть, иначе эвристика / «Прочее»."""
    from config import OTHER_TOPIC
    for c in comments:
        hit = scored.get((survey_key, c["row_id"], c["col"])) if scored else None
        if hit and hit.get("sentiment") in ("pos", "neu", "neg"):
            c["sentiment"] = hit["sentiment"]
            c["topic"] = hit.get("topic") or OTHER_TOPIC
            c["source"] = "model"
        else:
            c["sentiment"] = sentiment_of(c["text"])
            c["topic"] = None
            c["source"] = "heuristic"
    return comments

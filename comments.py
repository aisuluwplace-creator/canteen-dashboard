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

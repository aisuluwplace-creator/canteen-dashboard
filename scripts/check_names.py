"""Поиск комментариев, в которых могут быть имена людей — для ручной проверки анонимности.

    python scripts/check_names.py

Эвристики: слово с заглавной буквы не в начале предложения; пары вида «Имя Отчество»
(окончания -ович/-евич/-овна/-евна/-ич/-қызы/-ұлы); обращения («уважаемый …»).
Скрипт ничего не удаляет и не изменяет — только выводит список.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from comments import collect_comments  # noqa: E402
from config import SURVEYS  # noqa: E402
from data import load_survey_plain  # noqa: E402

# слова с заглавной, которые почти всегда не имена (маршруты, места, бренды, местоимения в начале)
STOP = {
    "маршрут", "автобус", "аэропорт", "алматы", "алмата", "талгар", "иссык", "алатау", "байтерек", "узунагач",
    "сейфулина", "сейфуллина", "суюнбая", "тулебаева", "водник", "сгп", "свх", "жкт", "пдд", "мрт", "кт", "узи",
    "дмс", "angar", "kargo", "aksunkar", "каргo", "ангар", "аксункар", "карго", "терминал", "шаттл", "route",
    "спасибо", "рахмет", "алла", "всё", "все", "очень", "хотелось", "просим", "прошу", "добрый", "здравствуйте",
}
PATRONYMIC_RE = re.compile(r"\b[А-ЯЁӘҒҚҢӨҰҮІ][а-яёәғқңөұүі]+\s+[А-ЯЁӘҒҚҢӨҰҮІ][а-яёәғқңөұүі]+(ович|евич|ич|овна|евна|ична|қызы|ұлы)\b")
ADDRESS_RE = re.compile(r"\b(уважаем\w+|дорог\w+|здравствуйте,?)\s+[А-ЯЁ][а-яё]+", re.I)
CAP_WORD_RE = re.compile(r"(?<![.!?\n]\s)(?<!^)\b([А-ЯЁӘҒҚҢӨҰҮІ][а-яёәғқңөұүі]{2,})\b")


def suspicious(text):
    reasons = []
    if PATRONYMIC_RE.search(text):
        reasons.append("имя-отчество")
    if ADDRESS_RE.search(text):
        reasons.append("обращение")
    caps = []
    for m in CAP_WORD_RE.finditer(text):
        word = m.group(1)
        start = m.start(1)
        prefix = text[:start].rstrip(" ")
        if not prefix or prefix[-1] in ".!?\n":   # начало предложения или новой строки
            continue
        if word.lower() in STOP:
            continue
        caps.append(word)
    if caps:
        reasons.append("заглавная не в начале: " + ", ".join(sorted(set(caps))))
    return reasons


def main():
    total = flagged = 0
    for cfg in SURVEYS:
        df = load_survey_plain(cfg.file_glob)
        if df.empty:
            continue
        for c in collect_comments(df, list(df.columns), cfg.comment_cols):
            total += 1
            reasons = suspicious(c["text"])
            if reasons:
                flagged += 1
                print(f"[{cfg.key} · ID {c['row_id']}] {'; '.join(reasons)}\n    {c['text'][:200]!r}")
    print(f"\nпроверено {total} комментариев, требуют внимания {flagged}. Ничего не удалено.")


if __name__ == "__main__":
    main()

"""Аудит интерфейса без браузера: тексты, форматирование чисел, граничные случаи фильтров.

    python scripts/check_ui.py
"""
import re
import sys
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import MONTHS  # noqa: E402

APP = str(ROOT / "streamlit_app.py")


def label_to_period(label):
    """«Январь 2026» → Period('2026-01') (виджет хранит Period, а options — подписи)."""
    name, year = label.rsplit(" ", 1)
    month = MONTHS["ru"].index(name)
    return pd.Period(f"{year}-{month:02d}", freq="M")
LATIN_WORD = re.compile(r"(?<![\w/.-])[A-Za-z]{3,}(?![\w/.-])")
DOT_DECIMAL = re.compile(r"(?<![\d.])\d+\.\d+(?![\d.])")
BIG_INT = re.compile(r"(?<![\d.,])\d{4,}(?![\d.,])")
HYPHEN_MINUS = re.compile(r"(?<![\w-])-\d")
ALLOWED_LATIN = {"RU", "EN", "Angar", "Kargo", "Aksunkar"}   # названия локаций из данных и коды языков


def texts(at):
    """Все видимые строки приложения (markdown/caption/info/warning/tabs/labels)."""
    out = []
    for kind in ("markdown", "caption", "info", "warning", "error", "success"):
        for el in getattr(at, kind):
            out.append(str(el.value))
    for t in at.tabs:
        out.append(str(t.label))
    for ms in at.multiselect:
        out.append(str(ms.label))
    for sb in at.selectbox:
        out.append(str(sb.label))
    for ex in at.expander:
        out.append(str(ex.label))
    return out


def strip_html(s):
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&\w+;", " ", s)
    return s


def audit_texts(at, lang):
    problems = []
    for raw in texts(at):
        if "quote-card" in raw or "pill-wrap" in raw:
            continue   # тексты сотрудников показываются как есть — не проверяем
        s = strip_html(raw)
        s = re.sub(r"\b\d{2}\.\d{2}\.\d{4}\b", " ", s)   # даты
        if lang == "ru":
            for w in LATIN_WORD.findall(s):
                if w not in ALLOWED_LATIN and not w.islower():
                    problems.append(f"латиница: {w!r} в {s.strip()[:90]!r}")
                elif w not in ALLOWED_LATIN:
                    problems.append(f"латиница: {w!r} в {s.strip()[:90]!r}")
            for m in DOT_DECIMAL.findall(s):
                problems.append(f"точка в дробном: {m!r} в {s.strip()[:90]!r}")
            for m in HYPHEN_MINUS.findall(s):
                problems.append(f"дефис вместо минуса: {m!r} в {s.strip()[:90]!r}")
        for m in BIG_INT.findall(s):
            if not re.fullmatch(r"(19|20)\d\d", m):   # годы допустимы
                problems.append(f"число без разделителя тысяч: {m!r} в {s.strip()[:90]!r}")
        if "nan" in s.split() or "None" in s:
            problems.append(f"nan/None в тексте: {s.strip()[:90]!r}")
    return problems


def run(lang="ru", mutate=None):
    at = AppTest.from_file(APP, default_timeout=180)
    at.session_state["lang"] = lang
    at.run()
    if mutate:
        mutate(at)
        at.run()
    return at


def report(title, at):
    errs = [str(e.value)[:300] for e in at.exception]
    print(f"--- {title}: exceptions={len(errs)} warnings={len(at.warning)} infos={len(at.info)}")
    for e in errs:
        print("   EXC:", e)
    return not errs


def main():
    ok = True
    # 1. тексты по умолчанию на трёх языках
    for lang in ("ru", "kz", "en"):
        at = run(lang)
        ok &= report(f"по умолчанию [{lang}]", at)
        probs = audit_texts(at, lang)
        seen = set()
        for p in probs:
            if p not in seen:
                seen.add(p)
                print("   ТЕКСТ:", p)
        ok &= not probs

    # 2. граничные случаи фильтров (по ключам виджетов)
    def same_period(at):
        for ms in at.multiselect:
            if ms.key and ms.key.endswith("_cmp_ru"):
                cur = next(m for m in at.multiselect if m.key == ms.key.replace("_cmp_", "_cur_"))
                ms.set_value(list(cur.value))
    ok &= report("одинаковый период в обоих фильтрах", run("ru", same_period))

    def empty_compare(at):
        for ms in at.multiselect:
            if ms.key and ms.key.endswith("_cmp_ru"):
                ms.set_value([])
    ok &= report("пустой период сравнения", run("ru", empty_compare))

    def empty_current(at):
        for ms in at.multiselect:
            if ms.key and ms.key.endswith("_cur_ru"):
                ms.set_value([])
    ok &= report("пустой текущий период", run("ru", empty_current))

    def tiny_period(at):
        for ms in at.multiselect:
            if ms.key and (ms.key.endswith("_cur_ru") or ms.key.endswith("_cmp_ru")):
                ms.set_value([label_to_period(ms.options[-1])])   # последний месяц — единичные ответы
    at = run("ru", tiny_period)
    ok &= report("период с 1–2 ответами в обоих фильтрах", at)

    from collections import Counter
    from config import SURVEYS
    from data import load_survey_plain
    rare = {}
    for cfg in SURVEYS:
        if cfg.segment is None:
            continue
        df = load_survey_plain(cfg.file_glob)
        cnt = Counter(t for tags in df.iloc[:, cfg.segment.col].apply(cfg.segment.extract) for t in tags)
        rare[f"{cfg.key}_seg"] = min(cnt, key=cnt.get)
        print(f"   самый редкий сегмент {cfg.key}: {rare[cfg.key + '_seg']!r} ({min(cnt.values())} анкет)")

    def small_segment(at):
        for ms in at.multiselect:
            if ms.key in rare:
                ms.set_value([rare[ms.key]])
    at = run("ru", small_segment)
    ok &= report("редкий сегмент (анонимность)", at)
    print("   предупреждений об анонимности:", sum("анонимности" in str(w.value) for w in at.warning))

    print("\nUI CHECK OK" if ok else "\nUI CHECK FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

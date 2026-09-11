"""Единое форматирование чисел и дат для интерфейса.

Правила: тысячи через неразрывный пробел (1 422), дробная часть через запятую
для RU/KZ и точку для EN (3,6 / 3.6), типографский минус (−), дельты со знаком (+5 п.п., −4,0%).
"""
import math

NBSP = " "
MINUS = "−"
DECIMAL_SEP = {"ru": ",", "kz": ",", "en": "."}
PP_UNIT = {"ru": "п.п.", "kz": "п.т.", "en": "pp"}   # процентные пункты / пайыздық тармақ / percentage points
DASH = "—"


def _is_missing(x):
    return x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))


def fmt_int(n, lang="ru"):
    """1422 -> '1 422' (неразрывный пробел)."""
    if _is_missing(n):
        return DASH
    n = int(round(n))
    body = f"{abs(n):,}".replace(",", NBSP)
    return (MINUS if n < 0 else "") + body


def fmt_num(x, decimals=1, lang="ru"):
    """3.61 -> '3,6'; -0.4 -> '−0,4'."""
    if _is_missing(x):
        return DASH
    x = round(float(x), decimals)
    if x == 0:
        x = 0.0  # избавляемся от '-0,0'
    int_part, _, frac_part = f"{abs(x):.{decimals}f}".partition(".")
    int_part = f"{int(int_part):,}".replace(",", NBSP)
    s = int_part + (DECIMAL_SEP.get(lang, ",") + frac_part if decimals > 0 else "")
    return (MINUS if x < 0 else "") + s


def fmt_pct(x, decimals=0, lang="ru"):
    """Доля в процентах (уже умноженная на 100): 54.3 -> '54%'."""
    if _is_missing(x):
        return DASH
    return fmt_num(x, decimals, lang) + "%"


def fmt_signed(x, decimals=1, lang="ru"):
    """Дельта со знаком: +0,3 / −0,4 / 0,0."""
    if _is_missing(x):
        return DASH
    x = round(float(x), decimals)
    s = fmt_num(x, decimals, lang)
    return ("+" + s) if x > 0 else s


def fmt_pp(x, decimals=0, lang="ru"):
    """Изменение доли в процентных пунктах: +5 п.п."""
    if _is_missing(x):
        return DASH
    return fmt_signed(x, decimals, lang) + NBSP + PP_UNIT.get(lang, "п.п.")


def fmt_rel_pct(x, decimals=1, lang="ru"):
    """Относительное изменение в процентах: −4,0%."""
    if _is_missing(x):
        return DASH
    return fmt_signed(x, decimals, lang) + "%"


def fmt_date(d, lang="ru"):
    """Дата -> 'ДД.ММ.ГГГГ'."""
    if d is None or (hasattr(d, "year") is False):
        return DASH
    try:
        return f"{d.day:02d}.{d.month:02d}.{d.year}"
    except (AttributeError, ValueError):
        return DASH


def plotly_separators(lang="ru"):
    """Строка separators для Plotly: первый символ — десятичный, второй — тысячный."""
    return DECIMAL_SEP.get(lang, ",") + NBSP

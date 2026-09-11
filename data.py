"""Загрузка данных опросов и работа с периодами и волнами."""
import glob
import re

import pandas as pd
import streamlit as st

from config import BASE_DIR, MIN_WAVE_SIZE, MONTHS
from i18n import tr


@st.cache_data
def load_survey(file_glob: str) -> pd.DataFrame:
    matches = glob.glob(str(BASE_DIR / file_glob))
    if not matches:
        return pd.DataFrame()
    df = pd.read_excel(matches[0], sheet_name=0)
    return df


def prepare(df: pd.DataFrame, date_col: int) -> pd.DataFrame:
    """Добавляет служебные колонки _dt (дата) и _period (месяц)."""
    dt = pd.to_datetime(df.iloc[:, date_col], errors="coerce")
    return df.assign(_dt=dt, _period=dt.dt.to_period("M"))


def period_options(df, date_col):
    dt = pd.to_datetime(df.iloc[:, date_col], errors="coerce")
    periods = dt.dropna().dt.to_period("M").unique()
    return sorted(periods)


def period_label(p, lang):
    return f"{MONTHS[lang][p.month]} {p.year}"


def waves(df: pd.DataFrame):
    """Месяцы, которые считаются волнами опроса (>= MIN_WAVE_SIZE анкет), по возрастанию."""
    counts = df["_period"].value_counts()
    return sorted(p for p, n in counts.items() if n >= MIN_WAVE_SIZE)


def last_wave(df: pd.DataFrame):
    w = waves(df)
    if w:
        return w[-1]
    periods = sorted(df["_period"].dropna().unique())
    return periods[-1] if periods else None


def default_periods(df: pd.DataFrame):
    """Две самые наполненные волны: более поздняя — текущая, более ранняя — сравнение."""
    counts = df["_period"].value_counts()
    periods = sorted(counts.index)
    busiest = sorted(periods, key=lambda p: counts.get(p, 0), reverse=True)[:2]
    busiest.sort()
    if len(busiest) == 2:
        return [busiest[1]], [busiest[0]]
    if busiest:
        return [busiest[0]], []
    return [], []


def data_updated_at(dfs):
    """Дата последнего ответа среди всех опросов (для шапки)."""
    dates = [df["_dt"].max() for df in dfs if not df.empty and "_dt" in df]
    dates = [d for d in dates if pd.notna(d)]
    return max(dates) if dates else None


def describe_periods(selected, lw, lang, role="current"):
    """Человекочитаемое описание выбора периодов.

    Если выбрана ровно последняя волна — «Последняя волна: Январь 2026»,
    иначе перечисление месяцев; для периода сравнения — «Сравнение: …».
    """
    if not selected:
        return tr("period_not_selected", lang)
    names = ", ".join(period_label(p, lang) for p in sorted(selected))
    if role == "current" and lw is not None and list(selected) == [lw]:
        return tr("last_wave_desc", lang, period=names)
    if role == "compare":
        return tr("compare_desc", lang, period=names)
    return names


_LANG_SPLIT = re.compile(r"\b(RU|KZ|EN)\s*:\s*", re.I)


def question_full_text(header, lang="ru"):
    """Полный текст вопроса на нужном языке из трёхъязычного заголовка колонки «RU: … KZ: … EN: …»."""
    h = re.sub(r"[\u00a0\s]+", " ", str(header)).strip()
    parts = _LANG_SPLIT.split(h)
    if len(parts) >= 3:
        found = {parts[i].lower(): parts[i + 1].strip(" ;,") for i in range(1, len(parts) - 1, 2)}
        return found.get(lang) or found.get("ru") or h
    return h

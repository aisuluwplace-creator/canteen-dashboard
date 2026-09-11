"""Загрузка данных опросов и работа с периодами."""
import glob

import pandas as pd
import streamlit as st

from config import BASE_DIR, MONTHS


@st.cache_data
def load_survey(file_glob: str) -> pd.DataFrame:
    matches = glob.glob(str(BASE_DIR / file_glob))
    if not matches:
        return pd.DataFrame()
    df = pd.read_excel(matches[0], sheet_name=0)
    return df


def period_options(df, date_col):
    dt = pd.to_datetime(df.iloc[:, date_col], errors="coerce")
    periods = dt.dropna().dt.to_period("M").unique()
    return sorted(periods)


def period_label(p, lang):
    return f"{MONTHS[lang][p.month]} {p.year}"

"""Расчёт показателей по вопросам и KPI раздела. Все числа считаются из данных."""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config import DISSATISFIED_SCORES, SATISFIED_SCORES, Question, SurveyConfig
from stats import Comparison, compare_means, compare_shares

SCORES = [1, 2, 3, 4, 5]


@dataclass
class QSummary:
    q: Question
    n: int = 0
    values: pd.Series = None            # numeric15: оценки; categorical: канонические категории
    mean: float = None                  # numeric15
    counts: dict = field(default_factory=dict)   # категория/оценка -> число ответов
    shares: dict = field(default_factory=dict)   # категория/оценка -> доля, %

    @property
    def negative_keys(self):
        """Что считаем негативным ответом: оценки 1–2 или заданные в конфиге варианты."""
        return list(DISSATISFIED_SCORES) if self.q.kind == "numeric15" else list(self.q.negative)

    @property
    def headline_keys(self):
        """Категории для «главной» доли categorical-вопроса: негативные, а если их нет — первая категория."""
        if self.q.kind != "categorical":
            return []
        return list(self.q.negative) if self.q.negative else [self.q.categories[0]]

    def share_of(self, keys):
        return sum(self.shares.get(k, 0.0) for k in keys)

    def count_of(self, keys):
        return int(sum(self.counts.get(k, 0) for k in keys))

    @property
    def negative_share(self):
        return self.share_of(self.negative_keys) if self.negative_keys else None

    @property
    def positive_share(self):
        return self.share_of(SATISFIED_SCORES) if self.q.kind == "numeric15" else None


def question_values(q: Question, df: pd.DataFrame, cols) -> pd.Series:
    col = cols[q.col]
    if q.kind == "numeric15":
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        return s[s.isin(SCORES)]
    return df[col].apply(q.normalize).dropna()


def summarize_question(q: Question, df: pd.DataFrame, cols) -> QSummary:
    vals = question_values(q, df, cols)
    keys = SCORES if q.kind == "numeric15" else q.categories
    n = len(vals)
    counts = {k: int((vals == k).sum()) for k in keys}
    shares = {k: (counts[k] / n * 100 if n else 0.0) for k in keys}
    mean = float(vals.mean()) if (q.kind == "numeric15" and n) else None
    return QSummary(q=q, n=n, values=vals, mean=mean, counts=counts, shares=shares)


def compare_question(cur: QSummary, cmp_: QSummary) -> Comparison:
    """Сравнение вопроса между периодами: средний балл (шкала) или главная доля (категории)."""
    if cur.q.kind == "numeric15":
        return compare_means(cur.values, cmp_.values)
    keys = cur.headline_keys
    return compare_shares(cur.count_of(keys), cur.n, cmp_.count_of(keys), cmp_.n)


# --------------------------------------------------------------------- KPI --
def scale_questions(cfg: SurveyConfig):
    return [q for q in cfg.questions if q.kind == "numeric15"]


def satisfaction_frame(cfg: SurveyConfig, df: pd.DataFrame, cols) -> pd.DataFrame:
    """Оценки, из которых считается удовлетворённость: по строке — респондент, по колонкам — критерии.

    Если задан satisfaction_col — одна колонка; иначе все шкалы 1–5 раздела (сводный балл).
    """
    qs = [q for q in scale_questions(cfg) if cfg.satisfaction_col is None or q.col == cfg.satisfaction_col]
    frame = pd.DataFrame({q.col: pd.to_numeric(df[cols[q.col]], errors="coerce") for q in qs}, index=df.index)
    frame = frame.where(frame.isin(SCORES))
    return frame.dropna(how="all")


@dataclass
class Satisfaction:
    n: int = 0                  # респондентов с хотя бы одной оценкой
    n_ratings: int = 0          # всего оценок
    mean: float = None          # средний балл (по всем оценкам)
    per_respondent: pd.Series = None   # средний балл каждого респондента — для теста значимости
    pos_share: float = None     # доля оценок 4–5, %
    neg_share: float = None     # доля оценок 1–2, %
    pos_count: int = 0
    neg_count: int = 0


def satisfaction(cfg: SurveyConfig, df: pd.DataFrame, cols) -> Satisfaction:
    frame = satisfaction_frame(cfg, df, cols)
    if frame.empty:
        return Satisfaction()
    stacked = frame.stack()
    n_ratings = int(len(stacked))
    pos = int(stacked.isin(SATISFIED_SCORES).sum())
    neg = int(stacked.isin(DISSATISFIED_SCORES).sum())
    return Satisfaction(
        n=int(len(frame)), n_ratings=n_ratings, mean=float(stacked.mean()),
        per_respondent=frame.mean(axis=1),
        pos_share=pos / n_ratings * 100, neg_share=neg / n_ratings * 100,
        pos_count=pos, neg_count=neg,
    )


def _respondent_share_counts(s: Satisfaction, share):
    """Для z-теста долей используем число респондентов (а не оценок) как размер выборки —
    оценки одного человека не независимы, так консервативнее."""
    if s.n == 0 or share is None:
        return 0, 0
    return round(share / 100 * s.n), s.n


def compare_satisfaction(cur: Satisfaction, cmp_: Satisfaction):
    """Три сравнения: средний балл, доля довольных, доля недовольных."""
    mean_c = compare_means(cur.per_respondent if cur.per_respondent is not None else [],
                           cmp_.per_respondent if cmp_.per_respondent is not None else [])
    if cur.mean is not None and cmp_.mean is not None:
        mean_c.delta = cur.mean - cmp_.mean   # дельта — по всем оценкам, как и само значение
    kp, npos = _respondent_share_counts(cur, cur.pos_share)
    kp2, npos2 = _respondent_share_counts(cmp_, cmp_.pos_share)
    pos_c = compare_shares(kp, npos, kp2, npos2)
    if cur.pos_share is not None and cmp_.pos_share is not None:
        pos_c.delta = cur.pos_share - cmp_.pos_share
    kn, nneg = _respondent_share_counts(cur, cur.neg_share)
    kn2, nneg2 = _respondent_share_counts(cmp_, cmp_.neg_share)
    neg_c = compare_shares(kn, nneg, kn2, nneg2)
    if cur.neg_share is not None and cmp_.neg_share is not None:
        neg_c.delta = cur.neg_share - cmp_.neg_share
    return mean_c, pos_c, neg_c


# ---------------------------------------------------------- problem metric --
def pick_problem_question(cfg: SurveyConfig, summaries_cur: dict):
    """Главная проблемная метрика: заданная в конфиге или вопрос с наибольшей долей негативных ответов."""
    if cfg.problem_col is not None:
        return next((q for q in cfg.questions if q.col == cfg.problem_col), None), False
    candidates = [(s.negative_share, q) for q, s in summaries_cur.items()
                  if s.negative_share is not None and s.n > 0]
    if not candidates:
        return None, True
    candidates.sort(key=lambda t: t[0], reverse=True)
    return candidates[0][1], True


def compare_negative_share(cur: QSummary, cmp_: QSummary) -> Comparison:
    keys = cur.negative_keys
    return compare_shares(cur.count_of(keys), cur.n, cmp_.count_of(keys), cmp_.n)


# ------------------------------------------------------------- analysis --
@dataclass
class Analysis:
    """Все расчёты по разделу для пары периодов — используются вкладкой раздела и «Обзором»."""
    n_cur: int
    n_cmp: int
    sat_cur: Satisfaction
    sat_cmp: Satisfaction
    mean_c: Comparison
    pos_c: Comparison
    neg_c: Comparison
    summ_cur: dict          # {Question: QSummary}
    summ_cmp: dict
    problem_q: Question     # может быть None
    problem_auto: bool
    problem_c: Comparison   # изменение доли негативных ответов проблемной метрики


def analyze(cfg: SurveyConfig, df_cur: pd.DataFrame, df_cmp: pd.DataFrame, cols) -> Analysis:
    sat_cur, sat_cmp = satisfaction(cfg, df_cur, cols), satisfaction(cfg, df_cmp, cols)
    mean_c, pos_c, neg_c = compare_satisfaction(sat_cur, sat_cmp)
    summ_cur = {q: summarize_question(q, df_cur, cols) for q in cfg.questions}
    summ_cmp = {q: summarize_question(q, df_cmp, cols) for q in cfg.questions}
    problem_q, auto = pick_problem_question(cfg, summ_cur)
    problem_c = compare_negative_share(summ_cur[problem_q], summ_cmp[problem_q]) if problem_q else Comparison()
    return Analysis(len(df_cur), len(df_cmp), sat_cur, sat_cmp, mean_c, pos_c, neg_c,
                    summ_cur, summ_cmp, problem_q, auto, problem_c)

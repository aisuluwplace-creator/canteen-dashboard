"""Статистическая значимость различий между периодами.

- шкалы 1–5: критерий Манна–Уитни (scipy.stats.mannwhitneyu);
- доли («Да/Нет», доля довольных и т.п.): двусторонний z-тест для двух долей.
Порог p и минимальный размер выборки — в config.py.
"""
import math
from dataclasses import dataclass

import numpy as np
from scipy import stats as sps

from config import MIN_N_FOR_TEST, SIGNIFICANCE_ALPHA

# статусы сравнения
SIGNIFICANT = "significant"     # p < порога
NOT_SIGNIFICANT = "ns"          # в пределах погрешности
LOW_N = "low_n"                 # мало данных для сравнения (n < MIN_N_FOR_TEST хотя бы в одном периоде)
NO_COMPARE = "no_compare"       # период сравнения не выбран / пуст


@dataclass
class Comparison:
    delta: float = None     # текущий − сравнение (в единицах метрики: баллы или п.п.)
    p: float = None
    status: str = NO_COMPARE

    @property
    def significant(self):
        return self.status == SIGNIFICANT


def _status(p):
    if p is None or math.isnan(p):
        return NOT_SIGNIFICANT
    return SIGNIFICANT if p < SIGNIFICANCE_ALPHA else NOT_SIGNIFICANT


def mann_whitney_p(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return None
    if np.all(a == a[0]) and np.all(b == b[0]) and a[0] == b[0]:
        return 1.0  # все значения одинаковые — различий нет
    return float(sps.mannwhitneyu(a, b, alternative="two-sided").pvalue)


def two_proportion_z_p(k1, n1, k2, n2):
    """Двусторонний z-тест для двух долей k1/n1 и k2/n2 (пул дисперсии)."""
    if n1 == 0 or n2 == 0:
        return None
    p1, p2 = k1 / n1, k2 / n2
    pooled = (k1 + k2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    return float(2 * (1 - sps.norm.cdf(abs(z))))


def compare_means(cur_values, cmp_values) -> Comparison:
    """Сравнение средних по шкале 1–5 (Манн–Уитни). delta — разница средних в баллах."""
    cur = np.asarray(cur_values, dtype=float)
    cmp_ = np.asarray(cmp_values, dtype=float)
    cur, cmp_ = cur[~np.isnan(cur)], cmp_[~np.isnan(cmp_)]
    if len(cmp_) == 0 or len(cur) == 0:
        return Comparison(status=NO_COMPARE)
    delta = float(cur.mean() - cmp_.mean())
    if len(cur) < MIN_N_FOR_TEST or len(cmp_) < MIN_N_FOR_TEST:
        return Comparison(delta=delta, status=LOW_N)
    p = mann_whitney_p(cur, cmp_)
    return Comparison(delta=delta, p=p, status=_status(p))


def compare_shares(k_cur, n_cur, k_cmp, n_cmp) -> Comparison:
    """Сравнение долей. delta — в процентных пунктах."""
    if n_cmp == 0 or n_cur == 0:
        return Comparison(status=NO_COMPARE)
    delta = (k_cur / n_cur - k_cmp / n_cmp) * 100
    if n_cur < MIN_N_FOR_TEST or n_cmp < MIN_N_FOR_TEST:
        return Comparison(delta=delta, status=LOW_N)
    p = two_proportion_z_p(k_cur, n_cur, k_cmp, n_cmp)
    return Comparison(delta=delta, p=p, status=_status(p))

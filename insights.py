"""Блок «Ключевые выводы»: детерминированные правила поверх рассчитанных метрик.

Никакого LLM — текст одинаков от запуска к запуску. Пороги — в config.py.
Порядок: сначала негативные сигналы, потом поляризация, потом улучшения.
"""
from dataclasses import dataclass

from config import INSIGHTS_MAX, NEGATIVE_SHARE_ALERT, POLARIZATION_PP, cat_label
from formatting import fmt_num, fmt_pct, fmt_pp
from i18n import L
from metrics import compare_negative_share, compare_question
from stats import LOW_N, NO_COMPARE, Comparison

SEV_NEGATIVE, SEV_ALERT, SEV_POLAR, SEV_POSITIVE, SEV_NEUTRAL = 0, 1, 2, 3, 4

TXT = {
    "sig": {"ru": "значимое изменение", "kz": "маңызды өзгеріс", "en": "significant change"},
    "mean_up": {"ru": "Средний балл удовлетворённости вырос с {a} до {b} ({sig})",
                "kz": "Қанағаттанудың орташа балы {a}-дан {b}-ге өсті ({sig})",
                "en": "Average satisfaction score rose from {a} to {b} ({sig})"},
    "mean_down": {"ru": "Средний балл удовлетворённости снизился с {a} до {b} ({sig})",
                  "kz": "Қанағаттанудың орташа балы {a}-дан {b}-ге төмендеді ({sig})",
                  "en": "Average satisfaction score fell from {a} to {b} ({sig})"},
    "pos_up": {"ru": "Доля довольных (оценки 4–5) выросла с {a} до {b} ({sig})",
               "kz": "Қанағаттанғандар үлесі (4–5 баға) {a}-дан {b}-ге өсті ({sig})",
               "en": "Share of satisfied (scores 4–5) rose from {a} to {b} ({sig})"},
    "pos_down": {"ru": "Доля довольных (оценки 4–5) снизилась с {a} до {b} ({sig})",
                 "kz": "Қанағаттанғандар үлесі (4–5 баға) {a}-дан {b}-ге төмендеді ({sig})",
                 "en": "Share of satisfied (scores 4–5) fell from {a} to {b} ({sig})"},
    "neg_up": {"ru": "Доля недовольных (оценки 1–2) выросла с {a} до {b} ({sig})",
               "kz": "Қанағаттанбағандар үлесі (1–2 баға) {a}-дан {b}-ге өсті ({sig})",
               "en": "Share of dissatisfied (scores 1–2) rose from {a} to {b} ({sig})"},
    "neg_down": {"ru": "Доля недовольных (оценки 1–2) снизилась с {a} до {b} ({sig})",
                 "kz": "Қанағаттанбағандар үлесі (1–2 баға) {a}-дан {b}-ге төмендеді ({sig})",
                 "en": "Share of dissatisfied (scores 1–2) fell from {a} to {b} ({sig})"},
    "q_mean_up": {"ru": "«{q}»: средний балл вырос с {a} до {b} ({sig})",
                  "kz": "«{q}»: орташа балл {a}-дан {b}-ге өсті ({sig})",
                  "en": "“{q}”: average score rose from {a} to {b} ({sig})"},
    "q_mean_down": {"ru": "«{q}»: средний балл снизился с {a} до {b} ({sig})",
                    "kz": "«{q}»: орташа балл {a}-дан {b}-ге төмендеді ({sig})",
                    "en": "“{q}”: average score fell from {a} to {b} ({sig})"},
    "q_share_up": {"ru": "«{q}»: доля ответов «{c}» выросла с {a} до {b} ({sig})",
                   "kz": "«{q}»: «{c}» жауабының үлесі {a}-дан {b}-ге өсті ({sig})",
                   "en": "“{q}”: share of “{c}” answers rose from {a} to {b} ({sig})"},
    "q_share_down": {"ru": "«{q}»: доля ответов «{c}» снизилась с {a} до {b} ({sig})",
                     "kz": "«{q}»: «{c}» жауабының үлесі {a}-дан {b}-ге төмендеді ({sig})",
                     "en": "“{q}”: share of “{c}” answers fell from {a} to {b} ({sig})"},
    "alert_scale": {"ru": "«{q}»: {a} оценок — низкие (1–2)",
                    "kz": "«{q}»: бағалардың {a} — төмен (1–2)",
                    "en": "“{q}”: {a} of scores are low (1–2)"},
    "alert_cat": {"ru": "«{q}»: {a} ответили «{c}»",
                  "kz": "«{q}»: {a} «{c}» деп жауап берді",
                  "en": "“{q}”: {a} answered “{c}”"},
    "polar": {"ru": "«{q}»: мнения расходятся — доля оценок «5» изменилась на {d5}, доля оценок «1» — на {d1}",
              "kz": "«{q}»: пікірлер бөлінеді — «5» бағасының үлесі {d5}, «1» бағасының үлесі {d1} өзгерді",
              "en": "“{q}”: opinions are polarising — share of “5” changed by {d5}, share of “1” by {d1}"},
    "no_change": {"ru": "Существенных изменений по сравнению с периодом «{p}» нет",
                  "kz": "«{p}» кезеңімен салыстырғанда елеулі өзгерістер жоқ",
                  "en": "No significant changes compared with “{p}”"},
    "no_compare": {"ru": "Период сравнения не выбран — динамика не рассчитывается",
                   "kz": "Салыстыру кезеңі таңдалмаған — динамика есептелмейді",
                   "en": "No comparison period selected — no change is calculated"},
    "low_n": {"ru": "В одном из периодов слишком мало ответов — сравнение между периодами не проводилось",
              "kz": "Кезеңдердің бірінде жауап тым аз — кезеңдерді салыстыру жүргізілмеді",
              "en": "Too few answers in one of the periods — periods were not compared"},
    "or": {"ru": " или ", "kz": " немесе ", "en": " or "},
}


@dataclass
class Insight:
    severity: int
    weight: float       # для сортировки внутри группы (модуль эффекта)
    text: str


def _t(key, lang, **kw):
    return TXT[key][lang].format(**kw)


def _cats(keys, lang):
    return TXT["or"][lang].join(cat_label(k, lang) for k in keys)


def generate_insights(cfg, lang, sat_cur, sat_cmp, sat_cmps, summ_cur, summ_cmp, problem_q, cmp_period_name):
    """Возвращает список Insight (уже отсортированный и обрезанный до INSIGHTS_MAX).

    sat_cur/sat_cmp — metrics.Satisfaction; sat_cmps — (mean_c, pos_c, neg_c) из compare_satisfaction;
    summ_cur/summ_cmp — {Question: QSummary}; problem_q — Question главной проблемной метрики.
    """
    out = []
    covered = set()          # вопросы, по которым уже есть вывод о значимом изменении
    OVERALL_BONUS = 1000     # выводы по общей удовлетворённости идут первыми в своей группе
    sig = _t("sig", lang)
    mean_c, pos_c, neg_c = sat_cmps
    has_compare = mean_c.status != NO_COMPARE
    low_n = mean_c.status == LOW_N

    # 1. Средний балл, доли довольных/недовольных
    if mean_c.significant:
        key = "mean_up" if mean_c.delta > 0 else "mean_down"
        out.append(Insight(SEV_POSITIVE if mean_c.delta > 0 else SEV_NEGATIVE, OVERALL_BONUS + abs(mean_c.delta) * 10,
                           _t(key, lang, a=fmt_num(sat_cmp.mean, 1, lang), b=fmt_num(sat_cur.mean, 1, lang), sig=sig)))
    if pos_c.significant:
        key = "pos_up" if pos_c.delta > 0 else "pos_down"
        out.append(Insight(SEV_POSITIVE if pos_c.delta > 0 else SEV_NEGATIVE, OVERALL_BONUS + abs(pos_c.delta),
                           _t(key, lang, a=fmt_pct(sat_cmp.pos_share, 0, lang), b=fmt_pct(sat_cur.pos_share, 0, lang), sig=sig)))
    if neg_c.significant:
        key = "neg_up" if neg_c.delta > 0 else "neg_down"
        out.append(Insight(SEV_NEGATIVE if neg_c.delta > 0 else SEV_POSITIVE, OVERALL_BONUS + abs(neg_c.delta),
                           _t(key, lang, a=fmt_pct(sat_cmp.neg_share, 0, lang), b=fmt_pct(sat_cur.neg_share, 0, lang), sig=sig)))

    any_significant = any(c.significant for c in sat_cmps)

    # 2. Значимые изменения по отдельным вопросам
    for q, sc in summ_cur.items():
        if sc.n == 0:
            continue
        if cfg.satisfaction_col is not None and q.col == cfg.satisfaction_col:
            continue  # уже покрыто средним баллом
        sm = summ_cmp.get(q)
        if sm is None or sm.n == 0:
            continue
        qname = L(q.label, lang)
        if q.kind == "numeric15":
            c = compare_question(sc, sm)
            if c.significant:
                any_significant = True
                covered.add(q)
                key = "q_mean_up" if c.delta > 0 else "q_mean_down"
                out.append(Insight(SEV_POSITIVE if c.delta > 0 else SEV_NEGATIVE, abs(c.delta) * 10,
                                   _t(key, lang, q=qname, a=fmt_num(sm.mean, 1, lang), b=fmt_num(sc.mean, 1, lang), sig=sig)))
        else:
            keys = sc.headline_keys
            c = compare_question(sc, sm)
            if c.significant:
                any_significant = True
                covered.add(q)
                is_negative_cat = bool(q.negative)
                bad = (c.delta > 0) if is_negative_cat else False
                sev = SEV_NEGATIVE if bad else (SEV_POSITIVE if is_negative_cat else SEV_NEUTRAL)
                key = "q_share_up" if c.delta > 0 else "q_share_down"
                out.append(Insight(sev, abs(c.delta),
                                   _t(key, lang, q=qname, c=_cats(keys, lang),
                                      a=fmt_pct(sm.share_of(keys), 0, lang), b=fmt_pct(sc.share_of(keys), 0, lang), sig=sig)))

    # 3. Высокая доля негативных ответов (только текущий период)
    for q, sc in summ_cur.items():
        if sc.n == 0 or sc.negative_share is None or sc.negative_share <= NEGATIVE_SHARE_ALERT or q in covered:
            continue  # если по вопросу уже есть вывод с обеими долями — не дублируем
        qname = L(q.label, lang)
        if q.kind == "numeric15":
            text = _t("alert_scale", lang, q=qname, a=fmt_pct(sc.negative_share, 0, lang))
        else:
            text = _t("alert_cat", lang, q=qname, a=fmt_pct(sc.negative_share, 0, lang), c=_cats(q.negative, lang))
        out.append(Insight(SEV_ALERT, sc.negative_share, text))

    # 4. Поляризация: одновременный рост долей «5» и «1»
    if has_compare and not low_n:
        for q, sc in summ_cur.items():
            sm = summ_cmp.get(q)
            if q.kind != "numeric15" or sc.n == 0 or sm is None or sm.n == 0:
                continue
            d5 = sc.shares[5] - sm.shares[5]
            d1 = sc.shares[1] - sm.shares[1]
            if d5 > POLARIZATION_PP and d1 > POLARIZATION_PP:
                out.append(Insight(SEV_POLAR, d5 + d1,
                                   _t("polar", lang, q=L(q.label, lang), d5=fmt_pp(d5, 0, lang), d1=fmt_pp(d1, 0, lang))))

    # 5. Итог по динамике, если значимых изменений нет
    if not has_compare:
        out.append(Insight(SEV_NEUTRAL, 0, _t("no_compare", lang)))
    elif low_n:
        out.append(Insight(SEV_NEUTRAL, 0, _t("low_n", lang)))
    elif not any_significant:
        out.append(Insight(SEV_NEUTRAL, 0, _t("no_change", lang, p=cmp_period_name)))

    out.sort(key=lambda i: (i.severity, -i.weight))
    # нейтральный итог показываем всегда, остальное режем до лимита
    neutral = [i for i in out if i.severity == SEV_NEUTRAL]
    rest = [i for i in out if i.severity != SEV_NEUTRAL][:max(INSIGHTS_MAX - len(neutral), 1)]
    return rest + neutral

import pandas as pd
import streamlit as st

from charts import render_grouped_bar, render_trend_bar
from comments import clean_comments, sentiment_of
from components import hero, inject_css, kpi_row, legend_pills, section_head
from config import COMPARE_COLOR, CURRENT_COLOR, MUTED, PLOTLY_CFG, SURVEYS, SurveyConfig, cat_label
from data import (data_updated_at, default_periods, describe_periods, last_wave, load_survey, period_label,
                  period_options, prepare)
from formatting import DASH, fmt_date, fmt_int, fmt_rel_pct
from i18n import LANGS, L, tr

st.set_page_config(page_title="Опросы удовлетворённости", page_icon="📊", layout="wide")
inject_css()


def render_survey(cfg: SurveyConfig, lang: str):
    df = load_survey(cfg.file_glob)
    if df.empty:
        st.warning(tr("warn_no_file", lang, title=L(cfg.title, lang)))
        return
    cols = list(df.columns)
    df = prepare(df, cfg.date_col)

    periods = period_options(df, cfg.date_col)
    if not periods:
        st.warning(tr("warn_no_dates", lang))
        return

    lw = last_wave(df)
    default_current, default_compare = default_periods(df)
    fmt = lambda p: period_label(p, lang)  # noqa: E731

    filt_cols = st.columns([1.3, 1.3, 1.4] if cfg.segment else [1.5, 1.5])
    with filt_cols[0]:
        cur_sel = st.multiselect(tr("filter_current_period", lang), periods, default=default_current,
                                  format_func=fmt, key=f"{cfg.key}_cur_{lang}", placeholder=tr("filter_period_placeholder", lang))
    with filt_cols[1]:
        cmp_sel = st.multiselect(tr("filter_compare_period", lang), periods, default=default_compare,
                                  format_func=fmt, key=f"{cfg.key}_cmp_{lang}", placeholder=tr("filter_period_placeholder", lang))

    seg_selected = None
    if cfg.segment:
        raw_tags = df[cols[cfg.segment.col]].apply(cfg.segment.extract)
        all_tags = sorted({t for tags in raw_tags for t in tags})
        with filt_cols[2]:
            seg_selected = st.multiselect(L(cfg.segment.label, lang), all_tags, default=[], key=f"{cfg.key}_seg",
                                           placeholder=tr("filter_segment_placeholder", lang))
        if seg_selected:
            mask = raw_tags.apply(lambda tags: any(t in seg_selected for t in tags))
            df = df[mask]

    cur_periods, cmp_periods = set(cur_sel), set(cmp_sel)
    df_cur = df[df["_period"].isin(cur_periods)]
    df_cmp = df[df["_period"].isin(cmp_periods)]

    # описания периодов для подписей: «Последняя волна: Январь 2026» / «Сравнение: Ноябрь 2025»
    cur_desc = describe_periods(cur_sel, lw, lang, role="current")
    cmp_desc = describe_periods(cmp_sel, lw, lang, role="compare")
    cur_short = ", ".join(fmt(p) for p in sorted(cur_sel)) or tr("period_not_selected", lang)
    cmp_short = ", ".join(fmt(p) for p in sorted(cmp_sel)) or tr("period_not_selected", lang)

    n_total, n_cur, n_cmp = len(df), len(df_cur), len(df_cmp)
    delta_pct = (n_cur - n_cmp) / n_cmp * 100 if n_cmp else None

    kpi_row([
        (tr("kpi_total", lang), fmt_int(n_total, lang), "", "", tr("kpi_total_foot", lang)),
        (tr("kpi_current", lang), fmt_int(n_cur, lang), "", "", cur_desc),
        (tr("kpi_compare", lang), fmt_int(n_cmp, lang), "", "compare", cmp_desc),
        # изменение числа анкет — нейтральная карточка, знак не окрашиваем
        (tr("kpi_delta", lang), fmt_rel_pct(delta_pct, 1, lang) if delta_pct is not None else DASH, "", "neutral",
         tr("kpi_delta_foot", lang)),
    ])

    legend_pills([(CURRENT_COLOR, cur_desc), (COMPARE_COLOR, cmp_desc)])

    st.write("")
    section_head(tr("sec_trend_title", lang), tr("sec_trend_note", lang))
    monthly = df.groupby("_period").size().reindex(periods, fill_value=0)
    bar_colors = [CURRENT_COLOR if p in cur_periods else (COMPARE_COLOR if p in cmp_periods else MUTED) for p in periods]
    fig = render_trend_bar([fmt(p) for p in periods], monthly.values, bar_colors, tr("trend_hover_suffix", lang), lang)
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)

    st.write("")
    section_head(tr("sec_questions_title", lang), tr("sec_questions_note", lang, cur=cur_short, cmp=cmp_short))
    q_cols = st.columns(2)
    for i, q in enumerate(cfg.questions):
        col_name = cols[q.col]
        with q_cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{L(q.label, lang)}**")
                if q.kind == "numeric15":
                    cur_s = pd.to_numeric(df_cur[col_name], errors="coerce").dropna()
                    cmp_s = pd.to_numeric(df_cmp[col_name], errors="coerce").dropna()
                    cats = ["1", "2", "3", "4", "5"]
                    cur_vals = [(cur_s == k).sum() / len(cur_s) * 100 if len(cur_s) else 0 for k in range(1, 6)]
                    cmp_vals = [(cmp_s == k).sum() / len(cmp_s) * 100 if len(cmp_s) else 0 for k in range(1, 6)]
                    fig = render_grouped_bar(cats, cur_vals, cmp_vals, cur_short, cmp_short, lang, tr("axis_score", lang))
                    cur_n, cmp_n = len(cur_s), len(cmp_s)
                else:
                    cur_norm = df_cur[col_name].apply(q.normalize).dropna()
                    cmp_norm = df_cmp[col_name].apply(q.normalize).dropna()
                    cat_disp = [cat_label(c, lang) for c in q.categories]
                    cur_vals = [(cur_norm == c).sum() / len(cur_norm) * 100 if len(cur_norm) else 0 for c in q.categories]
                    cmp_vals = [(cmp_norm == c).sum() / len(cmp_norm) * 100 if len(cmp_norm) else 0 for c in q.categories]
                    fig = render_grouped_bar(cat_disp, cur_vals, cmp_vals, cur_short, cmp_short, lang)
                    cur_n, cmp_n = len(cur_norm), len(cmp_norm)
                st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)
                st.caption(tr("answered_caption", lang, cur=fmt_int(cur_n, lang), cur_p=cur_short,
                              cmp=fmt_int(cmp_n, lang), cmp_p=cmp_short))

    st.write("")
    section_head(tr("sec_comments_title", lang), tr("sec_comments_note", lang))
    st.markdown(f'<div class="lang-note">{tr("comments_language_note", lang)}</div>', unsafe_allow_html=True)
    all_comments_cur = []
    for c in cfg.comment_cols:
        all_comments_cur += clean_comments(df_cur[cols[c]])
    all_comments_cmp = []
    for c in cfg.comment_cols:
        all_comments_cmp += clean_comments(df_cmp[cols[c]])

    SENT_ORDER = ["pos", "neu", "neg"]   # Позитивные · Нейтральные · Негативные — везде в этом порядке
    sent_names = {k: tr(f"sent_{k}", lang) for k in SENT_ORDER}

    def sentiment_shares(comments):
        if not comments:
            return {k: 0 for k in SENT_ORDER}
        tags = [sentiment_of(c) for c in comments]
        n = len(tags)
        return {k: tags.count(k) / n * 100 for k in SENT_ORDER}

    cur_sent = sentiment_shares(all_comments_cur)
    cmp_sent = sentiment_shares(all_comments_cmp)

    col_s1, col_s2 = st.columns([1, 1.4])
    with col_s1:
        with st.container(border=True):
            st.markdown(f"**{tr('sentiment_title', lang)}**")
            st.caption(tr("sentiment_caption", lang, cur=fmt_int(len(all_comments_cur), lang), cur_p=cur_short,
                          cmp=fmt_int(len(all_comments_cmp), lang), cmp_p=cmp_short))
            fig = render_grouped_bar(
                [sent_names[k] for k in SENT_ORDER],
                [cur_sent[k] for k in SENT_ORDER], [cmp_sent[k] for k in SENT_ORDER],
                cur_short, cmp_short, lang,
            )
            st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)

    with col_s2:
        st.markdown(f"**{tr('comments_current_title', lang, period=cur_short)}**")
        buckets = {k: [] for k in SENT_ORDER}
        for c in all_comments_cur:
            buckets[sentiment_of(c)].append(c)
        tabs = st.tabs([f"{sent_names[k]} ({fmt_int(len(buckets[k]), lang)})" for k in SENT_ORDER])
        for tab, key in zip(tabs, SENT_ORDER):
            with tab:
                sample = buckets[key][:8]
                if not sample:
                    st.caption(tr("no_comments", lang))
                for q in sample:
                    st.markdown(f'<div class="quote-card {key if key != "neu" else ""}">{q}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ language --
if "lang" not in st.session_state:
    st.session_state["lang"] = "ru"

lang_col = st.columns([5, 2])[1]
with lang_col:
    st.radio(
        "Язык", [code for code, _ in LANGS], index=[c for c, _ in LANGS].index(st.session_state["lang"]),
        format_func=lambda c: dict(LANGS)[c], horizontal=True, label_visibility="collapsed", key="lang",
    )

LANG = st.session_state["lang"]

# ------------------------------------------------------------------ hero --
_loaded = [prepare(load_survey(s.file_glob), s.date_col) for s in SURVEYS if not load_survey(s.file_glob).empty]
_updated = data_updated_at(_loaded)
_last_waves = [last_wave(d) for d in _loaded if last_wave(d) is not None]
hero(LANG,
     fmt_date(_updated, LANG) if _updated is not None else DASH,
     period_label(max(_last_waves), LANG) if _last_waves else DASH)

tabs = st.tabs([f"{s.icon} {L(s.title, LANG)}" for s in SURVEYS])
for tab, cfg in zip(tabs, SURVEYS):
    with tab:
        render_survey(cfg, LANG)

st.divider()
st.markdown(f'<div class="foot-note">{tr("footer_note", LANG)}</div>', unsafe_allow_html=True)

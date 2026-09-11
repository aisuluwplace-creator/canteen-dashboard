import streamlit as st
import pandas as pd

from charts import render_grouped_bar, render_trend_bar
from comments import clean_comments, sentiment_of
from components import hero, inject_css, kpi_row, section_head
from config import COMPARE_COLOR, CURRENT_COLOR, MUTED, PLOTLY_CFG, SURVEYS, SurveyConfig, cat_label
from data import load_survey, period_label, period_options
from i18n import LANGS, L, tr

st.set_page_config(page_title="Опросы удовлетворённости", page_icon="📊", layout="wide")
inject_css()


def render_survey(cfg: SurveyConfig, lang: str):
    df = load_survey(cfg.file_glob)
    if df.empty:
        st.warning(tr("warn_no_file", lang, title=L(cfg.title, lang)))
        return
    cols = list(df.columns)
    dt = pd.to_datetime(df[cols[cfg.date_col]], errors="coerce")
    df = df.assign(_dt=dt, _period=dt.dt.to_period("M"))

    periods = period_options(df, cfg.date_col)
    if not periods:
        st.warning(tr("warn_no_dates", lang))
        return

    # default to the two best-populated waves (not just the newest calendar month,
    # which may be a near-empty tail), later one = current, earlier one = compare
    counts = df["_period"].value_counts()
    busiest = sorted(periods, key=lambda p: counts.get(p, 0), reverse=True)[:2]
    busiest.sort()
    if len(busiest) == 2:
        default_compare, default_current = [busiest[0]], [busiest[1]]
    elif busiest:
        default_current, default_compare = [busiest[0]], []
    else:
        default_current, default_compare = [], []

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
            df = df.assign(_dt=df["_dt"], _period=df["_period"])

    cur_periods = set(cur_sel)
    cmp_periods = set(cmp_sel)
    df_cur = df[df["_period"].isin(cur_periods)]
    df_cmp = df[df["_period"].isin(cmp_periods)]

    n_total, n_cur, n_cmp = len(df), len(df_cur), len(df_cmp)
    delta_pct = round((n_cur - n_cmp) / n_cmp * 100, 1) if n_cmp else None

    kpi_row([
        (tr("kpi_total", lang), n_total, "", "", tr("kpi_total_foot", lang)),
        (tr("kpi_current", lang), n_cur, "", "", ", ".join(fmt(p) for p in cur_sel) or tr("period_not_selected", lang)),
        (tr("kpi_compare", lang), n_cmp, "", "compare", ", ".join(fmt(p) for p in cmp_sel) or tr("period_not_selected", lang)),
        (tr("kpi_delta", lang), (f"{'+' if delta_pct and delta_pct > 0 else ''}{delta_pct}" if delta_pct is not None else "—"),
         "%" if delta_pct is not None else "", "good" if (delta_pct or 0) >= 0 else "flag", tr("kpi_delta_foot", lang)),
    ])

    st.markdown(
        f'<span class="legend-pill"><span class="sw" style="background:{CURRENT_COLOR}"></span>{tr("legend_current", lang)}</span>'
        f'<span class="legend-pill"><span class="sw" style="background:{COMPARE_COLOR}"></span>{tr("legend_compare", lang)}</span>',
        unsafe_allow_html=True,
    )

    st.write("")
    section_head(tr("sec_trend_title", lang), tr("sec_trend_note", lang))
    monthly = df.groupby("_period").size().reindex(periods, fill_value=0)
    bar_colors = [CURRENT_COLOR if p in cur_periods else (COMPARE_COLOR if p in cmp_periods else MUTED) for p in periods]
    hover_suffix = tr("trend_hover_suffix", lang)
    fig = render_trend_bar([fmt(p) for p in periods], monthly.values, bar_colors, hover_suffix)
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)

    st.write("")
    section_head(tr("sec_questions_title", lang), tr("sec_questions_note", lang))
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
                    cur_vals = [round((cur_s == k).sum() / len(cur_s) * 100, 1) if len(cur_s) else 0 for k in range(1, 6)]
                    cmp_vals = [round((cmp_s == k).sum() / len(cmp_s) * 100, 1) if len(cmp_s) else 0 for k in range(1, 6)]
                    fig = render_grouped_bar(cats, cur_vals, cmp_vals, tr("chart_series_current", lang),
                                              tr("chart_series_compare", lang), tr("axis_score", lang))
                    cur_n, cmp_n = len(cur_s), len(cmp_s)
                else:
                    cur_norm = df_cur[col_name].apply(q.normalize).dropna()
                    cmp_norm = df_cmp[col_name].apply(q.normalize).dropna()
                    cat_disp = [cat_label(c, lang) for c in q.categories]
                    cur_vals = [round((cur_norm == c).sum() / len(cur_norm) * 100, 1) if len(cur_norm) else 0 for c in q.categories]
                    cmp_vals = [round((cmp_norm == c).sum() / len(cmp_norm) * 100, 1) if len(cmp_norm) else 0 for c in q.categories]
                    fig = render_grouped_bar(cat_disp, cur_vals, cmp_vals, tr("chart_series_current", lang),
                                              tr("chart_series_compare", lang))
                    cur_n, cmp_n = len(cur_norm), len(cmp_norm)
                st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)
                st.caption(tr("answered_caption", lang, cur=cur_n, cmp=cmp_n))

    st.write("")
    section_head(tr("sec_comments_title", lang), tr("sec_comments_note", lang))
    st.markdown(f'<div class="lang-note">{tr("comments_language_note", lang)}</div>', unsafe_allow_html=True)
    all_comments_cur = []
    for c in cfg.comment_cols:
        all_comments_cur += clean_comments(df_cur[cols[c]])
    all_comments_cmp = []
    for c in cfg.comment_cols:
        all_comments_cmp += clean_comments(df_cmp[cols[c]])

    def sentiment_shares(comments):
        if not comments:
            return {"pos": 0, "neu": 0, "neg": 0}
        tags = [sentiment_of(c) for c in comments]
        n = len(tags)
        return {k: round(tags.count(k) / n * 100, 1) for k in ["pos", "neu", "neg"]}

    cur_sent = sentiment_shares(all_comments_cur)
    cmp_sent = sentiment_shares(all_comments_cmp)

    col_s1, col_s2 = st.columns([1, 1.4])
    with col_s1:
        with st.container(border=True):
            st.markdown(f"**{tr('sentiment_title', lang)}**")
            st.caption(tr("sentiment_caption", lang, cur=len(all_comments_cur), cmp=len(all_comments_cmp)))
            fig = render_grouped_bar(
                [tr("sent_pos", lang), tr("sent_neu", lang), tr("sent_neg", lang)],
                [cur_sent["pos"], cur_sent["neu"], cur_sent["neg"]],
                [cmp_sent["pos"], cmp_sent["neu"], cmp_sent["neg"]],
                tr("chart_series_current", lang), tr("chart_series_compare", lang),
            )
            st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)

    with col_s2:
        st.markdown(f"**{tr('comments_current_title', lang)}**")
        buckets = {"pos": [], "neg": [], "neu": []}
        for c in all_comments_cur:
            buckets[sentiment_of(c)].append(c)
        tabs = st.tabs([
            f"{tr('tab_positive', lang)} ({len(buckets['pos'])})",
            f"{tr('tab_negative', lang)} ({len(buckets['neg'])})",
            f"{tr('tab_neutral', lang)} ({len(buckets['neu'])})",
        ])
        for tab, key, cls in zip(tabs, ["pos", "neg", "neu"], ["pos", "neg", ""]):
            with tab:
                sample = buckets[key][:8]
                if not sample:
                    st.caption(tr("no_comments", lang))
                for q in sample:
                    st.markdown(f'<div class="quote-card {cls}">{q}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ language --
if "lang" not in st.session_state:
    st.session_state["lang"] = "ru"

lang_col = st.columns([5, 2])[1]
with lang_col:
    st.radio(
        "Language", [code for code, _ in LANGS], index=[c for c, _ in LANGS].index(st.session_state["lang"]),
        format_func=lambda c: dict(LANGS)[c], horizontal=True, label_visibility="collapsed", key="lang",
    )

LANG = st.session_state["lang"]

hero(LANG)

tabs = st.tabs([f"{s.icon} {L(s.title, LANG)}" for s in SURVEYS])
for tab, cfg in zip(tabs, SURVEYS):
    with tab:
        render_survey(cfg, LANG)

st.divider()
st.markdown(f'<div class="foot-note">{tr("footer_note", LANG)}</div>', unsafe_allow_html=True)

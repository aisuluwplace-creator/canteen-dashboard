import pandas as pd
import streamlit as st

from charts import render_grouped_bar, render_scale_stacked, render_topics_bar, render_trend_bar
from comments import annotate, collect_comments, group_short_comments, load_model_metrics, load_scored, split_feed
from components import (counts_line, delta_html, delta_line, hero, inject_css, insights_block, kpi_row,
                        legend_pills, overview_cards, scale_note, section_head, short_answer_pills, with_no_change,
                        yes_no_card)
from config import (ANONYMITY_MIN_GROUP, COMPARE_COLOR, CURRENT_COLOR, MAX_FEED_COMMENTS, MIN_COMMENT_LEN, MUTED,
                    OTHER_TOPIC, PLOTLY_CFG, SCALE_LABELS, SIGNIFICANCE_ALPHA, SURVEYS, TOPICS, SurveyConfig,
                    cat_label, topic_label)
from data import (data_updated_at, default_periods, describe_periods, last_wave, load_survey, period_label,
                  period_options, prepare, question_full_text, waves)
from formatting import DASH, fmt_date, fmt_int, fmt_num, fmt_pct, fmt_pp, fmt_signed
from i18n import LANGS, L, tr
from insights import generate_insights
from metrics import analyze, compare_question
from stats import SIGNIFICANT

st.set_page_config(page_title="Опросы удовлетворённости", page_icon="📊", layout="wide")
inject_css()


def load_prepared(cfg: SurveyConfig):
    df = load_survey(cfg.file_glob)
    if df.empty:
        return df
    return prepare(df, cfg.date_col)


def cats_text(keys, lang):
    return tr("or_sep", lang).join(cat_label(k, lang) for k in keys) if len(keys) > 1 else cat_label(keys[0], lang)


def problem_card_parts(an, lang):
    """Значение и подпись карточки главной проблемной метрики."""
    q = an.problem_q
    if q is None:
        return None
    sc = an.summ_cur[q]
    if q.kind == "numeric15":
        foot = tr("kpi_problem_foot_scale", lang)
    else:
        foot = tr("kpi_problem_foot_cat", lang, c=cats_text(q.negative, lang))
    value = fmt_pct(sc.negative_share, 0, lang) if sc.n else DASH
    return L(q.label, lang), value, foot, sc


def result_kpis(cfg, an, lang, cmp_short):
    """Четыре карточки результата: средний балл, довольные, недовольные, главная проблема."""
    sat_cur, sat_cmp = an.sat_cur, an.sat_cmp
    has_cur = sat_cur.n > 0

    if cfg.satisfaction_col is None:
        mean_foot = tr("kpi_mean_foot_composite", lang)
    else:
        q = next(q for q in cfg.questions if q.col == cfg.satisfaction_col)
        mean_foot = tr("kpi_mean_foot_single", lang, q=L(q.label, lang))

    def card(label, value, suffix, comp, delta_text, foot, higher_is_better=True):
        cls = ""
        if comp is not None and comp.status == SIGNIFICANT and comp.delta:
            cls = "good" if (comp.delta > 0) == higher_is_better else "flag"
        return dict(label=label, value=value, suffix=suffix, cls=cls,
                    delta_html=delta_html(with_no_change(delta_text, comp, lang), comp, lang, higher_is_better) if has_cur else "",
                    foot=foot if has_cur else tr("kpi_no_data", lang))

    items = [
        card(tr("kpi_mean", lang), fmt_num(sat_cur.mean, 1, lang) if has_cur else DASH, " / 5" if has_cur else "",
             an.mean_c, fmt_signed(an.mean_c.delta, 1, lang), mean_foot, True),
        card(tr("kpi_pos", lang), fmt_pct(sat_cur.pos_share, 0, lang) if has_cur else DASH, "",
             an.pos_c, fmt_pp(an.pos_c.delta, 0, lang), tr("kpi_pos_foot", lang), True),
        card(tr("kpi_neg", lang), fmt_pct(sat_cur.neg_share, 0, lang) if has_cur else DASH, "",
             an.neg_c, fmt_pp(an.neg_c.delta, 0, lang), tr("kpi_neg_foot", lang), False),
    ]
    parts = problem_card_parts(an, lang)
    if parts:
        label, value, foot, sc = parts
        items.append(card(label, value, "", an.problem_c if sc.n else None,
                          fmt_pp(an.problem_c.delta, 0, lang), foot, False))
    kpi_row(items)


SENT_ORDER = ["pos", "neu", "neg"]   # Позитивные · Нейтральные · Негативные — везде в этом порядке


@st.cache_data
def scored_cache():
    return load_scored()


def render_comments(cfg, lang, df_cur, df_cmp, cols, cur_short, cmp_short):
    scored = scored_cache()
    metrics = load_model_metrics()
    use_model = scored is not None

    st.write("")
    section_head(tr("sec_comments_title", lang),
                 tr("sec_comments_note_model", lang) if use_model else tr("sec_comments_note", lang))
    st.markdown(f'<div class="lang-note">{tr("comments_language_note", lang)}</div>', unsafe_allow_html=True)
    if use_model and metrics and metrics.get("sentiment"):
        m = metrics["sentiment"]
        st.caption(tr("accuracy_line", lang, acc=fmt_pct(m["accuracy"] * 100, 0, lang), n=fmt_int(m["n"], lang)))

    cur = annotate(collect_comments(df_cur, cols, cfg.comment_cols), cfg.key, scored)
    cmp_ = annotate(collect_comments(df_cmp, cols, cfg.comment_cols), cfg.key, scored)
    sent_names = {k: tr(f"sent_{k}", lang) for k in SENT_ORDER}

    def shares(items):
        n = len(items)
        return {k: (sum(1 for c in items if c["sentiment"] == k) / n * 100 if n else 0) for k in SENT_ORDER}

    cur_sent, cmp_sent = shares(cur), shares(cmp_)

    # темы, встречающиеся в текущем периоде (в порядке конфига, «Прочее» — последним)
    topic_keys = [k for k, _, _ in TOPICS.get(cfg.key, [])] + [OTHER_TOPIC]
    present = [k for k in topic_keys if any(c["topic"] == k for c in cur)] if use_model else []

    col_s1, col_s2 = st.columns([1, 1.4])
    with col_s1:
        with st.container(border=True):
            st.markdown(f"**{tr('sentiment_title', lang)}**")
            st.caption(tr("sentiment_caption", lang, cur=fmt_int(len(cur), lang), cur_p=cur_short,
                          cmp=fmt_int(len(cmp_), lang), cmp_p=cmp_short))
            fig = render_grouped_bar([sent_names[k] for k in SENT_ORDER],
                                     [cur_sent[k] for k in SENT_ORDER], [cmp_sent[k] for k in SENT_ORDER],
                                     cur_short, cmp_short, lang)
            st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)
    with col_s2:
        if present:
            with st.container(border=True):
                st.markdown(f"**{tr('topics_title', lang)}**")
                st.caption(tr("topics_note", lang, period=cur_short))
                labels = [topic_label(cfg.key, k, lang) for k in present]
                counts = {sk: [sum(1 for c in cur if c["topic"] == tk and c["sentiment"] == sk) for tk in present]
                          for sk in SENT_ORDER}
                st.plotly_chart(render_topics_bar(labels, counts, sent_names, lang), width="stretch", config=PLOTLY_CFG)

    # --- лента комментариев ---
    st.markdown(f"**{tr('comments_current_title', lang, period=cur_short)}**")
    selected_topic = None
    if present:
        options = [None] + present
        selected_topic = st.selectbox(tr("topic_filter", lang), options,
                                      format_func=lambda k: tr("topic_all", lang) if k is None else topic_label(cfg.key, k, lang),
                                      key=f"{cfg.key}_topic_{lang}")
    feed = [c for c in cur if selected_topic is None or c["topic"] == selected_topic]
    st.caption(tr("feed_note", lang, n=fmt_int(MIN_COMMENT_LEN, lang)))

    buckets = {k: [c["text"] for c in feed if c["sentiment"] == k] for k in SENT_ORDER}
    tabs = st.tabs([f"{sent_names[k]} ({fmt_int(len(buckets[k]), lang)})" for k in SENT_ORDER])
    for tab, key in zip(tabs, SENT_ORDER):
        with tab:
            substantive, short = split_feed(buckets[key])
            if not substantive and not short:
                st.caption(tr("no_comments", lang))
                continue
            for q in substantive[:MAX_FEED_COMMENTS]:
                st.markdown(f'<div class="quote-card {key if key != "neu" else ""}">{q}</div>', unsafe_allow_html=True)
            grouped = group_short_comments(short)
            if grouped:
                st.caption(tr("short_title", lang))
                short_answer_pills([(t, n, key if key != "neu" else "") for t, n in grouped[:30]])


def render_survey(cfg: SurveyConfig, lang: str):
    df = load_prepared(cfg)
    if df.empty:
        st.warning(tr("warn_no_file", lang, title=L(cfg.title, lang)))
        return
    cols = list(df.columns)

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

    # анонимность: для узкого сегмента (меньше ANONYMITY_MIN_GROUP анкет в периоде) данные не показываем
    if seg_selected and any(0 < len(d) < ANONYMITY_MIN_GROUP for d in (df_cur, df_cmp)):
        st.warning(tr("anonymity_msg", lang, n=fmt_int(ANONYMITY_MIN_GROUP, lang)), icon="🔒")
        return

    # описания периодов для подписей: «Последняя волна: Январь 2026» / «Сравнение: Ноябрь 2025»
    cur_desc = describe_periods(cur_sel, lw, lang, role="current")
    cmp_desc = describe_periods(cmp_sel, lw, lang, role="compare")
    cur_short = ", ".join(fmt(p) for p in sorted(cur_sel)) or tr("period_not_selected", lang)
    cmp_short = ", ".join(fmt(p) for p in sorted(cmp_sel)) or tr("period_not_selected", lang)

    n_total, n_cur, n_cmp = len(df), len(df_cur), len(df_cmp)
    counts_line(tr("counts_line", lang, total=fmt_int(n_total, lang), cur_p=cur_short, cur=fmt_int(n_cur, lang),
                   cmp_p=cmp_short, cmp=fmt_int(n_cmp, lang)))

    # пояснение про условный блок анкеты (например, ДМС: вопросы только для пользовавшихся страховкой)
    if cfg.gate is not None and n_cur:
        gate_q = next((q for q in cfg.questions if q.col == cfg.gate.col), None)
        gate_vals = df_cur[cols[cfg.gate.col]].apply(gate_q.normalize) if gate_q else None
        n_gate = int((gate_vals == cfg.gate.category).sum()) if gate_vals is not None else 0
        n_block = int(pd.to_numeric(df_cur[cols[cfg.gate.block_col]], errors="coerce").notna().sum())
        st.info(tr("gate_note", lang, cur_p=cur_short, total=fmt_int(n_cur, lang),
                   ans=cat_label(cfg.gate.category, lang), gate_q=L(gate_q.label, lang) if gate_q else "",
                   gate=fmt_int(n_gate, lang), block=fmt_int(n_block, lang)), icon="ℹ️")

    an = analyze(cfg, df_cur, df_cmp, cols)

    # --- ключевые выводы ---
    section_head(tr("insights_title", lang), tr("insights_note", lang, alpha=fmt_num(SIGNIFICANCE_ALPHA, 2, lang)))
    insights_block(generate_insights(cfg, lang, an.sat_cur, an.sat_cmp, (an.mean_c, an.pos_c, an.neg_c),
                                     an.summ_cur, an.summ_cmp, an.problem_q, cmp_short))

    # --- KPI по результату ---
    result_kpis(cfg, an, lang, cmp_short)
    legend_pills([(CURRENT_COLOR, cur_desc), (COMPARE_COLOR, cmp_desc)])

    st.write("")
    section_head(tr("sec_questions_title", lang), tr("sec_questions_note", lang, cur=cur_short, cmp=cmp_short))
    q_cols = st.columns(2)
    for i, q in enumerate(cfg.questions):
        sc, sm = an.summ_cur[q], an.summ_cmp[q]
        comp = compare_question(sc, sm)
        full_text = question_full_text(cols[q.col], lang)
        with q_cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{L(q.label, lang)}**", help=f"{tr('question_help', lang)}: {full_text}")
                if q.kind == "numeric15":
                    # средний балл по каждому периоду + дельта и метка значимости над полосами
                    if sc.n and sm.n:
                        means = tr("scale_mean_line", lang, cur=fmt_num(sc.mean, 1, lang), cur_p=cur_short,
                                   cmp=fmt_num(sm.mean, 1, lang), cmp_p=cmp_short)
                    elif sc.n:
                        means = tr("scale_mean_line_single", lang, cur=fmt_num(sc.mean, 1, lang), cur_p=cur_short)
                    else:
                        means = None
                    if means:
                        delta_line(means.split(":")[0], means.split(":", 1)[1].strip(),
                                   with_no_change(fmt_signed(comp.delta, 1, lang), comp, lang), comp, lang, True)
                    fig = render_scale_stacked(sc.shares if sc.n else None, sm.shares if sm.n else None,
                                               cur_short, cmp_short, lang)
                    st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)
                    label = SCALE_LABELS.get((cfg.key, q.col))
                    if label:
                        scale_note(L(label, lang))
                elif q.categories == ["yes", "no"]:
                    # компактная карточка вместо графика
                    flag = "yes" in q.negative
                    cmp_text = tr("yn_compare", lang, cmp_p=cmp_short, v=fmt_pct(sm.shares["yes"], 0, lang)) if sm.n else ""
                    yes_no_card(fmt_pct(sc.shares["yes"], 0, lang) if sc.n else DASH, tr("yn_answered_yes", lang),
                                fmt_pp(comp.delta, 0, lang), comp if sc.n else None, lang, cmp_text, flag=flag)
                else:
                    keys = sc.headline_keys
                    if sc.n:
                        delta_line(tr("q_share_line", lang, c=cats_text(keys, lang)), fmt_pct(sc.share_of(keys), 0, lang),
                                   with_no_change(fmt_pp(comp.delta, 0, lang), comp, lang), comp, lang,
                                   higher_is_better=not bool(q.negative))
                    cat_disp = [cat_label(c, lang) for c in q.categories]
                    cur_vals = [sc.shares[c] for c in q.categories]
                    cmp_vals = [sm.shares[c] for c in q.categories]
                    fig = render_grouped_bar(cat_disp, cur_vals, cmp_vals, cur_short, cmp_short, lang)
                    st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)
                st.caption(tr("answered_caption", lang, cur=fmt_int(sc.n, lang), cur_p=cur_short,
                              cmp=fmt_int(sm.n, lang), cmp_p=cmp_short))

    render_comments(cfg, lang, df_cur, df_cmp, cols, cur_short, cmp_short)

    # --- о данных: динамика числа ответов по месяцам (без дыр в оси) ---
    st.write("")
    with st.expander(tr("about_data", lang)):
        st.markdown(f"**{tr('sec_trend_title', lang)}**")
        st.caption(f"{tr('sec_trend_note', lang)}. {tr('about_data_note', lang)}")
        full_range = list(pd.period_range(min(periods), max(periods), freq="M"))
        monthly = df.groupby("_period").size().reindex(full_range, fill_value=0)
        bar_colors = [CURRENT_COLOR if p in cur_periods else (COMPARE_COLOR if p in cmp_periods else MUTED) for p in full_range]
        fig = render_trend_bar([fmt(p) for p in full_range], monthly.values, bar_colors, tr("trend_hover_suffix", lang), lang)
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)


def render_overview(lang: str):
    """Сводка: по карточке на раздел — средний балл, динамика к предыдущей волне, главная проблема."""
    section_head(tr("overview_title", lang), tr("overview_note", lang))
    cards = []
    for cfg in SURVEYS:
        df = load_prepared(cfg)
        title = f"{cfg.icon} {L(cfg.title, lang)}"
        link = tr("overview_details", lang, tab=f"{cfg.icon} {L(cfg.title, lang)}")
        if df.empty:
            cards.append(dict(title=title, sub="", value_label=tr("overview_mean", lang), value=DASH, suffix="",
                              delta_html="", problem_label=tr("overview_problem", lang),
                              problem_text=tr("overview_no_data", lang), link=link))
            continue
        cols = list(df.columns)
        w = waves(df)
        cur_p = w[-1] if w else last_wave(df)
        cmp_p = w[-2] if len(w) >= 2 else None
        df_cur = df[df["_period"] == cur_p]
        df_cmp = df[df["_period"] == cmp_p] if cmp_p is not None else df.iloc[0:0]
        an = analyze(cfg, df_cur, df_cmp, cols)

        sub = f"{tr('last_wave_desc', lang, period=period_label(cur_p, lang))} · " \
              f"{tr('overview_responses', lang, n=fmt_int(len(df_cur), lang))}"
        if an.sat_cur.n:
            value = fmt_num(an.sat_cur.mean, 1, lang)
            dh = delta_html(with_no_change(fmt_signed(an.mean_c.delta, 1, lang), an.mean_c, lang), an.mean_c, lang, True)
            if cmp_p is not None:
                dh = dh.replace('</div>', f'<span class="sig">· {tr("overview_vs", lang, period=period_label(cmp_p, lang))}</span></div>')
        else:
            value, dh = DASH, ""
        parts = problem_card_parts(an, lang)
        if parts and parts[3].n:
            label, pval, foot, sc = parts
            problem_text = f"<b>{pval}</b> — «{label}», {foot}"
        else:
            problem_text = tr("overview_no_data", lang)
        cls = ""
        if an.mean_c.status == SIGNIFICANT and an.mean_c.delta:
            cls = "good" if an.mean_c.delta > 0 else "flag"
        cards.append(dict(title=title, sub=sub, value_label=tr("overview_mean", lang), value=value,
                          suffix=" / 5" if an.sat_cur.n else "", delta_html=dh,
                          problem_label=tr("overview_problem", lang), problem_text=problem_text, link=link, cls=cls))
    overview_cards(cards)


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
_loaded = [d for d in (load_prepared(s) for s in SURVEYS) if not d.empty]
_updated = data_updated_at(_loaded)
_last_waves = [last_wave(d) for d in _loaded if last_wave(d) is not None]
hero(LANG,
     fmt_date(_updated, LANG) if _updated is not None else DASH,
     period_label(max(_last_waves), LANG) if _last_waves else DASH)

tabs = st.tabs([f"📋 {tr('tab_overview', LANG)}"] + [f"{s.icon} {L(s.title, LANG)}" for s in SURVEYS])
with tabs[0]:
    render_overview(LANG)
for tab, cfg in zip(tabs[1:], SURVEYS):
    with tab:
        render_survey(cfg, LANG)

st.divider()
_metrics = load_model_metrics()
_footer_key = "footer_note_model" if (scored_cache() is not None and _metrics and _metrics.get("sentiment")) else "footer_note"
st.markdown(f'<div class="foot-note">{tr(_footer_key, LANG)}</div>', unsafe_allow_html=True)

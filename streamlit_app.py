import glob
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).parent

st.set_page_config(page_title="Опросы удовлетворённости", page_icon="📊", layout="wide")

# ---------------------------------------------------------------- palette --
BG, SURFACE, BORDER = "#eef1f6", "#ffffff", "rgba(20,27,46,0.10)"
INK, INK_2, INK_MUTED = "#141b2e", "#4a5573", "#8891a8"
NAVY, NAVY_DEEP, SKY = "#1b2a63", "#101a42", "#5f86dd"

CURRENT_COLOR, COMPARE_COLOR = "#1b2a63", "#8facea"
GOOD, CRITICAL, WARN, MUTED = "#1f9d55", "#d9503d", "#e0a530", "#c7cbd6"
POS_SENT, NEU_SENT, NEG_SENT = "#1f9d55", "#c7cbd6", "#d9503d"
CHART_TEXT = INK_2
CARD_SHADOW = "0 1px 2px rgba(16,26,66,0.05), 0 10px 24px -14px rgba(16,26,66,0.22)"
PLOTLY_CFG = {"displayModeBar": False}
RU_MONTHS = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
             "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

st.markdown(
    textwrap.dedent(f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] {{ font-family:"Public Sans", system-ui, sans-serif; }}
      .stApp {{ background:{BG}; }}
      #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ visibility:hidden; height:0; }}
      .block-container{{ padding-top:0; padding-bottom:3rem; max-width:1220px; }}
      h1,h2,h3,h4,h5 {{ font-family:"Manrope", system-ui, sans-serif; }}
      .hero{{
        background:linear-gradient(135deg,{NAVY_DEEP} 0%,{NAVY} 62%,#2c418f 100%);
        margin:0 -1rem 24px; padding:28px 40px 24px;
        border-radius:0 0 22px 22px;
        display:flex; align-items:center; justify-content:space-between; gap:24px; flex-wrap:wrap;
        box-shadow:0 14px 30px -18px rgba(16,26,66,0.55);
      }}
      .hero .kicker{{ font-size:11.5px; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; color:{SKY}; margin-bottom:8px; }}
      .hero-title{{ display:flex; align-items:center; gap:14px; }}
      .hero-title .tri{{ width:0; height:0; flex:none; border-top:15px solid transparent; border-bottom:15px solid transparent; }}
      .hero-title .tri.left{{ border-left:20px solid {SKY}; }}
      .hero-title .tri.right{{ border-right:20px solid {SKY}; opacity:0.55; }}
      .hero-title h1{{ margin:0; color:#ffffff; font-size:32px; font-weight:800; letter-spacing:-0.01em; white-space:nowrap; }}
      .hero .sub{{ color:#c7d3f4; font-size:13.5px; margin-top:8px; max-width:56ch; }}
      .sec-head{{ display:flex; align-items:baseline; gap:10px; margin:6px 0 4px; }}
      .sec-head .bar{{ width:5px; height:20px; border-radius:3px; background:{NAVY}; flex:none; }}
      .sec-head h2{{ font-size:18px; font-weight:800; color:{INK}; margin:0; }}
      .sec-note{{ font-size:12.5px; color:{INK_MUTED}; margin:2px 0 14px 15px; }}
      .kpi-row{{ display:grid; grid-template-columns:repeat(4,minmax(150px,1fr)); gap:14px; margin-bottom:6px; }}
      @media (max-width:900px){{ .kpi-row{{ grid-template-columns:repeat(2,1fr); }} }}
      .kpi-card{{
        background:{SURFACE}; border:1px solid {BORDER}; border-left:4px solid {NAVY}; border-radius:12px;
        box-shadow:{CARD_SHADOW}; padding:16px 18px 14px; display:flex; flex-direction:column; gap:8px; min-width:0;
      }}
      .kpi-card.good{{ border-left-color:{GOOD}; }}
      .kpi-card.flag{{ border-left-color:{CRITICAL}; }}
      .kpi-card.compare{{ border-left-color:{COMPARE_COLOR}; }}
      .kpi-card .kpi-label{{ font-size:11px; font-weight:700; letter-spacing:0.04em; text-transform:uppercase; color:{INK_MUTED}; line-height:1.4; min-height:28px; }}
      .kpi-card .kpi-value{{ font-family:"Manrope",sans-serif; font-size:28px; font-weight:800; color:{INK}; letter-spacing:-0.01em; }}
      .kpi-card .kpi-value small{{ font-size:13px; font-weight:600; color:{INK_MUTED}; margin-left:2px; }}
      .kpi-card .kpi-foot{{ font-size:11.5px; color:{INK_MUTED}; }}
      .kpi-card.flag .kpi-value{{ color:{CRITICAL}; }}
      .kpi-card.good .kpi-value{{ color:{GOOD}; }}
      .kpi-card.compare .kpi-value{{ color:{COMPARE_COLOR}; }}
      div[data-testid="stVerticalBlockBorderWrapper"]{{ background:{SURFACE}; border:1px solid {BORDER} !important; border-radius:14px !important; box-shadow:{CARD_SHADOW}; }}
      div[data-testid="stVerticalBlockBorderWrapper"] > div {{ border-radius:14px; }}
      .quote-card{{
        background:{SURFACE}; border:1px solid {BORDER}; border-left:3px solid {NAVY};
        border-radius:8px; padding:12px 16px; margin-bottom:9px; font-style:italic; font-size:13px;
        line-height:1.5; color:{INK_2}; box-shadow:{CARD_SHADOW};
      }}
      .quote-card.pos{{ border-left-color:{POS_SENT}; }}
      .quote-card.neg{{ border-left-color:{NEG_SENT}; }}
      .quote-card::before{{content:"\\201C"; font-style:normal; font-weight:800; color:{NAVY}; margin-right:2px;}}
      .legend-pill{{ display:inline-flex; align-items:center; gap:6px; font-size:12.5px; color:{INK_2}; margin-right:18px; }}
      .legend-pill .sw{{ width:11px; height:11px; border-radius:3px; }}
      hr {{ border-color:{BORDER} !important; margin:26px 0 20px !important; }}
      .foot-note {{ font-size:11px; color:{INK_MUTED}; line-height:1.6; }}
      .stTabs [data-baseweb="tab-list"] {{ gap:6px; }}
      .stTabs [data-baseweb="tab"] {{ background:{SURFACE}; border-radius:10px 10px 0 0; padding:10px 18px; font-weight:600; }}
    </style>
    """),
    unsafe_allow_html=True,
)


def section_head(title, note):
    st.markdown(
        f'<div class="sec-head"><span class="bar"></span><h2>{title}</h2></div>'
        f'<div class="sec-note">{note}</div>',
        unsafe_allow_html=True,
    )


def kpi_row(items):
    st.markdown(
        '<div class="kpi-row">' + "".join(
            f'''<div class="kpi-card {cls}">
                  <div class="kpi-label">{label}</div>
                  <div class="kpi-value">{value}<small>{suffix}</small></div>
                  <div class="kpi-foot">{foot}</div>
                </div>'''
            for label, value, suffix, cls, foot in items
        ) + "</div>",
        unsafe_allow_html=True,
    )


# ============================================================== data model --
@dataclass
class Question:
    col: int
    label: str
    kind: str  # "numeric15" or "categorical"
    categories: list = field(default_factory=list)   # required for "categorical"
    normalize: object = None                          # fn(raw_str) -> canonical category | None


@dataclass
class Segment:
    col: int
    label: str
    extract: object  # fn(raw_str) -> list[str] of tags


@dataclass
class SurveyConfig:
    key: str
    title: str
    icon: str
    file_glob: str
    date_col: int
    questions: list
    comment_cols: list
    segment: object = None


def yn_normalize(raw):
    if pd.isna(raw):
        return None
    t = str(raw).strip().lower()
    if t.startswith("да") or t.startswith("yes") or t.startswith("иә") or t.startswith("ия"):
        return "Да"
    if t.startswith("нет") or t.startswith("no") or t.startswith("жок"):
        return "Нет"
    return None


def prefix_normalize(order):
    prefixes = [(p.lower(), p) for p in order]

    def fn(raw):
        if pd.isna(raw):
            return None
        t = str(raw).strip().lower()
        for p_low, p_orig in prefixes:
            if t.startswith(p_low):
                return p_orig
        return None
    return fn


def extract_locations(raw):
    if pd.isna(raw):
        return []
    return [p.strip() for p in str(raw).split(";") if p.strip()]


ROUTE_RE = re.compile(r"[Мм]аршрут\s*#?\s*(\d+)")


def extract_routes(raw):
    if pd.isna(raw):
        return []
    nums = ROUTE_RE.findall(str(raw))
    if nums:
        return [f"Маршрут #{n}" for n in sorted(set(int(n) for n in nums))]
    return ["Другое / личный транспорт"]


CANTEEN = SurveyConfig(
    key="canteen", title="Столовая · Асхана", icon="🍲",
    file_glob="СТОЛОВАЯ*.xlsx", date_col=1,
    segment=Segment(col=6, label="Локация столовой", extract=extract_locations),
    questions=[
        Question(11, "Вкус и качество блюд", "numeric15"),
        Question(12, "Полезность питания", "numeric15"),
        Question(13, "Чистота и гигиена", "numeric15"),
        Question(14, "Разнообразие меню", "numeric15"),
        Question(15, "Размер порций", "numeric15"),
        Question(17, "Проблемы ЖКТ после еды", "categorical", ["Да", "Нет"], yn_normalize),
    ],
    comment_cols=[18],
)

TRANSPORT = SurveyConfig(
    key="transport", title="Транспорт · Развозка", icon="🚐",
    file_glob="ТРАНСПОРТ*.xlsx", date_col=1,
    segment=Segment(col=6, label="Маршрут", extract=extract_routes),
    questions=[
        Question(7, "Место сбора", "numeric15"),
        Question(8, "Пунктуальность", "numeric15"),
        Question(9, "Охват маршрутов", "numeric15"),
        Question(10, "Достаточность мест", "numeric15"),
        Question(11, "Безопасность", "numeric15"),
        Question(12, "Комфорт", "numeric15"),
        Question(13, "Соответствие расписанию", "numeric15"),
    ],
    comment_cols=[14, 15],
)

DMS = SurveyConfig(
    key="dms", title="Медстраховка · ДМС", icon="🩺",
    file_glob="МЕДИЦИНСКАЯ*.xlsx", date_col=1,
    segment=None,
    questions=[
        Question(7, "Пользовались страховкой за 12 мес.", "categorical", ["Да", "Нет"], yn_normalize),
        Question(11, "Частота доплат сверх покрытия", "categorical",
                 ["Никогда", "Редко", "Иногда", "Часто", "Всегда"],
                 prefix_normalize(["Никогда", "Редко", "Иногда", "Часто", "Всегда"])),
        Question(14, "Удовлетворённость услугами", "numeric15"),
        Question(15, "Время ожидания услуги", "numeric15"),
        Question(17, "Откладывали лечение из-за лимитов", "categorical", ["Да", "Нет"], yn_normalize),
        Question(19, "Обращались за ночной помощью", "categorical", ["Да", "Нет"], yn_normalize),
    ],
    comment_cols=[21],
)

SURVEYS = [CANTEEN, TRANSPORT, DMS]


@st.cache_data
def load_survey(file_glob: str) -> pd.DataFrame:
    matches = glob.glob(str(BASE_DIR / file_glob))
    if not matches:
        return pd.DataFrame()
    df = pd.read_excel(matches[0], sheet_name=0)
    return df


# ============================================================ sentiment --
POSITIVE_WORDS = [
    "хорош", "отличн", "супер", "прекрасн", "устраива", "нрав", "спасибо",
    "вкусн", "удобн", "быстр", "чист", "довол", "класс", "молодц", "комфорт",
    "satisfied", "good", "great", "excellent", "жаксы", "рахмет",
]
NEGATIVE_WORDS = [
    "плохо", "ужас", "грязн", "долго", "неудобн", "жалоб", "проблем",
    "не работа", "не устраива", "недостаточ", "не хвата", "хамств", "груб",
    "опаздыва", "не приезжа", "жирн", "невкусн", "холодн", "дорог", "медленн",
    "отказ", "некомпетент", "bad", "poor", "terrible", "slow", "жаман",
]
NEGATION_WORDS = {"не", "ни", "нет", "no", "not", "жоқ", "жок"}
WORD_RE = re.compile(r"[a-zа-яёқғңөұүhі]+")
NO_COMMENT = {
    "нет", "-", ".", "..", "...", "", "нет комментариев", "без комментариев",
    "нету", "коментариев нет", "комментариев нет", "жок", "нема", "no", "net",
    "n/a", "na", "?", "нет отзывов", "все хорошо.", "-.",
}


def is_gibberish(t):
    letters = re.sub(r"[^a-zа-яёқғңөұүhі]", "", t.lower())
    if len(letters) < 6:
        return True
    return len(set(letters)) / len(letters) < 0.28


def clean_comments(series: pd.Series):
    out = []
    for raw in series.dropna():
        t = str(raw).strip()
        tl = t.lower()
        if tl in NO_COMMENT or len(t) < 4 or is_gibberish(t):
            continue
        out.append(t)
    return out


def sentiment_of(text):
    t = text.lower()
    pos = neg = 0

    # multi-word / phrase-level negative cues (already encode their own negation)
    neg += sum(1 for w in NEGATIVE_WORDS if w in t)

    # single-stem positive cues, flipped to negative when directly negated
    # ("не вкусно" must not count as positive just because it contains "вкусн")
    tokens = WORD_RE.findall(t)
    for i, tok in enumerate(tokens):
        stem = next((w for w in POSITIVE_WORDS if tok.startswith(w)), None)
        if stem is None:
            continue
        negated = i > 0 and tokens[i - 1] in NEGATION_WORDS
        if negated:
            neg += 1
        else:
            pos += 1

    if pos > neg:
        return "pos"
    if neg > pos:
        return "neg"
    return "neu"


# ============================================================ rendering --
def period_options(df, date_col):
    dt = pd.to_datetime(df.iloc[:, date_col], errors="coerce")
    periods = dt.dropna().dt.to_period("M").unique()
    periods = sorted(periods)
    labels = [f"{RU_MONTHS[p.month]} {p.year}" for p in periods]
    return periods, labels


def render_grouped_bar(cats, cur_vals, cmp_vals, cur_label, cmp_label, x_title=""):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=cats, y=cmp_vals, name=cmp_label, marker=dict(color=COMPARE_COLOR, cornerradius=4)))
    fig.add_trace(go.Bar(x=cats, y=cur_vals, name=cur_label, marker=dict(color=CURRENT_COLOR, cornerradius=4)))
    fig.update_layout(
        barmode="group", height=230, margin=dict(l=10, r=10, t=6, b=30),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CHART_TEXT, family="Public Sans, sans-serif", size=11.5),
        showlegend=False,
        xaxis=dict(showgrid=False, title=x_title, color=CHART_TEXT),
        yaxis=dict(showgrid=True, gridcolor="rgba(20,27,46,0.06)", ticksuffix="%", color=CHART_TEXT),
        bargap=0.28, bargroupgap=0.12,
    )
    return fig


def render_survey(cfg: SurveyConfig):
    df = load_survey(cfg.file_glob)
    if df.empty:
        st.warning(f"Файл с данными для «{cfg.title}» не найден рядом со streamlit_app.py.")
        return
    cols = list(df.columns)
    dt = pd.to_datetime(df[cols[cfg.date_col]], errors="coerce")
    df = df.assign(_dt=dt, _period=dt.dt.to_period("M"))

    periods, labels = period_options(df, cfg.date_col)
    if not periods:
        st.warning("В файле нет распознаваемых дат.")
        return
    label_by_period = dict(zip(periods, labels))
    period_by_label = dict(zip(labels, periods))

    # default to the two best-populated waves (not just the newest calendar month,
    # which may be a near-empty tail), later one = current, earlier one = compare
    counts = df["_period"].value_counts()
    busiest = sorted(periods, key=lambda p: counts.get(p, 0), reverse=True)[:2]
    busiest.sort()
    if len(busiest) == 2:
        default_compare, default_current = [label_by_period[busiest[0]]], [label_by_period[busiest[1]]]
    elif busiest:
        default_current, default_compare = [label_by_period[busiest[0]]], []
    else:
        default_current, default_compare = [], []

    filt_cols = st.columns([1.3, 1.3, 1.4] if cfg.segment else [1.5, 1.5])
    with filt_cols[0]:
        cur_sel = st.multiselect("Текущий период", labels, default=default_current, key=f"{cfg.key}_cur",
                                  placeholder="Выберите период")
    with filt_cols[1]:
        cmp_sel = st.multiselect("Период сравнения", labels, default=default_compare, key=f"{cfg.key}_cmp",
                                  placeholder="Выберите период")

    seg_selected = None
    if cfg.segment:
        raw_tags = df[cols[cfg.segment.col]].apply(cfg.segment.extract)
        all_tags = sorted({t for tags in raw_tags for t in tags})
        with filt_cols[2]:
            seg_selected = st.multiselect(cfg.segment.label, all_tags, default=[], key=f"{cfg.key}_seg",
                                           placeholder="Все")
        if seg_selected:
            mask = raw_tags.apply(lambda tags: any(t in seg_selected for t in tags))
            df = df[mask]
            df = df.assign(_dt=df["_dt"], _period=df["_period"])

    cur_periods = {period_by_label[l] for l in cur_sel}
    cmp_periods = {period_by_label[l] for l in cmp_sel}
    df_cur = df[df["_period"].isin(cur_periods)]
    df_cmp = df[df["_period"].isin(cmp_periods)]

    n_total, n_cur, n_cmp = len(df), len(df_cur), len(df_cmp)
    delta_pct = round((n_cur - n_cmp) / n_cmp * 100, 1) if n_cmp else None

    kpi_row([
        ("Анкет собрано всего", n_total, "", "", "за всё время сбора данных"),
        ("Анкет за текущий период", n_cur, "", "", ", ".join(cur_sel) or "период не выбран"),
        ("Анкет за период сравнения", n_cmp, "", "compare", ", ".join(cmp_sel) or "период не выбран"),
        ("Изменение числа анкет", (f"{'+' if delta_pct and delta_pct > 0 else ''}{delta_pct}" if delta_pct is not None else "—"),
         "%" if delta_pct is not None else "", "good" if (delta_pct or 0) >= 0 else "flag", "текущий период к периоду сравнения"),
    ])

    st.markdown(
        f'<span class="legend-pill"><span class="sw" style="background:{CURRENT_COLOR}"></span>Текущий период</span>'
        f'<span class="legend-pill"><span class="sw" style="background:{COMPARE_COLOR}"></span>Период сравнения</span>',
        unsafe_allow_html=True,
    )

    st.write("")
    section_head("Динамика количества ответов", "Число заполненных анкет по месяцам за всю историю сбора (с учётом фильтра сегмента)")
    monthly = df.groupby("_period").size().reindex(periods, fill_value=0)
    bar_colors = [CURRENT_COLOR if p in cur_periods else (COMPARE_COLOR if p in cmp_periods else MUTED) for p in periods]
    fig = go.Figure(go.Bar(
        x=[label_by_period[p] for p in periods], y=monthly.values,
        marker=dict(color=bar_colors, cornerradius=4),
        text=monthly.values, textposition="outside", textfont=dict(color=CHART_TEXT),
        hovertemplate="%{x}: <b>%{y}</b> анкет<extra></extra>",
    ))
    fig.update_layout(
        height=260, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CHART_TEXT, family="Public Sans, sans-serif"),
        xaxis=dict(showgrid=False, color=CHART_TEXT), yaxis=dict(showgrid=False, visible=False),
    )
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)

    st.write("")
    section_head("Ответы по вопросам", "Тёмно-синий столбец — текущий период, голубой — период сравнения. По вертикали — доля ответивших, в процентах")
    q_cols = st.columns(2)
    for i, q in enumerate(cfg.questions):
        col_name = cols[q.col]
        with q_cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{q.label}**")
                if q.kind == "numeric15":
                    cur_s = pd.to_numeric(df_cur[col_name], errors="coerce").dropna()
                    cmp_s = pd.to_numeric(df_cmp[col_name], errors="coerce").dropna()
                    cats = ["1", "2", "3", "4", "5"]
                    cur_vals = [round((cur_s == k).sum() / len(cur_s) * 100, 1) if len(cur_s) else 0 for k in range(1, 6)]
                    cmp_vals = [round((cmp_s == k).sum() / len(cmp_s) * 100, 1) if len(cmp_s) else 0 for k in range(1, 6)]
                    fig = render_grouped_bar(cats, cur_vals, cmp_vals, "Текущий", "Сравнение", "оценка (1–5)")
                else:
                    cur_norm = df_cur[col_name].apply(q.normalize).dropna()
                    cmp_norm = df_cmp[col_name].apply(q.normalize).dropna()
                    cur_vals = [round((cur_norm == c).sum() / len(cur_norm) * 100, 1) if len(cur_norm) else 0 for c in q.categories]
                    cmp_vals = [round((cmp_norm == c).sum() / len(cmp_norm) * 100, 1) if len(cmp_norm) else 0 for c in q.categories]
                    fig = render_grouped_bar(q.categories, cur_vals, cmp_vals, "Текущий", "Сравнение")
                st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)
                cur_n = len(pd.to_numeric(df_cur[col_name], errors="coerce").dropna()) if q.kind == "numeric15" else df_cur[col_name].apply(q.normalize).dropna().shape[0]
                cmp_n = len(pd.to_numeric(df_cmp[col_name], errors="coerce").dropna()) if q.kind == "numeric15" else df_cmp[col_name].apply(q.normalize).dropna().shape[0]
                st.caption(f"На этот вопрос ответили: {cur_n} чел. за текущий период, {cmp_n} чел. за период сравнения")

    st.write("")
    section_head("Комментарии сотрудников", "Пустые и малоинформативные ответы исключены; тональность определена по ключевым словам (эвристика)")
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
            st.markdown(f"**Тональность комментариев**")
            st.caption(f"Комментариев с текстом: {len(all_comments_cur)} за текущий период, {len(all_comments_cmp)} за период сравнения")
            fig = render_grouped_bar(["Позитив", "Нейтрально", "Негатив"],
                                      [cur_sent["pos"], cur_sent["neu"], cur_sent["neg"]],
                                      [cmp_sent["pos"], cmp_sent["neu"], cmp_sent["neg"]],
                                      "Текущий", "Сравнение")
            st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)

    with col_s2:
        st.markdown("**Комментарии за текущий период**")
        tabs = st.tabs([f"Позитивные ({sum(1 for c in all_comments_cur if sentiment_of(c)=='pos')})",
                        f"Негативные ({sum(1 for c in all_comments_cur if sentiment_of(c)=='neg')})",
                        f"Нейтральные ({sum(1 for c in all_comments_cur if sentiment_of(c)=='neu')})"])
        buckets = {"pos": [], "neg": [], "neu": []}
        for c in all_comments_cur:
            buckets[sentiment_of(c)].append(c)
        for tab, key, cls in zip(tabs, ["pos", "neg", "neu"], ["pos", "neg", ""]):
            with tab:
                sample = buckets[key][:8]
                if not sample:
                    st.caption("Нет комментариев в этой категории за выбранный период.")
                for q in sample:
                    st.markdown(f'<div class="quote-card {cls}">{q}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ hero --
st.markdown(
    textwrap.dedent("""
    <div class="hero">
      <div>
        <div class="kicker">Satisfaction Survey · Прототип для обсуждения</div>
        <div class="hero-title">
          <span class="tri left"></span>
          <h1>Опросы удовлетворённости</h1>
          <span class="tri right"></span>
        </div>
        <div class="sub">Столовая, транспорт и медстраховка — сравнение текущей волны опроса с предыдущим периодом.</div>
      </div>
    </div>
    """),
    unsafe_allow_html=True,
)

tabs = st.tabs([f"{s.icon} {s.title}" for s in SURVEYS])
for tab, cfg in zip(tabs, SURVEYS):
    with tab:
        render_survey(cfg)

st.divider()
st.markdown(
    '<div class="foot-note">Прототип для внутреннего обсуждения. Тональность комментариев определяется '
    'простым эвристическим анализом ключевых слов, а не полноценной NLP-моделью, и может ошибаться на сарказме '
    'и сложных формулировках — на следующих итерациях можно уточнить словарь или подключить более точную модель.</div>',
    unsafe_allow_html=True,
)

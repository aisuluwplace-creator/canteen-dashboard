import re
import textwrap
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_FILE = "Столовая - Асхана - Canteen(1-654).xlsx"

st.set_page_config(page_title="Пульс столовой · Асхана", page_icon="🍲", layout="wide")

# ---------------------------------------------------------------- palette --
# Light corporate ground with the navy / medium-blue pair from the TAV Almaty (ALA)
# Power BI house style — same two-tone family as the airport's own dashboards.
BG, SURFACE, BORDER = "#eef1f6", "#ffffff", "rgba(20,27,46,0.10)"
INK, INK_2, INK_MUTED = "#141b2e", "#4a5573", "#8891a8"
NAVY, NAVY_DEEP, SKY = "#1b2a63", "#101a42", "#5f86dd"

POS_5, POS_4 = "#1b2a63", "#8facea"
NEU_3 = "#d7dbe4"
NEG_2, NEG_1 = "#f3b7ab", "#d9503d"
GOOD, CRITICAL, WARN, MUTED = "#1f9d55", "#d9503d", "#e0a530", "#c7cbd6"
DISH_A, DISH_B = "#1b2a63", "#8facea"
FIX_A, FIX_B = "#d9503d", "#f3b7ab"
CHART_TEXT = INK_2
CARD_SHADOW = "0 1px 2px rgba(16,26,66,0.05), 0 10px 24px -14px rgba(16,26,66,0.22)"

st.markdown(
    textwrap.dedent(f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] {{ font-family:"Public Sans", system-ui, sans-serif; }}
      .stApp {{ background:{BG}; }}
      #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ visibility:hidden; height:0; }}
      .block-container{{ padding-top:0; padding-bottom:3rem; max-width:1180px; }}
      h1,h2,h3,h4,h5 {{ font-family:"Manrope", system-ui, sans-serif; }}
      /* ---- hero banner ---- */
      .hero{{
        background:linear-gradient(135deg,{NAVY_DEEP} 0%,{NAVY} 62%,#2c418f 100%);
        margin:0 -1rem 28px; padding:30px 40px 26px;
        border-radius:0 0 22px 22px;
        display:flex; align-items:center; justify-content:space-between; gap:24px; flex-wrap:wrap;
        box-shadow:0 14px 30px -18px rgba(16,26,66,0.55);
      }}
      .hero .kicker{{
        font-size:11.5px; font-weight:700; letter-spacing:0.14em; text-transform:uppercase;
        color:{SKY}; margin-bottom:8px;
      }}
      .hero-title{{ display:flex; align-items:center; gap:14px; }}
      .hero-title .tri{{
        width:0; height:0; flex:none;
        border-top:15px solid transparent; border-bottom:15px solid transparent;
      }}
      .hero-title .tri.left{{ border-left:20px solid {SKY}; }}
      .hero-title .tri.right{{ border-right:20px solid {SKY}; opacity:0.55; }}
      .hero-title h1{{
        margin:0; color:#ffffff; font-size:34px; font-weight:800; letter-spacing:-0.01em; white-space:nowrap;
      }}
      .hero .sub{{ color:#c7d3f4; font-size:13.5px; margin-top:8px; max-width:52ch; }}
      .hero-chips{{ display:flex; flex-direction:column; gap:8px; align-items:flex-end; }}
      .hero-chip{{
        display:inline-flex; align-items:center; gap:8px;
        background:rgba(255,255,255,0.10); border:1px solid rgba(255,255,255,0.16);
        border-radius:999px; padding:7px 14px; font-size:12.5px; color:#dfe7fb; white-space:nowrap;
      }}
      .hero-chip b{{ color:#ffffff; font-weight:700; font-variant-numeric:tabular-nums; }}
      /* ---- section headers ---- */
      .sec-head{{ display:flex; align-items:baseline; gap:10px; margin:6px 0 4px; }}
      .sec-head .bar{{ width:5px; height:20px; border-radius:3px; background:{NAVY}; flex:none; }}
      .sec-head h2{{ font-size:19px; font-weight:800; color:{INK}; margin:0; }}
      .sec-note{{ font-size:12.5px; color:{INK_MUTED}; margin:2px 0 16px 15px; }}
      /* ---- kpi cards ---- */
      .kpi-row{{ display:grid; grid-template-columns:repeat(5,minmax(150px,1fr)); gap:14px; margin-bottom:6px; }}
      @media (max-width:900px){{ .kpi-row{{ grid-template-columns:repeat(2,1fr); }} }}
      .kpi-card{{
        background:{SURFACE}; border:1px solid {BORDER}; border-left:4px solid {NAVY}; border-radius:12px;
        box-shadow:{CARD_SHADOW};
        padding:16px 18px 14px; display:flex; flex-direction:column; gap:8px; min-width:0;
        transition:transform .15s ease, box-shadow .15s ease;
      }}
      .kpi-card:hover{{ transform:translateY(-2px); box-shadow:0 4px 10px rgba(16,26,66,0.08), 0 16px 30px -16px rgba(16,26,66,0.30); }}
      .kpi-card.good{{ border-left-color:{GOOD}; }}
      .kpi-card.flag{{ border-left-color:{CRITICAL}; }}
      .kpi-card .kpi-label{{
        font-size:11px; font-weight:700; letter-spacing:0.04em; text-transform:uppercase;
        color:{INK_MUTED}; line-height:1.4; min-height:30px;
      }}
      .kpi-card .kpi-value{{ font-family:"Manrope",sans-serif; font-size:30px; font-weight:800; color:{INK}; letter-spacing:-0.01em; }}
      .kpi-card .kpi-value small{{ font-size:14px; font-weight:600; color:{INK_MUTED}; margin-left:2px; }}
      .kpi-card .kpi-foot{{ font-size:11.5px; color:{INK_MUTED}; }}
      .kpi-card.flag .kpi-value{{ color:{CRITICAL}; }}
      .kpi-card.good .kpi-value{{ color:{GOOD}; }}
      .side-card{{
        background:{SURFACE}; border:1px solid {BORDER}; border-left:4px solid {GOOD}; border-radius:12px;
        box-shadow:{CARD_SHADOW};
        padding:20px 22px; height:100%; display:flex; flex-direction:column; justify-content:center; gap:8px;
      }}
      .side-card .kpi-value{{ font-family:"Manrope",sans-serif; font-size:32px; font-weight:800; color:{GOOD}; }}
      .side-card .kpi-foot{{ font-size:12.5px; color:{INK_2}; line-height:1.55; }}
      /* ---- chart card wrapper (st.container(border=True)) ---- */
      div[data-testid="stVerticalBlockBorderWrapper"]{{
        background:{SURFACE}; border:1px solid {BORDER} !important; border-radius:14px !important;
        box-shadow:{CARD_SHADOW};
      }}
      div[data-testid="stVerticalBlockBorderWrapper"] > div {{ border-radius:14px; }}
      /* ---- quotes ---- */
      .quote-card{{
        background:{SURFACE}; border:1px solid {BORDER}; border-left:3px solid {NAVY};
        border-radius:8px; padding:13px 17px; margin-bottom:10px; font-style:italic; font-size:13.5px;
        line-height:1.55; color:{INK_2}; box-shadow:{CARD_SHADOW};
      }}
      .quote-card::before{{content:"\\201C"; font-style:normal; font-weight:800; color:{NAVY}; margin-right:2px;}}
      hr {{ border-color:{BORDER} !important; margin:30px 0 22px !important; }}
      .foot-note {{ font-size:11.5px; color:{INK_MUTED}; line-height:1.6; }}
    </style>
    """),
    unsafe_allow_html=True,
)

# ------------------------------------------------------------- load data --
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name="Sheet1")


@st.cache_data
def prepare(path: str):
    df = load_data(path)
    cols = list(df.columns)

    short_labels = {
        5: "Регулярность посещения",
        6: "Удовлетворённость качеством питания",
        7: "Разнообразие меню",
        9: "Свежесть продуктов",
        10: "Вкусовые качества",
        11: "Температура подачи",
        12: "Вежливость персонала",
        13: "Санитария и чистота",
        14: "Самочувствие после еды",
    }

    questions = []
    means = []
    for idx, label in short_labels.items():
        s = df[cols[idx]].dropna().astype(int)
        n = len(s)
        pct = {k: round((s == k).sum() / n * 100, 1) for k in range(1, 6)}
        mean = round(s.mean(), 2)
        means.append(mean)
        questions.append({"label": label, "mean": mean, "pct": pct, "n": n})
    questions.sort(key=lambda q: q["mean"])

    overall_index = round(sum(means) / len(means) / 5 * 100, 1)
    total = len(df)

    reg = df[cols[5]].dropna().astype(int)
    regular_pct = round((reg >= 4).sum() / len(reg) * 100, 1)
    sat = df[cols[6]].dropna().astype(int)
    satisfied_pct = round((sat >= 4).sum() / len(sat) * 100, 1)

    # collection window, dropping a lone far outlier date (gap > 60 days)
    dates = df[cols[1]].dropna().sort_values()
    gaps = dates.diff().dt.days
    main_dates = dates[gaps.isna() | (gaps <= 60)]
    date_min, date_max = main_dates.min(), main_dates.max()

    # GI discomfort classification
    def classify_gi(v):
        if pd.isna(v):
            return None
        t = str(v).strip().lower()
        if not t:
            return None
        if any(t.startswith(p) for p in ["нет", "жоқ", "жок", "no"]):
            return "no"
        if any(t.startswith(p) for p in ["да", "иә", "ия", "yes", "иа"]):
            return "yes"
        return "unclear"

    gi = df[cols[16]].apply(classify_gi)
    gi_counts = gi.value_counts(dropna=True)
    gi_total = gi_counts.sum()
    gi_summary = {k: round(v / gi_total * 100, 1) for k, v in gi_counts.items()}
    for k in ["yes", "no", "unclear"]:
        gi_summary.setdefault(k, 0.0)

    junk = {
        "все", "нет", ".", "-", "никакие", "не знаю", "затрудняюсь ответить", "",
        "все блюда", "всё", "всё нравится", "все нравится", "все устраивает",
        "всё устраивает", "не пробовал", "не пробовала", "n/a", "na", "?", "..", "...",
        "нет таких", "ничего", "никакой", "никаких", "все норм", "все нормально",
        "все хорошо", "почти все", "все вкусно",
    }

    def top_phrases(colidx, top_n=10, min_count=3):
        s = df[cols[colidx]].dropna().astype(str).str.strip().str.lower()
        s = s[~s.isin(junk) & (s.str.len() > 1)]
        vc = s.value_counts()
        vc = vc[vc >= min_count]
        return [{"label": k.capitalize(), "count": int(v)} for k, v in vc.head(top_n).items()]

    top_dishes = top_phrases(8)
    improve_dishes = top_phrases(15)

    s15 = df[cols[15]].dropna().astype(str).str.strip().str.lower()
    no_complaint_pct = round(s15.isin(junk).sum() / len(s15) * 100, 1)

    def is_gibberish(t):
        letters = re.sub(r"[^a-zа-яёқғңөұүhі]", "", t.lower())
        if len(letters) < 8:
            return True
        return len(set(letters)) / len(letters) < 0.28

    raw17 = df[cols[17]].dropna().astype(str).str.strip()
    candidates, seen = [], set()
    for t in raw17:
        tl = t.lower()
        if tl in junk or len(t) < 20 or len(t) > 220 or is_gibberish(t):
            continue
        key = tl[:40]
        if key in seen:
            continue
        seen.add(key)
        candidates.append(t)
    candidates.sort(key=len, reverse=True)
    quotes = candidates[:8]

    return {
        "total": total,
        "date_min": date_min,
        "date_max": date_max,
        "overall_index": overall_index,
        "regular_pct": regular_pct,
        "satisfied_pct": satisfied_pct,
        "gi_summary": gi_summary,
        "no_complaint_pct": no_complaint_pct,
        "questions": questions,
        "top_dishes": top_dishes,
        "improve_dishes": improve_dishes,
        "quotes": quotes,
    }


data_path = Path(__file__).parent / DATA_FILE
if not data_path.exists():
    st.error(f"Не найден файл с данными: {DATA_FILE}. Положите его рядом с streamlit_app.py")
    st.stop()

d = prepare(str(data_path))


def section_head(title, note):
    st.markdown(
        f'<div class="sec-head"><span class="bar"></span><h2>{title}</h2></div>'
        f'<div class="sec-note">{note}</div>',
        unsafe_allow_html=True,
    )


PLOTLY_CFG = {"displayModeBar": False}

# ------------------------------------------------------------------ hero --
st.markdown(
    textwrap.dedent(f"""
    <div class="hero">
      <div>
        <div class="kicker">Опрос сотрудников · Столовая «Асхана»</div>
        <div class="hero-title">
          <span class="tri left"></span>
          <h1>Пульс столовой</h1>
          <span class="tri right"></span>
        </div>
        <div class="sub">Как сотрудники оценивают питание, сервис и чистоту — по {d['total']} анонимным анкетам.</div>
      </div>
      <div class="hero-chips">
        <span class="hero-chip">Ответов&nbsp;<b>{d['total']}</b></span>
        <span class="hero-chip">Период&nbsp;<b>{d['date_min'].strftime('%d.%m')}–{d['date_max'].strftime('%d.%m.%Y')}</b></span>
        <span class="hero-chip">Анкета&nbsp;<b>RU · KZ · EN</b></span>
      </div>
    </div>
    """),
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------- kpi --
gi_yes = d["gi_summary"]["yes"]
kpis = [
    ("Индекс удовлетворённости", d["overall_index"], "/100", "", "среднее по 9 критериям"),
    ("Регулярно пользуются столовой", d["regular_pct"], "%", "good", "оценка 4–5 из 5"),
    ("Полностью довольны питанием", d["satisfied_pct"], "%", "", "оценка 4–5 из 5"),
    ("Отмечают дискомфорт после еды", gi_yes, "%", "flag", "жалобы на ЖКТ"),
    ("Нет претензий к меню", d["no_complaint_pct"], "%", "good", "ответ «нет» / «всё устраивает»"),
]
st.markdown(
    '<div class="kpi-row">' + "".join(
        f'''<div class="kpi-card {cls}">
              <div class="kpi-label">{label}</div>
              <div class="kpi-value">{value}<small>{suffix}</small></div>
              <div class="kpi-foot">{foot}</div>
            </div>'''
        for label, value, suffix, cls, foot in kpis
    ) + "</div>",
    unsafe_allow_html=True,
)

st.divider()

# ------------------------------------------------------ diverging Likert --
section_head("Оценка по направлениям", "Доля ответов 1–5 по каждому вопросу — от слабых зон к сильным")

Q = d["questions"][::-1]  # weakest at the top of the horizontal bar chart
labels = [q["label"] for q in Q]
means = [q["mean"] for q in Q]

def seg(qs, key):
    return [q["pct"][key] for q in qs]

half3 = [q["pct"][3] / 2 for q in Q]
base1 = [-(h + q["pct"][2] + q["pct"][1]) for h, q in zip(half3, Q)]
base2 = [-(h + q["pct"][2]) for h, q in zip(half3, Q)]
base3 = [-h for h in half3]
base4 = [h for h in half3]
base5 = [h + q["pct"][4] for h, q in zip(half3, Q)]

fig = go.Figure()
trace_specs = [
    ("1 — совсем не согласны", 1, base1, NEG_1),
    ("2", 2, base2, NEG_2),
    ("3 — нейтрально", 3, base3, NEU_3),
    ("4", 4, base4, POS_4),
    ("5 — полностью согласны", 5, base5, POS_5),
]
for name, key, base, color in trace_specs:
    fig.add_trace(go.Bar(
        y=labels, x=seg(Q, key), base=base, orientation="h", name=name,
        marker=dict(color=color, line=dict(width=1, color=SURFACE)),
        hovertemplate="%{x}%% — оценка " + str(key) + "<br>%{y}<extra></extra>",
    ))

right_edges = [b5 + q["pct"][5] for b5, q in zip(base5, Q)]
label_x = max(right_edges) + 3.5
for lab, m in zip(labels, means):
    fig.add_annotation(x=label_x, y=lab, text=f"<b>{m:.2f}</b>", showarrow=False,
                        xanchor="left", font=dict(size=12.5, color=INK), xref="x", yref="y")

fig.update_layout(
    barmode="overlay", height=420, margin=dict(l=10, r=60, t=48, b=10),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color=CHART_TEXT, family="Public Sans, sans-serif"),
    bargap=0.32,
    legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0, font=dict(size=12, color=CHART_TEXT)),
    xaxis=dict(showticklabels=False, showgrid=False, zeroline=True, zerolinewidth=1, zerolinecolor="rgba(20,27,46,0.18)"),
    yaxis=dict(showgrid=False, color=CHART_TEXT),
)
with st.container(border=True):
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)

st.divider()

# ------------------------------------------------------------ dish panels --
section_head("Что говорят о меню", "Свободные ответы, сгруппированные по упоминаниям блюд")

col_a, col_b = st.columns(2)


def dish_chart(items, color_top, color_rest):
    items = items[::-1]  # so the largest ends up on top in a horizontal bar
    colors = [color_top if i == len(items) - 1 else color_rest for i in range(len(items))]
    fig = go.Figure(go.Bar(
        y=[i["label"] for i in items], x=[i["count"] for i in items], orientation="h",
        marker=dict(color=colors, cornerradius=5),
        text=[i["count"] for i in items], textposition="outside",
        textfont=dict(color=CHART_TEXT),
        hovertemplate="%{y}: <b>%{x}</b> упоминаний<extra></extra>",
    ))
    fig.update_layout(
        height=340, margin=dict(l=10, r=30, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CHART_TEXT, family="Public Sans, sans-serif"),
        bargap=0.35,
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showgrid=False, color=CHART_TEXT),
    )
    return fig


with col_a:
    with st.container(border=True):
        st.markdown("**Чаще всего хвалят**")
        st.caption("Топ-10 блюд · «какие блюда самые удачные»")
        st.plotly_chart(dish_chart(d["top_dishes"], DISH_A, DISH_B), width="stretch", config=PLOTLY_CFG)

with col_b:
    with st.container(border=True):
        st.markdown("**Просят доработать**")
        st.caption("Топ-10 блюд · «что нужно улучшить»")
        st.plotly_chart(dish_chart(d["improve_dishes"], FIX_A, FIX_B), width="stretch", config=PLOTLY_CFG)

st.divider()

# -------------------------------------------------------------- health --
section_head("Сигналы здоровья и питания", "Дискомфорт ЖКТ после еды и запрос на альтернативный рацион")

col_h1, col_h2 = st.columns([1, 1])
with col_h1:
    with st.container(border=True):
        st.markdown("**Дискомфорт ЖКТ после еды в столовой**")
        gi = d["gi_summary"]
        order = [
            ("Да, бывает дискомфорт", "yes", CRITICAL),
            ("Нет, не сталкивались", "no", GOOD),
            ("Ответ неясен / без ответа", "unclear", MUTED),
        ]
        fig = go.Figure(go.Pie(
            labels=[o[0] for o in order],
            values=[gi[o[1]] for o in order],
            hole=0.68,
            marker=dict(colors=[o[2] for o in order], line=dict(color=SURFACE, width=3)),
            textinfo="percent",
            textfont=dict(color="#ffffff", size=13, family="Manrope, sans-serif"),
            hovertemplate="%{label}: <b>%{value}%</b><extra></extra>",
            sort=False,
        ))
        fig.update_layout(
            height=280, margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=CHART_TEXT, family="Public Sans, sans-serif"),
            showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5, font=dict(size=11.5)),
            annotations=[dict(text=f"<b>{gi['yes']}%</b><br><span style='font-size:11px'>жалобы на ЖКТ</span>",
                               x=0.5, y=0.5, showarrow=False, font=dict(size=20, color=INK, family="Manrope, sans-serif"))],
        )
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CFG)

with col_h2:
    st.markdown(
        f'''<div class="side-card">
              <div class="kpi-value">{d['no_complaint_pct']}%</div>
              <div class="kpi-foot">сотрудников не назвали ни одного блюда, которое стоит убрать или
              доработать — прямых претензий к меню нет.</div>
            </div>''',
        unsafe_allow_html=True,
    )

st.divider()

# --------------------------------------------------------------- quotes --
section_head("Голос сотрудников", "Отобранные развёрнутые комментарии из открытого поля отзывов")

qcol1, qcol2 = st.columns(2)
for i, q in enumerate(d["quotes"]):
    target = qcol1 if i % 2 == 0 else qcol2
    target.markdown(f'<div class="quote-card">{q}</div>', unsafe_allow_html=True)

st.divider()
st.markdown(
    f'''<div class="foot-note">Источник: анонимный онлайн-опрос сотрудников о корпоративной столовой «Асхана» (RU/KZ/EN),
    {d['total']} ответов. Индекс удовлетворённости — среднее по девяти вопросам шкалы 1–5, приведённое к 0–100.
    Открытые ответы очищены от пустых и малоинформативных записей перед подсчётом упоминаний блюд.</div>''',
    unsafe_allow_html=True,
)

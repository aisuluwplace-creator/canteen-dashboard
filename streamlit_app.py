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

MONTHS = {
    "ru": ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
           "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
    "kz": ["", "Қаңтар", "Ақпан", "Наурыз", "Сәуір", "Мамыр", "Маусым",
           "Шілде", "Тамыз", "Қыркүйек", "Қазан", "Қараша", "Желтоқсан"],
    "en": ["", "January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
}

# ==================================================================== i18n --
LANGS = [("ru", "RU · Русский"), ("kz", "ҚАЗ · Қазақша"), ("en", "EN · English")]

T = {
    "hero_kicker": {"ru": "Satisfaction Survey · Прототип для обсуждения",
                    "kz": "Satisfaction Survey · Талқылауға арналған прототип",
                    "en": "Satisfaction Survey · Draft for review"},
    "hero_title": {"ru": "Опросы удовлетворённости", "kz": "Қанағаттану сауалнамалары", "en": "Satisfaction Surveys"},
    "hero_sub": {"ru": "Столовая, транспорт и медстраховка — сравнение текущей волны опроса с предыдущим периодом.",
                 "kz": "Асхана, тасымал және медсақтандыру — ағымдағы сауалнама толқынын алдыңғы кезеңмен салыстыру.",
                 "en": "Cafeteria, shuttle and medical insurance — comparing the current survey wave with a previous period."},
    "filter_current_period": {"ru": "Текущий период", "kz": "Ағымдағы кезең", "en": "Current period"},
    "filter_compare_period": {"ru": "Период сравнения", "kz": "Салыстыру кезеңі", "en": "Comparison period"},
    "filter_period_placeholder": {"ru": "Выберите период", "kz": "Кезеңді таңдаңыз", "en": "Select a period"},
    "filter_segment_placeholder": {"ru": "Все", "kz": "Барлығы", "en": "All"},
    "period_not_selected": {"ru": "период не выбран", "kz": "кезең таңдалмаған", "en": "no period selected"},
    "kpi_total": {"ru": "Анкет собрано всего", "kz": "Барлық жиналған анкета", "en": "Total responses collected"},
    "kpi_total_foot": {"ru": "за всё время сбора данных", "kz": "деректер жиналған уақыт бойы", "en": "across the entire collection period"},
    "kpi_current": {"ru": "Анкет за текущий период", "kz": "Ағымдағы кезеңдегі анкета", "en": "Responses — current period"},
    "kpi_compare": {"ru": "Анкет за период сравнения", "kz": "Салыстыру кезеңіндегі анкета", "en": "Responses — comparison period"},
    "kpi_delta": {"ru": "Изменение числа анкет", "kz": "Анкета санының өзгеруі", "en": "Change in responses"},
    "kpi_delta_foot": {"ru": "текущий период к периоду сравнения", "kz": "ағымдағы кезең салыстыру кезеңіне қатысты",
                        "en": "current period vs. comparison period"},
    "legend_current": {"ru": "Текущий период", "kz": "Ағымдағы кезең", "en": "Current period"},
    "legend_compare": {"ru": "Период сравнения", "kz": "Салыстыру кезеңі", "en": "Comparison period"},
    "sec_trend_title": {"ru": "Динамика количества ответов", "kz": "Жауаптар санының динамикасы", "en": "Response volume over time"},
    "sec_trend_note": {"ru": "Число заполненных анкет по месяцам за всю историю сбора (с учётом фильтра сегмента)",
                        "kz": "Барлық кезең бойынша айлар бойынша толтырылған анкеталар саны (сегмент сүзгісін ескере отырып)",
                        "en": "Number of completed responses per month across the whole history (segment filter applied)"},
    "trend_hover_suffix": {"ru": "анкет", "kz": "анкета", "en": "responses"},
    "sec_questions_title": {"ru": "Ответы по вопросам", "kz": "Сұрақтар бойынша жауаптар", "en": "Answers by question"},
    "sec_questions_note": {"ru": "Тёмно-синий столбец — текущий период, голубой — период сравнения. По вертикали — доля ответивших, в процентах",
                            "kz": "Қою көк баған — ағымдағы кезең, ашық көк — салыстыру кезеңі. Тік ось — жауап берушілер үлесі, пайызбен",
                            "en": "Dark-blue bar — current period, light-blue — comparison period. Vertical axis: share of respondents, %"},
    "axis_score": {"ru": "оценка (1–5)", "kz": "баға (1–5)", "en": "rating (1–5)"},
    "chart_series_current": {"ru": "Текущий", "kz": "Ағымдағы", "en": "Current"},
    "chart_series_compare": {"ru": "Сравнение", "kz": "Салыстыру", "en": "Comparison"},
    "answered_caption": {
        "ru": "На этот вопрос ответили: {cur} чел. за текущий период, {cmp} чел. за период сравнения",
        "kz": "Бұл сұраққа жауап бергендер: ағымдағы кезеңде {cur} адам, салыстыру кезеңінде {cmp} адам",
        "en": "Answered this question: {cur} people in the current period, {cmp} in the comparison period",
    },
    "sec_comments_title": {"ru": "Комментарии сотрудников", "kz": "Қызметкерлердің пікірлері", "en": "Employee comments"},
    "sec_comments_note": {
        "ru": "Пустые и малоинформативные ответы исключены; тональность определена по ключевым словам (эвристика)",
        "kz": "Бос және ақпараты аз жауаптар алынып тасталды; көңіл-күй түйінді сөздер бойынша анықталды (эвристика)",
        "en": "Empty and uninformative answers are excluded; sentiment is detected by keyword heuristics",
    },
    "comments_language_note": {
        "ru": "Сами комментарии показаны как есть, на языке автора — автоматический перевод мог бы исказить смысл.",
        "kz": "Пікірлердің өзі автордың тілінде, өзгеріссіз көрсетілген — автоматты аударма мағынаны бұрмалауы мүмкін.",
        "en": "Comments themselves are shown verbatim, in the author's original language — machine translation could distort meaning.",
    },
    "sentiment_title": {"ru": "Тональность комментариев", "kz": "Пікірлердің көңіл-күйі", "en": "Comment sentiment"},
    "sentiment_caption": {
        "ru": "Комментариев с текстом: {cur} за текущий период, {cmp} за период сравнения",
        "kz": "Мәтіні бар пікірлер: ағымдағы кезеңде {cur}, салыстыру кезеңінде {cmp}",
        "en": "Comments with text: {cur} in the current period, {cmp} in the comparison period",
    },
    "sent_pos": {"ru": "Позитив", "kz": "Оң", "en": "Positive"},
    "sent_neu": {"ru": "Нейтрально", "kz": "Бейтарап", "en": "Neutral"},
    "sent_neg": {"ru": "Негатив", "kz": "Теріс", "en": "Negative"},
    "comments_current_title": {"ru": "Комментарии за текущий период", "kz": "Ағымдағы кезеңнің пікірлері", "en": "Comments — current period"},
    "tab_positive": {"ru": "Позитивные", "kz": "Оң пікірлер", "en": "Positive"},
    "tab_negative": {"ru": "Негативные", "kz": "Теріс пікірлер", "en": "Negative"},
    "tab_neutral": {"ru": "Нейтральные", "kz": "Бейтарап пікірлер", "en": "Neutral"},
    "no_comments": {"ru": "Нет комментариев в этой категории за выбранный период.",
                    "kz": "Таңдалған кезеңде бұл санатта пікір жоқ.",
                    "en": "No comments in this category for the selected period."},
    "warn_no_file": {"ru": "Файл с данными для «{title}» не найден рядом со streamlit_app.py.",
                      "kz": "«{title}» үшін деректер файлы streamlit_app.py жанынан табылмады.",
                      "en": "No data file found for “{title}” next to streamlit_app.py."},
    "warn_no_dates": {"ru": "В файле нет распознаваемых дат.", "kz": "Файлда танылатын күндер жоқ.",
                       "en": "No recognizable dates found in the file."},
    "footer_note": {
        "ru": "Прототип для внутреннего обсуждения. Тональность комментариев определяется простым эвристическим "
              "анализом ключевых слов, а не полноценной NLP-моделью, и может ошибаться на сарказме и сложных "
              "формулировках — на следующих итерациях можно уточнить словарь или подключить более точную модель.",
        "kz": "Ішкі талқылауға арналған прототип. Пікірлердің көңіл-күйі толыққанды NLP-модель емес, түйінді "
              "сөздерге негізделген қарапайым эвристикамен анықталады және сарказм мен күрделі тұжырымдарда "
              "қателесуі мүмкін — келесі итерацияларда сөздікті нақтылауға немесе дәлірек модель қосуға болады.",
        "en": "Prototype for internal discussion. Comment sentiment is detected with a simple keyword heuristic, "
              "not a full NLP model, and can misread sarcasm or complex phrasing — later iterations could refine "
              "the wordlist or plug in a more accurate model.",
    },
}


def tr(key, lang, **kwargs):
    s = T[key][lang]
    return s.format(**kwargs) if kwargs else s


def L(d, lang):
    """Pick the localized string from a {'ru':..,'kz':..,'en':..} dict."""
    return d.get(lang, d.get("ru"))


st.markdown(
    textwrap.dedent(f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] {{ font-family:"Public Sans", system-ui, sans-serif; }}
      .stApp {{ background:{BG}; }}
      #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ visibility:hidden; height:0; }}
      [data-testid="stHeader"] {{ height:0; min-height:0; visibility:hidden; pointer-events:none; }}
      .block-container{{ padding-top:0; padding-bottom:3rem; max-width:1220px; }}
      h1,h2,h3,h4,h5 {{ font-family:"Manrope", system-ui, sans-serif; }}
      .st-key-lang{{ padding:14px 0 0; }}
      .st-key-lang div[role="radiogroup"]{{ gap:6px; flex-wrap:nowrap; justify-content:flex-end; }}
      .st-key-lang label{{
        background:{SURFACE}; border:1px solid {BORDER}; border-radius:8px; padding:4px 10px; white-space:nowrap;
      }}
      .st-key-lang label[data-selected="true"]{{ border-color:{NAVY}; background:{NAVY}; }}
      .st-key-lang label[data-selected="true"] p{{ color:#ffffff !important; }}
      .hero{{
        background:linear-gradient(135deg,{NAVY_DEEP} 0%,{NAVY} 62%,#2c418f 100%);
        margin:0 -1rem 24px; padding:22px 40px 24px;
        border-radius:0 0 22px 22px;
        display:flex; align-items:center; justify-content:space-between; gap:24px; flex-wrap:wrap;
        box-shadow:0 14px 30px -18px rgba(16,26,66,0.55);
      }}
      .hero .kicker{{ font-size:11.5px; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; color:{SKY}; margin-bottom:8px; }}
      .hero-title{{ display:flex; align-items:center; gap:14px; }}
      .hero-title .tri{{ width:0; height:0; flex:none; border-top:15px solid transparent; border-bottom:15px solid transparent; }}
      .hero-title .tri.left{{ border-left:20px solid {SKY}; }}
      .hero-title .tri.right{{ border-right:20px solid {SKY}; opacity:0.55; }}
      .hero-title h1{{ margin:0; color:#ffffff; font-size:32px; font-weight:800; letter-spacing:-0.01em; }}
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
      .lang-note {{ font-size:11.5px; color:{INK_MUTED}; margin:-6px 0 12px 15px; font-style:italic; }}
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
    label: dict           # {"ru":.., "kz":.., "en":..}
    kind: str              # "numeric15" or "categorical"
    categories: list = field(default_factory=list)   # canonical category keys, required for "categorical"
    normalize: object = None                          # fn(raw_str) -> canonical category | None


@dataclass
class Segment:
    col: int
    label: dict            # {"ru":.., "kz":.., "en":..}
    extract: object         # fn(raw_str) -> list[str] of tags


@dataclass
class SurveyConfig:
    key: str
    title: dict             # {"ru":.., "kz":.., "en":..}
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
        return "yes"
    if t.startswith("нет") or t.startswith("no") or t.startswith("жок"):
        return "no"
    return None


def prefix_normalize(order_ru, canon):
    prefixes = list(zip([p.lower() for p in order_ru], canon))

    def fn(raw):
        if pd.isna(raw):
            return None
        t = str(raw).strip().lower()
        for p_low, key in prefixes:
            if t.startswith(p_low):
                return key
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


# canonical category key -> localized label
CAT_LABELS = {
    "yes":     {"ru": "Да",       "kz": "Иә",        "en": "Yes"},
    "no":      {"ru": "Нет",      "kz": "Жоқ",       "en": "No"},
    "never":   {"ru": "Никогда",  "kz": "Ешқашан",   "en": "Never"},
    "rarely":  {"ru": "Редко",    "kz": "Сирек",     "en": "Rarely"},
    "sometimes": {"ru": "Иногда", "kz": "Кейде",     "en": "Sometimes"},
    "often":   {"ru": "Часто",    "kz": "Жиі",       "en": "Often"},
    "always":  {"ru": "Всегда",   "kz": "Әрқашан",   "en": "Always"},
}


def cat_label(key, lang):
    return CAT_LABELS[key][lang]


CANTEEN = SurveyConfig(
    key="canteen",
    title={"ru": "Столовая · Асхана", "kz": "Асхана", "en": "Cafeteria"},
    icon="🍲", file_glob="СТОЛОВАЯ*.xlsx", date_col=1,
    segment=Segment(col=6, label={"ru": "Локация столовой", "kz": "Асхана орналасуы", "en": "Cafeteria location"},
                     extract=extract_locations),
    questions=[
        Question(11, {"ru": "Вкус и качество блюд", "kz": "Тағамның дәмі мен сапасы", "en": "Taste & quality of food"}, "numeric15"),
        Question(12, {"ru": "Полезность питания", "kz": "Тағамның пайдалылығы", "en": "Healthiness of food"}, "numeric15"),
        Question(13, {"ru": "Чистота и гигиена", "kz": "Тазалық пен гигиена", "en": "Cleanliness & hygiene"}, "numeric15"),
        Question(14, {"ru": "Разнообразие меню", "kz": "Мәзірдің әртүрлілігі", "en": "Menu variety"}, "numeric15"),
        Question(15, {"ru": "Размер порций", "kz": "Порция көлемі", "en": "Portion size"}, "numeric15"),
        Question(17, {"ru": "Проблемы ЖКТ после еды", "kz": "Тамақтанғаннан кейінгі асқазан мәселелері", "en": "Digestive issues after eating"},
                 "categorical", ["yes", "no"], yn_normalize),
    ],
    comment_cols=[18],
)

TRANSPORT = SurveyConfig(
    key="transport",
    title={"ru": "Транспорт · Развозка", "kz": "Тасымал / Шаттл", "en": "Shuttle / Transport"},
    icon="🚐", file_glob="ТРАНСПОРТ*.xlsx", date_col=1,
    segment=Segment(col=6, label={"ru": "Маршрут", "kz": "Бағыт", "en": "Route"}, extract=extract_routes),
    questions=[
        Question(7, {"ru": "Место сбора", "kz": "Жиналу орны", "en": "Pick-up point"}, "numeric15"),
        Question(8, {"ru": "Пунктуальность", "kz": "Дәл уақыттылық", "en": "Punctuality"}, "numeric15"),
        Question(9, {"ru": "Охват маршрутов", "kz": "Маршруттардың қамтылуы", "en": "Route coverage"}, "numeric15"),
        Question(10, {"ru": "Достаточность мест", "kz": "Орын жеткіліктілігі", "en": "Seat availability"}, "numeric15"),
        Question(11, {"ru": "Безопасность", "kz": "Қауіпсіздік", "en": "Safety"}, "numeric15"),
        Question(12, {"ru": "Комфорт", "kz": "Жайлылық", "en": "Comfort"}, "numeric15"),
        Question(13, {"ru": "Соответствие расписанию", "kz": "Кестеге сәйкестік", "en": "Schedule adherence"}, "numeric15"),
    ],
    comment_cols=[14, 15],
)

DMS = SurveyConfig(
    key="dms",
    title={"ru": "Медстраховка · ДМС", "kz": "Медициналық сақтандыру", "en": "Medical Insurance"},
    icon="🩺", file_glob="МЕДИЦИНСКАЯ*.xlsx", date_col=1,
    segment=None,
    questions=[
        Question(7, {"ru": "Пользовались страховкой за 12 мес.", "kz": "Соңғы 12 айда сақтандыруды қолдандыңыз ба",
                      "en": "Used insurance in the last 12 months"}, "categorical", ["yes", "no"], yn_normalize),
        Question(11, {"ru": "Частота доплат сверх покрытия", "kz": "Қамтудан тыс қосымша төлем жиілігі",
                       "en": "Frequency of out-of-pocket payments"}, "categorical",
                 ["never", "rarely", "sometimes", "often", "always"],
                 prefix_normalize(["Никогда", "Редко", "Иногда", "Часто", "Всегда"],
                                   ["never", "rarely", "sometimes", "often", "always"])),
        Question(14, {"ru": "Удовлетворённость услугами", "kz": "Қызметке қанағаттану деңгейі", "en": "Satisfaction with services"}, "numeric15"),
        Question(15, {"ru": "Время ожидания услуги", "kz": "Қызметті күту уақыты", "en": "Waiting time for service"}, "numeric15"),
        Question(17, {"ru": "Откладывали лечение из-за лимитов", "kz": "Шектеулерге байланысты емдеуді кейінге қалдыру",
                       "en": "Delayed treatment due to coverage limits"}, "categorical", ["yes", "no"], yn_normalize),
        Question(19, {"ru": "Обращались за ночной помощью", "kz": "Түнгі көмекке жүгіну", "en": "Used night-time care"},
                 "categorical", ["yes", "no"], yn_normalize),
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
    return sorted(periods)


def period_label(p, lang):
    return f"{MONTHS[lang][p.month]} {p.year}"


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
    fig = go.Figure(go.Bar(
        x=[fmt(p) for p in periods], y=monthly.values,
        marker=dict(color=bar_colors, cornerradius=4),
        text=monthly.values, textposition="outside", textfont=dict(color=CHART_TEXT),
        hovertemplate="%{x}: <b>%{y}</b> " + hover_suffix + "<extra></extra>",
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
    choice = st.radio(
        "Language", [code for code, _ in LANGS], index=[c for c, _ in LANGS].index(st.session_state["lang"]),
        format_func=lambda c: dict(LANGS)[c], horizontal=True, label_visibility="collapsed", key="lang",
    )

LANG = st.session_state["lang"]

# ------------------------------------------------------------------ hero --
st.markdown(
    textwrap.dedent(f"""
    <div class="hero">
      <div>
        <div class="kicker">{tr('hero_kicker', LANG)}</div>
        <div class="hero-title">
          <span class="tri left"></span>
          <h1>{tr('hero_title', LANG)}</h1>
          <span class="tri right"></span>
        </div>
        <div class="sub">{tr('hero_sub', LANG)}</div>
      </div>
    </div>
    """),
    unsafe_allow_html=True,
)

tabs = st.tabs([f"{s.icon} {L(s.title, LANG)}" for s in SURVEYS])
for tab, cfg in zip(tabs, SURVEYS):
    with tab:
        render_survey(cfg, LANG)

st.divider()
st.markdown(f'<div class="foot-note">{tr("footer_note", LANG)}</div>', unsafe_allow_html=True)

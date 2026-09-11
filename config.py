"""Конфигурация дашборда: палитра, описание опросов, пороги.

Все настройки, которые могут меняться без правки логики, лежат здесь.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent

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


# ------------------------------------------------------------ normalizers --
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


# ------------------------------------------------------------------ surveys --
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

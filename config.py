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

# ------------------------------------------------------------------ пороги --
# Волна опроса — месяц, в котором собрано не меньше этого числа анкет
# (одиночные ответы в «хвостовых» месяцах волной не считаются).
MIN_WAVE_SIZE = 30

# Статистическая значимость различий между периодами
SIGNIFICANCE_ALPHA = 0.05       # порог p-value
MIN_N_FOR_TEST = 30             # меньше ответов в любом из периодов — «мало данных для сравнения»

# Пороги правил для блока «Ключевые выводы»
NEGATIVE_SHARE_ALERT = 30.0     # доля негативных ответов (%), выше которой вопрос попадает в выводы
POLARIZATION_PP = 3.0           # одновременный рост долей «1» и «5» больше чем на столько п.п. — поляризация
INSIGHTS_MAX = 5                # максимум выводов в блоке

# Оценки 1–5: какие считаем «довольными» и «недовольными»
SATISFIED_SCORES = (4, 5)
DISSATISFIED_SCORES = (1, 2)

MONTHS = {
    "ru": ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
           "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
    "kz": ["", "Қаңтар", "Ақпан", "Наурыз", "Сәуір", "Мамыр", "Маусым",
           "Шілде", "Тамыз", "Қыркүйек", "Қазан", "Қараша", "Желтоқсан"],
    "en": ["", "January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
}


# ============================================================== data model --
@dataclass(eq=False)   # eq=False — чтобы Question можно было использовать как ключ словаря
class Question:
    col: int
    label: dict           # {"ru":.., "kz":.., "en":..}
    kind: str              # "numeric15" or "categorical"
    categories: list = field(default_factory=list)   # canonical category keys, required for "categorical"
    normalize: object = None                          # fn(raw_str) -> canonical category | None
    # для categorical: варианты ответа, которые считаем негативным сигналом (например, «Да» на вопрос о проблемах).
    # Пустой список — у вопроса нет негативного варианта, он не участвует в выборе проблемной метрики.
    negative: list = field(default_factory=list)


@dataclass
class Gate:
    """Условный блок анкеты: вопросы ниже показывались только тем, кто ответил `category` на вопрос `col`."""
    col: int
    category: str
    block_col: int          # колонка, по которой считаем число ответивших на условный блок


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
    # Главный вопрос удовлетворённости (колонка со шкалой 1–5). None — сводный балл:
    # среднее всех оценок 1–5 по всем критериям раздела.
    satisfaction_col: object = None
    # Главная проблемная метрика (колонка). None — выбирается автоматически: вопрос с
    # наибольшей долей негативных ответов (оценки 1–2 или негативный вариант ответа).
    problem_col: object = None
    gate: object = None     # Gate или None


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


def keyword_normalize(mapping):
    """Категория по ключевому слову внутри текста ответа (для вариантов вида «RU: … KZ: … EN: …»)."""
    pairs = [(k.lower(), v) for k, v in mapping]

    def fn(raw):
        if pd.isna(raw):
            return None
        t = str(raw).lower()
        for kw, key in pairs:
            if kw in t:
                return key
        return None
    return fn


# canonical category key -> localized label
CAT_LABELS = {
    "yes":     {"ru": "Да",       "kz": "Иә",        "en": "Yes"},
    "no":      {"ru": "Нет",      "kz": "Жоқ",       "en": "No"},
    "never":   {"ru": "Никогда",  "kz": "Ешқашан",   "en": "Never"},
    "rarely":  {"ru": "Редко",    "kz": "Сирек",     "en": "Rarely"},
    "sometimes": {"ru": "Иногда", "kz": "Кейде",     "en": "Sometimes"},
    "often":   {"ru": "Часто",    "kz": "Жиі",       "en": "Often"},
    "always":  {"ru": "Всегда",   "kz": "Әрқашан",   "en": "Always"},
    # варианты вопроса «Что улучшить?» (транспорт)
    "imp_pickup":      {"ru": "Место сбора",       "kz": "Жиналу орны",        "en": "Pick-up point"},
    "imp_routes":      {"ru": "Охват маршрутов",   "kz": "Бағыттар қамтылуы",  "en": "Route coverage"},
    "imp_capacity":    {"ru": "Места",             "kz": "Орындар",            "en": "Seats"},
    "imp_punctuality": {"ru": "Пунктуальность",    "kz": "Дәл уақыттылық",     "en": "Punctuality"},
    "imp_schedule":    {"ru": "Расписание",        "kz": "Кесте",              "en": "Schedule"},
    "imp_comfort":     {"ru": "Комфорт",           "kz": "Жайлылық",           "en": "Comfort"},
    "imp_safety":      {"ru": "Безопасность",      "kz": "Қауіпсіздік",        "en": "Safety"},
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
                 "categorical", ["yes", "no"], yn_normalize, negative=["yes"]),
    ],
    comment_cols=[18],
    satisfaction_col=None,   # явного вопроса об общей удовлетворённости нет — сводный балл по всем критериям
    problem_col=None,        # авто-выбор по доле негативных ответов
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
        # колонка 14 — выбор одного из 7 вариантов, а не свободный текст (раньше ошибочно считалась комментарием)
        Question(14, {"ru": "Что улучшить в первую очередь", "kz": "Бірінші кезекте нені жақсарту керек", "en": "What to improve first"},
                 "categorical",
                 ["imp_pickup", "imp_routes", "imp_capacity", "imp_punctuality", "imp_schedule", "imp_comfort", "imp_safety"],
                 keyword_normalize([("место сбор", "imp_pickup"), ("охват", "imp_routes"), ("достаточность", "imp_capacity"),
                                    ("пунктуальность", "imp_punctuality"), ("соответствие", "imp_schedule"),
                                    ("комфорт", "imp_comfort"), ("безопасность", "imp_safety")])),
    ],
    comment_cols=[15],
    satisfaction_col=None,   # явного вопроса об общей удовлетворённости нет — сводный балл по всем критериям
    problem_col=None,        # авто-выбор по доле негативных ответов
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
                                   ["never", "rarely", "sometimes", "often", "always"]),
                 negative=["often", "always"]),
        Question(14, {"ru": "Удовлетворённость услугами", "kz": "Қызметке қанағаттану деңгейі", "en": "Satisfaction with services"}, "numeric15"),
        Question(15, {"ru": "Время ожидания услуги", "kz": "Қызметті күту уақыты", "en": "Waiting time for service"}, "numeric15"),
        Question(17, {"ru": "Откладывали лечение из-за лимитов", "kz": "Шектеулерге байланысты емдеуді кейінге қалдыру",
                       "en": "Delayed treatment due to coverage limits"}, "categorical", ["yes", "no"], yn_normalize,
                 negative=["yes"]),
        Question(19, {"ru": "Обращались за ночной помощью", "kz": "Түнгі көмекке жүгіну", "en": "Used night-time care"},
                 "categorical", ["yes", "no"], yn_normalize),
    ],
    comment_cols=[21],
    satisfaction_col=14,     # «Насколько вы удовлетворены предоставляемыми услугами медстраховки?»
    problem_col=17,          # «Откладывали лечение из-за лимитов» — доля «Да»
    # блок о качестве услуг заполняли только те, кто пользовался страховкой за 12 мес.
    gate=Gate(col=7, category="yes", block_col=14),
)

SURVEYS = [CANTEEN, TRANSPORT, DMS]


# ------------------------------------------------------- подписи концов шкал --
# Что означают 1 и 5 в каждом вопросе со шкалой. В данных расшифровки нет (хранятся только числа),
# поэтому подписи заданы только там, где это однозначно следует из текста вопроса
# («Насколько вы довольны…»). None — показать подпись нельзя, требуется уточнение (TODO).
# Ключ: (ключ раздела, номер колонки).
SCALE_LABELS = {
    # Столовая — TODO: уточнить формулировку шкалы в анкете (в тексте вопроса её нет)
    ("canteen", 11): None,   # Вкус и качество блюд
    ("canteen", 12): None,   # Полезность питания
    ("canteen", 13): None,   # Чистота и гигиена
    ("canteen", 14): None,   # Разнообразие меню
    ("canteen", 15): None,   # Размер порций
    # Транспорт
    ("transport", 7): {"ru": "1 — совсем не довольны, 5 — полностью довольны",       # из текста «Насколько вы довольны местом сбора?»
                       "kz": "1 — мүлдем қанағаттанбайсыз, 5 — толық қанағаттанасыз",
                       "en": "1 — not satisfied at all, 5 — fully satisfied"},
    ("transport", 8): None,  # Пунктуальность — TODO
    ("transport", 9): None,  # Охват маршрутов — TODO
    ("transport", 10): None, # Достаточность мест — TODO
    ("transport", 11): None, # Безопасность — TODO
    ("transport", 12): None, # Комфорт — TODO
    ("transport", 13): None, # Соответствие расписанию — TODO
    # ДМС
    ("dms", 14): {"ru": "1 — совсем не удовлетворены, 5 — полностью удовлетворены",  # из текста «Насколько вы удовлетворены…»
                  "kz": "1 — мүлдем қанағаттанбайсыз, 5 — толық қанағаттанасыз",
                  "en": "1 — not satisfied at all, 5 — fully satisfied"},
    ("dms", 15): None,       # Время ожидания услуги — TODO: 1 — очень долго, 5 — быстро? Из данных не следует.
}

# Цвета сегментов 100%-полосы для шкалы 1–5 (сочетаются с тёмно-синей палитрой)
SCALE_COLORS = {1: "#b3382a", 2: "#ee8f7f", 3: "#cfd3dc", 4: "#7ccba1", 5: "#1f9d55"}
SCALE_TEXT_COLORS = {1: "#ffffff", 2: "#3a1a15", 3: "#4a5573", 4: "#123d27", 5: "#ffffff"}
MIN_SEGMENT_LABEL_PCT = 5.0   # не подписывать сегменты меньше этой доли


# ------------------------------------------------------------ комментарии --
DATA_DIR = BASE_DIR / "data"
COMMENTS_SCORED_PATH = DATA_DIR / "comments_scored.csv"     # результат scripts/score_comments.py
MODEL_METRICS_PATH = DATA_DIR / "model_metrics.json"        # результат scripts/evaluate.py
MANUAL_LABELS_PATH = DATA_DIR / "manual_labels.csv"         # шаблон ручной разметки

MIN_COMMENT_LEN = 25          # короче — считаем общей оценкой без деталей, в ленту не выводим
MAX_FEED_COMMENTS = 12        # сколько комментариев показывать в ленте
ANONYMITY_MIN_GROUP = 5       # сегмент меньше этого числа анкет не показываем
TOPIC_SIM_THRESHOLD = 0.40    # косинусная близость к описанию темы ниже порога → «Прочее»
OTHER_TOPIC = "other"
GENERAL_TOPIC = "general"

# Модели офлайн-скрипта (не входят в requirements.txt приложения, см. requirements-dev.txt)
SENTIMENT_MODEL_RU = "blanchefort/rubert-base-cased-sentiment"
SENTIMENT_MODEL_MULTI = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
KAZAKH_LETTERS = re.compile(r"[әғқңөұүһі]", re.I)

# Темы комментариев по разделам: ключ, подпись, описание для сопоставления эмбеддингов.
# Описание — на русском (модель мультиязычная, казахские комментарии сопоставляются с ним же).
TOPICS = {
    "canteen": [
        ("taste", {"ru": "Вкус и качество блюд", "kz": "Тағамның дәмі мен сапасы", "en": "Taste & quality"},
         "невкусно, вкус еды, качество блюд, холодная еда, пересолено, много приправ, сырое, застоявшиеся салаты"),
        ("menu", {"ru": "Разнообразие меню", "kz": "Мәзірдің әртүрлілігі", "en": "Menu variety"},
         "разнообразить меню, одно и то же, добавить блюда, национальная кухня, фрукты и овощи, десерты, диетическое питание"),
        ("water", {"ru": "Вода, чай и компот", "kz": "Су, шай және компот", "en": "Water, tea & drinks"},
         "вода с хлоркой, чай пахнет хлором, компот невкусный, фильтр для воды, напитки"),
        ("portions", {"ru": "Размер порций", "kz": "Порция көлемі", "en": "Portion size"},
         "маленькие порции, мало еды, не хватает порции, добавить порцию, порции побольше"),
        ("hygiene", {"ru": "Чистота и санитария", "kz": "Тазалық және санитария", "en": "Cleanliness"},
         "грязно, тараканы, посторонние предметы в еде, волосы в еде, чистота посуды, гигиена, санитария"),
        ("queue", {"ru": "Очереди и обслуживание", "kz": "Кезек және қызмет көрсету", "en": "Queues & service"},
         "большая очередь, долго ждать, мало кассиров, время обеда, не успеваем поесть, грубый персонал, обслуживание"),
        ("health", {"ru": "Самочувствие после еды", "kz": "Тамақтан кейінгі көңіл-күй", "en": "Digestive issues"},
         "проблемы с желудком, изжога, отравление, расстройство ЖКТ, плохо после еды, жирная еда"),
        ("price", {"ru": "Стоимость и оплата", "kz": "Құны және төлем", "en": "Price & payment"},
         "дорого, удерживают деньги за питание, оплата, компенсация, стоимость обеда"),
        (GENERAL_TOPIC, {"ru": "Общая оценка без деталей", "kz": "Жалпы баға", "en": "General remark"},
         "всё хорошо, всё устраивает, спасибо, отлично, нормально, нет замечаний, всё нравится"),
    ],
    "transport": [
        ("schedule", {"ru": "Расписание и время отправления", "kz": "Кесте және жүру уақыты", "en": "Schedule & departure time"},
         "время отправления, слишком рано выезжает, расписание смен, ночная смена, поздно приезжает, изменить время"),
        ("punctuality", {"ru": "Пунктуальность и ожидание", "kz": "Дәл уақыттылық және күту", "en": "Punctuality & waiting"},
         "опаздывает, уезжает раньше, не приезжает, долго ждать на холоде, автобус снимают с маршрута"),
        ("routes", {"ru": "Маршруты и остановки", "kz": "Бағыттар мен аялдамалар", "en": "Routes & stops"},
         "продлить маршрут, добавить остановку, не проезжает через наш район, охват маршрутов, новый маршрут, далеко идти"),
        ("capacity", {"ru": "Места и вместимость", "kz": "Орын және сыйымдылық", "en": "Seats & capacity"},
         "не хватает мест, автобус переполнен, стоя едем, маленький автобус, нужен большой автобус"),
        ("comfort", {"ru": "Комфорт и состояние транспорта", "kz": "Жайлылық және көлік жағдайы", "en": "Comfort & vehicle condition"},
         "старый автобус, холодно в салоне, жарко, грязно, неудобные сиденья, новый автобус, кондиционер, ремни"),
        ("drivers", {"ru": "Водители и безопасность", "kz": "Жүргізушілер және қауіпсіздік", "en": "Drivers & safety"},
         "водитель грубый, быстро едет, нарушает ПДД, вежливые водители, аккуратно водит, безопасность"),
        ("pickup", {"ru": "Место сбора", "kz": "Жиналу орны", "en": "Pick-up point"},
         "место сбора неудобное, далеко до остановки, ждать после смены, место посадки, стоянка"),
        (GENERAL_TOPIC, {"ru": "Общая оценка без деталей", "kz": "Жалпы баға", "en": "General remark"},
         "всё хорошо, всё устраивает, спасибо, отлично, нормально, нет претензий, не пользуюсь развозкой"),
    ],
    "dms": [
        ("limits", {"ru": "Лимиты и покрытие", "kz": "Лимиттер және қамту", "en": "Limits & coverage"},
         "маленький лимит, не покрывает, мало денег на стоматологию, расширить покрытие, добавить услуги в страховку, анализы платно"),
        ("queues", {"ru": "Очереди и запись", "kz": "Кезек және жазылу", "en": "Queues & appointments"},
         "долго ждать записи, очередь, не могут записать, ожидание приёма, долго согласовывают"),
        ("clinics", {"ru": "Клиники и врачи", "kz": "Емханалар және дәрігерлер", "en": "Clinics & doctors"},
         "врач отказался принимать, плохие клиники, сменить медцентр, нет нужных специалистов, отношение врачей, филиал"),
        ("drugs", {"ru": "Лекарства", "kz": "Дәрі-дәрмек", "en": "Medicines"},
         "лекарства, препараты, замена на дженерик, выдали лекарство, рецепт, аптека"),
        ("copay", {"ru": "Возмещение и доплаты", "kz": "Өтемақы және қосымша төлем", "en": "Reimbursement & co-pay"},
         "пришлось доплачивать, за всё платить, возмещение расходов, вернуть деньги, из своего кармана"),
        (GENERAL_TOPIC, {"ru": "Общая оценка без деталей", "kz": "Жалпы баға", "en": "General remark"},
         "всё хорошо, спасибо, доволен страховкой, отлично, нормально, нет замечаний"),
    ],
}
OTHER_TOPIC_LABEL = {"ru": "Прочее", "kz": "Басқа", "en": "Other"}


def topic_label(survey_key, topic_key, lang):
    if topic_key == OTHER_TOPIC:
        return OTHER_TOPIC_LABEL.get(lang, OTHER_TOPIC_LABEL["ru"])
    for key, label, _ in TOPICS.get(survey_key, []):
        if key == topic_key:
            return label.get(lang, label["ru"])
    return topic_key

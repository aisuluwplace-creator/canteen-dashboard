"""Тексты интерфейса на трёх языках (RU — основной)."""


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

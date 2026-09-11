"""Тексты интерфейса на трёх языках (RU — основной)."""


LANGS = [("ru", "RU · Русский"), ("kz", "ҚАЗ · Қазақша"), ("en", "EN · English")]

T = {
    "hero_kicker": {"ru": "Опросы сотрудников · Прототип для обсуждения",
                    "kz": "Қызметкерлер сауалнамасы · Талқылауға арналған прототип",
                    "en": "Employee surveys · Draft for review"},
    "hero_updated": {"ru": "Данные обновлены", "kz": "Деректер жаңартылды", "en": "Data updated"},
    "hero_last_wave": {"ru": "Последняя волна опроса", "kz": "Сауалнаманың соңғы толқыны", "en": "Latest survey wave"},
    "last_wave_desc": {"ru": "Последняя волна: {period}", "kz": "Соңғы толқын: {period}", "en": "Latest wave: {period}"},
    "compare_desc": {"ru": "Сравнение: {period}", "kz": "Салыстыру: {period}", "en": "Comparison: {period}"},
    "hero_title": {"ru": "Опросы удовлетворённости", "kz": "Қанағаттану сауалнамалары", "en": "Satisfaction Surveys"},
    "hero_sub": {"ru": "Столовая, транспорт и медстраховка — сравнение последней волны опроса с предыдущим периодом.",
                 "kz": "Асхана, тасымал және медсақтандыру — сауалнаманың соңғы толқынын алдыңғы кезеңмен салыстыру.",
                 "en": "Cafeteria, shuttle and medical insurance — comparing the latest survey wave with a previous period."},
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
    "kpi_delta_foot": {"ru": "к периоду сравнения", "kz": "салыстыру кезеңіне қатысты", "en": "vs. comparison period"},
    "sec_trend_title": {"ru": "Динамика количества ответов", "kz": "Жауаптар санының динамикасы", "en": "Response volume over time"},
    "sec_trend_note": {"ru": "Число заполненных анкет по месяцам за всю историю сбора (с учётом фильтра сегмента)",
                        "kz": "Барлық кезең бойынша айлар бойынша толтырылған анкеталар саны (сегмент сүзгісін ескере отырып)",
                        "en": "Number of completed responses per month across the whole history (segment filter applied)"},
    "trend_hover_suffix": {"ru": "анкет", "kz": "анкета", "en": "responses"},
    "sec_questions_title": {"ru": "Ответы по вопросам", "kz": "Сұрақтар бойынша жауаптар", "en": "Answers by question"},
    "sec_questions_note": {"ru": "Тёмно-синий столбец — {cur}, голубой — {cmp}. По вертикали — доля ответивших, в процентах",
                            "kz": "Қою көк баған — {cur}, ашық көк — {cmp}. Тік ось — жауап берушілер үлесі, пайызбен",
                            "en": "Dark-blue bar — {cur}, light-blue — {cmp}. Vertical axis: share of respondents, %"},
    "axis_score": {"ru": "Оценка (1–5)", "kz": "Баға (1–5)", "en": "Rating (1–5)"},
    "hover_share": {"ru": "Доля", "kz": "Үлес", "en": "Share"},
    "answered_caption": {
        "ru": "На этот вопрос ответили: {cur} чел. — {cur_p}; {cmp} чел. — {cmp_p}",
        "kz": "Бұл сұраққа жауап бергендер: {cur} адам — {cur_p}; {cmp} адам — {cmp_p}",
        "en": "Answered this question: {cur} people — {cur_p}; {cmp} people — {cmp_p}",
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
        "ru": "Комментариев с текстом: {cur} — {cur_p}; {cmp} — {cmp_p}",
        "kz": "Мәтіні бар пікірлер: {cur} — {cur_p}; {cmp} — {cmp_p}",
        "en": "Comments with text: {cur} — {cur_p}; {cmp} — {cmp_p}",
    },
    # единые названия категорий тональности — везде в этом порядке
    "sent_pos": {"ru": "Позитивные", "kz": "Оң пікірлер", "en": "Positive"},
    "sent_neu": {"ru": "Нейтральные", "kz": "Бейтарап пікірлер", "en": "Neutral"},
    "sent_neg": {"ru": "Негативные", "kz": "Теріс пікірлер", "en": "Negative"},
    "comments_current_title": {"ru": "Комментарии — {period}", "kz": "Пікірлер — {period}", "en": "Comments — {period}"},
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

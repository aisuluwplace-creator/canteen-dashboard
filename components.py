"""Переиспользуемые визуальные компоненты: стили, шапка, карточки, заголовки секций."""
import textwrap

import streamlit as st

from config import (BG, BORDER, CARD_SHADOW, COMPARE_COLOR, CRITICAL, GOOD, INK, INK_2, INK_MUTED,
                    NAVY, NAVY_DEEP, NEG_SENT, POS_SENT, SKY, SURFACE, WARN)
from i18n import tr
from stats import LOW_N, NO_COMPARE, NOT_SIGNIFICANT, SIGNIFICANT


def inject_css():
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
          .hero-title h1{{ margin:0; color:#ffffff; font-size:32px; font-weight:800; letter-spacing:-0.01em; }}
          .hero .sub{{ color:#c7d3f4; font-size:13.5px; margin-top:8px; max-width:56ch; }}
          .hero-meta{{ display:flex; flex-direction:column; gap:10px; align-items:flex-end; text-align:right; flex:none; }}
          .hero-meta .meta-item{{ background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.14);
                                  border-radius:10px; padding:8px 14px; min-width:220px; }}
          .hero-meta .meta-label{{ font-size:10.5px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:{SKY}; }}
          .hero-meta .meta-value{{ font-family:"Manrope",sans-serif; font-size:15px; font-weight:700; color:#ffffff; margin-top:2px; }}
          @media (max-width:760px){{ .hero-meta{{ align-items:flex-start; text-align:left; }} }}
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
          .kpi-card.neutral{{ border-left-color:{INK_MUTED}; }}
          .kpi-card .kpi-label{{ font-size:11px; font-weight:700; letter-spacing:0.04em; text-transform:uppercase; color:{INK_MUTED}; line-height:1.4; min-height:28px; }}
          .kpi-card .kpi-value{{ font-family:"Manrope",sans-serif; font-size:28px; font-weight:800; color:{INK}; letter-spacing:-0.01em; }}
          .kpi-card .kpi-value small{{ font-size:13px; font-weight:600; color:{INK_MUTED}; margin-left:2px; }}
          .kpi-card .kpi-foot{{ font-size:11.5px; color:{INK_MUTED}; }}
          .kpi-delta{{ display:flex; align-items:baseline; gap:8px; flex-wrap:wrap; font-size:12.5px; font-weight:700; color:{INK_2}; }}
          .kpi-delta .sig{{ font-size:11px; font-weight:500; color:{INK_MUTED}; }}
          .kpi-delta.good{{ color:{GOOD}; }}
          .kpi-delta.bad{{ color:{CRITICAL}; }}
          .kpi-delta.muted{{ color:{INK_MUTED}; font-weight:600; }}
          .delta-line{{ font-size:12.5px; color:{INK_2}; margin:-6px 0 6px; display:flex; gap:8px; align-items:baseline; flex-wrap:wrap; }}
          .delta-line b{{ color:{INK}; }}
          .delta-line .d{{ font-weight:700; }}
          .delta-line .d.good{{ color:{GOOD}; }}
          .delta-line .d.bad{{ color:{CRITICAL}; }}
          .delta-line .d.muted{{ color:{INK_MUTED}; font-weight:600; }}
          .delta-line .sig{{ font-size:11px; color:{INK_MUTED}; }}
          .yn-card{{ display:flex; flex-direction:column; gap:6px; padding:6px 2px 2px; }}
          .yn-card .yn-value{{ font-family:"Manrope",sans-serif; font-size:44px; font-weight:800; color:{INK}; line-height:1; letter-spacing:-0.02em; }}
          .yn-card .yn-value.flag{{ color:{CRITICAL}; }}
          .yn-card .yn-label{{ font-size:13px; color:{INK_2}; }}
          .yn-card .yn-cmp{{ font-size:12px; color:{INK_MUTED}; }}
          .scale-note{{ font-size:11.5px; color:{INK_MUTED}; margin:-4px 0 4px; }}
          .pill-wrap{{ display:flex; flex-wrap:wrap; gap:6px; margin:4px 0 10px; }}
          .pill{{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:999px; padding:3px 10px; font-size:12px; color:{INK_2}; }}
          .pill b{{ color:{INK}; margin-left:4px; }}
          .pill.pos{{ border-color:{POS_SENT}; }}
          .pill.neg{{ border-color:{NEG_SENT}; }}
          .counts-line{{ font-size:12px; color:{INK_MUTED}; margin:-4px 0 10px 2px; }}
          .insights{{ background:{SURFACE}; border:1px solid {BORDER}; border-left:4px solid {NAVY}; border-radius:12px;
                      box-shadow:{CARD_SHADOW}; padding:14px 18px 10px; margin:4px 0 18px; }}
          .insights ul{{ margin:0; padding-left:0; list-style:none; }}
          .insights li{{ font-size:13.5px; color:{INK}; line-height:1.5; padding:5px 0 5px 22px; position:relative; }}
          .insights li::before{{ content:""; position:absolute; left:4px; top:12px; width:9px; height:9px; border-radius:50%; background:{INK_MUTED}; }}
          .insights li.neg::before{{ background:{CRITICAL}; }}
          .insights li.alert::before{{ background:{WARN}; }}
          .insights li.polar::before{{ background:{SKY}; }}
          .insights li.pos::before{{ background:{GOOD}; }}
          .insights li.neutral{{ color:{INK_2}; }}
          .ov-row{{ display:grid; grid-template-columns:repeat(3,minmax(220px,1fr)); gap:16px; margin:4px 0 12px; }}
          @media (max-width:900px){{ .ov-row{{ grid-template-columns:1fr; }} }}
          .ov-card{{ background:{SURFACE}; border:1px solid {BORDER}; border-top:4px solid {NAVY}; border-radius:14px;
                     box-shadow:{CARD_SHADOW}; padding:18px 20px 14px; display:flex; flex-direction:column; gap:10px; }}
          .ov-card.flag{{ border-top-color:{CRITICAL}; }}
          .ov-card.good{{ border-top-color:{GOOD}; }}
          .ov-card .ov-title{{ font-family:"Manrope",sans-serif; font-size:17px; font-weight:800; color:{INK}; }}
          .ov-card .ov-sub{{ font-size:11.5px; color:{INK_MUTED}; margin-top:-6px; }}
          .ov-card .ov-value{{ font-family:"Manrope",sans-serif; font-size:40px; font-weight:800; color:{INK}; line-height:1; letter-spacing:-0.02em; }}
          .ov-card .ov-value small{{ font-size:14px; font-weight:600; color:{INK_MUTED}; margin-left:4px; }}
          .ov-card .ov-label{{ font-size:11px; font-weight:700; letter-spacing:0.05em; text-transform:uppercase; color:{INK_MUTED}; }}
          .ov-card .ov-problem{{ font-size:13px; color:{INK}; line-height:1.45; }}
          .ov-card .ov-problem b{{ color:{CRITICAL}; }}
          .ov-card .ov-link{{ font-size:11.5px; color:{SKY}; font-weight:600; border-top:1px solid {BORDER}; padding-top:10px; margin-top:auto; }}
          .kpi-card.flag .kpi-value{{ color:{CRITICAL}; }}
          .kpi-card.good .kpi-value{{ color:{GOOD}; }}
          .kpi-card.compare .kpi-value{{ color:{COMPARE_COLOR}; }}
          .kpi-card.neutral .kpi-value{{ color:{INK_2}; }}
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


def hero(lang, updated_text, last_wave_text):
    """Баннер: заголовок слева, дата обновления данных и последняя волна — справа."""
    st.markdown(
        textwrap.dedent(f"""
        <div class="hero">
          <div>
            <div class="kicker">{tr('hero_kicker', lang)}</div>
            <div class="hero-title"><h1>{tr('hero_title', lang)}</h1></div>
            <div class="sub">{tr('hero_sub', lang)}</div>
          </div>
          <div class="hero-meta">
            <div class="meta-item">
              <div class="meta-label">{tr('hero_updated', lang)}</div>
              <div class="meta-value">{updated_text}</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">{tr('hero_last_wave', lang)}</div>
              <div class="meta-value">{last_wave_text}</div>
            </div>
          </div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def section_head(title, note):
    st.markdown(
        f'<div class="sec-head"><span class="bar"></span><h2>{title}</h2></div>'
        f'<div class="sec-note">{note}</div>',
        unsafe_allow_html=True,
    )


def sig_label(status, lang):
    """Метка значимости для статуса сравнения из stats.py."""
    return {SIGNIFICANT: tr("sig_significant", lang), NOT_SIGNIFICANT: tr("sig_ns", lang),
            LOW_N: tr("sig_low_n", lang), NO_COMPARE: tr("sig_no_compare", lang)}.get(status, "")


def delta_class(comparison, higher_is_better=True):
    """Цвет дельты: зелёный/красный только для значимых изменений, иначе приглушённый серый."""
    if comparison is None or comparison.status != SIGNIFICANT or comparison.delta is None or comparison.delta == 0:
        return "muted"
    good = (comparison.delta > 0) == higher_is_better
    return "good" if good else "bad"


def delta_html(delta_text, comparison, lang, higher_is_better=True, css="kpi-delta"):
    """Строка «+0,3 · значимое изменение» с нужным цветом."""
    if comparison is None or comparison.status == NO_COMPARE:
        return f'<div class="{css} muted"><span class="sig">{tr("sig_no_compare", lang)}</span></div>'
    cls = delta_class(comparison, higher_is_better)
    if comparison.status == LOW_N:
        return f'<div class="{css} muted">{delta_text}<span class="sig">{sig_label(comparison.status, lang)}</span></div>'
    return f'<div class="{css} {cls}">{delta_text}<span class="sig">{sig_label(comparison.status, lang)}</span></div>'


def kpi_row(items):
    """items: список dict(label, value, suffix, cls, delta_html, foot)."""
    st.markdown(
        '<div class="kpi-row">' + "".join(
            f'''<div class="kpi-card {it.get("cls", "")}">
                  <div class="kpi-label">{it["label"]}</div>
                  <div class="kpi-value">{it["value"]}<small>{it.get("suffix", "")}</small></div>
                  {it.get("delta_html", "")}
                  <div class="kpi-foot">{it.get("foot", "")}</div>
                </div>'''
            for it in items
        ) + "</div>",
        unsafe_allow_html=True,
    )


def delta_line(prefix, value_text, delta_text, comparison, lang, higher_is_better=True):
    """Строка под заголовком вопроса: «Средний балл: 3,3 · −0,1 · в пределах погрешности»."""
    if comparison is None or comparison.status == NO_COMPARE:
        tail = f'<span class="sig">{tr("sig_no_compare", lang)}</span>'
    else:
        cls = "muted" if comparison.status == LOW_N else delta_class(comparison, higher_is_better)
        tail = f'<span class="d {cls}">{delta_text}</span><span class="sig">{sig_label(comparison.status, lang)}</span>'
    st.markdown(f'<div class="delta-line">{prefix}: <b>{value_text}</b>{tail}</div>', unsafe_allow_html=True)


def counts_line(text):
    st.markdown(f'<div class="counts-line">{text}</div>', unsafe_allow_html=True)


INSIGHT_CLASS = {0: "neg", 1: "alert", 2: "polar", 3: "pos", 4: "neutral"}


def insights_block(insights):
    st.markdown(
        '<div class="insights"><ul>' + "".join(
            f'<li class="{INSIGHT_CLASS.get(i.severity, "neutral")}">{i.text}</li>' for i in insights
        ) + "</ul></div>",
        unsafe_allow_html=True,
    )


def overview_cards(cards):
    """cards: список dict(title, sub, value, suffix, delta_html, problem_label, problem_text, link, cls)."""
    st.markdown(
        '<div class="ov-row">' + "".join(
            f'''<div class="ov-card {c.get("cls", "")}">
                  <div class="ov-title">{c["title"]}</div>
                  <div class="ov-sub">{c.get("sub", "")}</div>
                  <div class="ov-label">{c["value_label"]}</div>
                  <div class="ov-value">{c["value"]}<small>{c.get("suffix", "")}</small></div>
                  {c.get("delta_html", "")}
                  <div class="ov-label">{c["problem_label"]}</div>
                  <div class="ov-problem">{c["problem_text"]}</div>
                  <div class="ov-link">→ {c["link"]}</div>
                </div>'''
            for c in cards
        ) + "</div>",
        unsafe_allow_html=True,
    )


def legend_pills(items):
    """Подписи-легенда: [(цвет, текст), ...]."""
    st.markdown(
        "".join(f'<span class="legend-pill"><span class="sw" style="background:{color}"></span>{text}</span>'
                for color, text in items),
        unsafe_allow_html=True,
    )


def with_no_change(delta_text, comparison, lang):
    """Если дельта округляется до нуля — пишем «без изменений» вместо «0 п.п.»."""
    if comparison is not None and comparison.delta is not None and comparison.status not in (NO_COMPARE,):
        stripped = delta_text.replace("+", "").replace("−", "").replace("\u00a0", " ")
        if stripped.split(" ")[0].replace(",", ".").rstrip("%") in ("0", "0.0", "0.00"):
            return tr("no_change", lang)
    return delta_text


def yes_no_card(share_text, yes_label, delta_text, comparison, lang, cmp_text="", flag=False):
    """Компактная карточка для вопроса «Да/Нет»: крупная доля «Да», дельта и метка значимости."""
    dh = delta_html(with_no_change(delta_text, comparison, lang), comparison, lang, higher_is_better=not flag,
                    css="kpi-delta")
    st.markdown(
        f'''<div class="yn-card">
              <div class="yn-value {"flag" if flag and comparison is not None and comparison.status == SIGNIFICANT and (comparison.delta or 0) > 0 else ""}">{share_text}</div>
              <div class="yn-label">{yes_label}</div>
              {dh}
              <div class="yn-cmp">{cmp_text}</div>
            </div>''',
        unsafe_allow_html=True,
    )


def scale_note(text):
    st.markdown(f'<div class="scale-note">{text}</div>', unsafe_allow_html=True)


def short_answer_pills(items):
    """items: [(текст, число, класс тональности)] → «Всё хорошо ×12»."""
    st.markdown(
        '<div class="pill-wrap">' + "".join(
            f'<span class="pill {cls}">{text}<b>×{n}</b></span>' if n > 1 else f'<span class="pill {cls}">{text}</span>'
            for text, n, cls in items
        ) + "</div>",
        unsafe_allow_html=True,
    )

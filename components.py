"""Переиспользуемые визуальные компоненты: стили, шапка, карточки, заголовки секций."""
import textwrap

import streamlit as st

from config import (BG, BORDER, CARD_SHADOW, COMPARE_COLOR, CRITICAL, GOOD, INK, INK_2, INK_MUTED,
                    NAVY, NAVY_DEEP, NEG_SENT, POS_SENT, SKY, SURFACE)
from i18n import tr


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


def legend_pills(items):
    """Подписи-легенда: [(цвет, текст), ...]."""
    st.markdown(
        "".join(f'<span class="legend-pill"><span class="sw" style="background:{color}"></span>{text}</span>'
                for color, text in items),
        unsafe_allow_html=True,
    )

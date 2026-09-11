"""Графики Plotly в фирменной палитре."""
import plotly.graph_objects as go

from config import CHART_TEXT, COMPARE_COLOR, CURRENT_COLOR
from formatting import fmt_int, fmt_num, plotly_separators

FONT = dict(color=CHART_TEXT, family="Public Sans, sans-serif", size=11.5)
TRANSPARENT = "rgba(0,0,0,0)"


def base_layout(fig, lang="ru", **kwargs):
    fig.update_layout(
        plot_bgcolor=TRANSPARENT, paper_bgcolor=TRANSPARENT, font=FONT,
        separators=plotly_separators(lang),
        hoverlabel=dict(font=dict(family="Public Sans, sans-serif", size=12)),
        **kwargs,
    )
    return fig


def render_grouped_bar(cats, cur_vals, cmp_vals, cur_label, cmp_label, lang="ru", x_title="", share_word="Доля"):
    """Пары столбцов: голубой — период сравнения, тёмно-синий — текущий. Значения — проценты."""
    fig = go.Figure()
    for vals, label, color in ((cmp_vals, cmp_label, COMPARE_COLOR), (cur_vals, cur_label, CURRENT_COLOR)):
        fig.add_trace(go.Bar(
            x=cats, y=vals, name=label, marker=dict(color=color, cornerradius=4),
            text=[fmt_num(v, 0, lang) + "%" if v else "" for v in vals], textposition="outside",
            textfont=dict(color=CHART_TEXT, size=10.5), cliponaxis=False,
            customdata=[label] * len(cats),
            hovertemplate="%{customdata}<br>%{x}: <b>%{y:.1f}%</b><extra></extra>",
        ))
    base_layout(
        fig, lang,
        barmode="group", height=230, margin=dict(l=10, r=10, t=14, b=30), showlegend=False,
        xaxis=dict(showgrid=False, title=x_title, color=CHART_TEXT),
        yaxis=dict(showgrid=True, gridcolor="rgba(20,27,46,0.06)", ticksuffix="%", color=CHART_TEXT,
                   rangemode="tozero"),
        bargap=0.28, bargroupgap=0.12,
    )
    return fig


def render_trend_bar(labels, values, colors, hover_suffix, lang="ru"):
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=colors, cornerradius=4),
        text=[fmt_int(v, lang) for v in values], textposition="outside", textfont=dict(color=CHART_TEXT),
        cliponaxis=False,
        hovertemplate="%{x}: <b>%{text}</b> " + hover_suffix + "<extra></extra>",
    ))
    base_layout(
        fig, lang,
        height=260, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, color=CHART_TEXT), yaxis=dict(showgrid=False, visible=False),
    )
    return fig

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


def render_scale_stacked(cur_shares, cmp_shares, cur_label, cmp_label, lang="ru"):
    """100%-полоса для шкалы 1–5: две строки (сравнение внизу, текущий сверху).

    cur_shares/cmp_shares — {1..5: доля, %}. Сегменты меньше MIN_SEGMENT_LABEL_PCT не подписываются.
    Если для периода нет данных — его строка не рисуется.
    """
    from config import MIN_SEGMENT_LABEL_PCT, SCALE_COLORS, SCALE_TEXT_COLORS

    rows = []
    if cmp_shares is not None and sum(cmp_shares.values()) > 0:
        rows.append((cmp_label, cmp_shares))
    if cur_shares is not None and sum(cur_shares.values()) > 0:
        rows.append((cur_label, cur_shares))
    fig = go.Figure()
    y = [r[0] for r in rows]
    for score in [1, 2, 3, 4, 5]:
        xs = [shares.get(score, 0.0) for _, shares in rows]
        fig.add_trace(go.Bar(
            y=y, x=xs, orientation="h", name=str(score),
            marker=dict(color=SCALE_COLORS[score], line=dict(width=0)),
            text=[fmt_num(v, 0, lang) + "%" if v >= MIN_SEGMENT_LABEL_PCT else "" for v in xs],
            textposition="inside", insidetextanchor="middle", textangle=0,
            textfont=dict(color=SCALE_TEXT_COLORS[score], size=11.5, family="Public Sans, sans-serif"),
            hovertemplate="%{y}<br>" + str(score) + ": <b>%{x:.1f}%</b><extra></extra>",
        ))
    base_layout(
        fig, lang,
        barmode="stack", height=60 + 52 * max(len(rows), 1), margin=dict(l=10, r=10, t=8, b=8),
        bargap=0.3,
        xaxis=dict(range=[0, 100], showgrid=False, showticklabels=False, zeroline=False, fixedrange=True),
        yaxis=dict(showgrid=False, color=CHART_TEXT, fixedrange=True, categoryorder="array", categoryarray=y,
                   tickfont=dict(size=11.5)),
        legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="left", x=0, traceorder="normal",
                    font=dict(size=11), itemclick=False, itemdoubleclick=False),
        showlegend=True, uniformtext=dict(minsize=9, mode="hide"),
    )
    return fig


def render_topics_bar(labels, counts_by_sent, sent_names, lang="ru"):
    """Горизонтальная стековая полоса: комментарии по темам с разбивкой по тональности."""
    from config import NEG_SENT, NEU_SENT, POS_SENT
    colors = {"pos": POS_SENT, "neu": NEU_SENT, "neg": NEG_SENT}
    fig = go.Figure()
    totals = [sum(counts_by_sent[k][i] for k in counts_by_sent) for i in range(len(labels))]
    for key in ("pos", "neu", "neg"):
        vals = counts_by_sent[key]
        fig.add_trace(go.Bar(
            y=labels, x=vals, orientation="h", name=sent_names[key],
            marker=dict(color=colors[key], line=dict(width=0)),
            hovertemplate="%{y}<br>" + sent_names[key] + ": <b>%{x}</b><extra></extra>",
        ))
    # итог справа от полосы
    fig.add_trace(go.Scatter(
        y=labels, x=totals, mode="text", text=[fmt_int(t, lang) for t in totals], textposition="middle right",
        textfont=dict(color=CHART_TEXT, size=11.5), hoverinfo="skip", showlegend=False, cliponaxis=False,
    ))
    base_layout(
        fig, lang,
        barmode="stack", height=max(180, 34 * len(labels) + 70), margin=dict(l=10, r=40, t=8, b=8), bargap=0.32,
        xaxis=dict(showgrid=True, gridcolor="rgba(20,27,46,0.06)", color=CHART_TEXT, zeroline=False,
                   range=[0, max(totals + [1]) * 1.12]),
        yaxis=dict(showgrid=False, color=CHART_TEXT, autorange="reversed", tickfont=dict(size=11.5)),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0, font=dict(size=11),
                    itemclick=False, itemdoubleclick=False, traceorder="normal"),
        showlegend=True,
    )
    return fig

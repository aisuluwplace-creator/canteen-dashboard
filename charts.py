"""Графики Plotly в фирменной палитре."""
import plotly.graph_objects as go

from config import CHART_TEXT, COMPARE_COLOR, CURRENT_COLOR


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


def render_trend_bar(labels, values, colors, hover_suffix):
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=colors, cornerradius=4),
        text=values, textposition="outside", textfont=dict(color=CHART_TEXT),
        hovertemplate="%{x}: <b>%{y}</b> " + hover_suffix + "<extra></extra>",
    ))
    fig.update_layout(
        height=260, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CHART_TEXT, family="Public Sans, sans-serif"),
        xaxis=dict(showgrid=False, color=CHART_TEXT), yaxis=dict(showgrid=False, visible=False),
    )
    return fig

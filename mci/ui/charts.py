"""Gráficos Plotly con el estilo de MCI."""
import pandas as pd
import plotly.graph_objects as go

UP, DOWN, ACCENT, MUTED, GRID, TEXT = "#34D399", "#F87171", "#5EEAD4", "#8795AE", "#1B263B", "#E7EDF7"
PALETTE = ["#5EEAD4", "#60A5FA", "#FBBF24", "#F472B6"]
CONFIG = {"displayModeBar": False}


def _base(fig, h=320):
    fig.update_layout(
        height=h, margin=dict(l=6, r=6, t=10, b=6), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED, family="DM Sans, sans-serif", size=12), showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, zeroline=False), hoverlabel=dict(bgcolor="#161F31", font_color=TEXT))
    return fig


def slice_days(points, days):
    if not points or not days:
        return list(points or [])
    cutoff = points[-1][0] - days * 86_400_000
    out = [p for p in points if p[0] >= cutoff]
    return out if len(out) >= 2 else list(points)


def _dates(points):
    return pd.to_datetime([p[0] for p in points], unit="ms")


def price_chart(points, days=90):
    pts = slice_days(points, days)
    ys = [p[1] for p in pts]
    up = ys[-1] >= ys[0]
    color, fill = (UP, "rgba(52,211,153,0.10)") if up else (DOWN, "rgba(248,113,113,0.10)")
    fig = go.Figure(go.Scatter(x=_dates(pts), y=ys, mode="lines", line=dict(color=color, width=2.2),
                               fill="tozeroy", fillcolor=fill,
                               hovertemplate="%{x|%d %b %Y}<br>US$ %{y:,.6g}<extra></extra>"))
    lo, hi = min(ys), max(ys)
    pad = (hi - lo) * 0.08 or hi * 0.02
    _base(fig, 340).update_yaxes(range=[max(lo - pad, 0), hi + pad])
    return fig


def line_area(points, color=ACCENT, days=365, title_fmt="US$ %{y:,.4s}"):
    pts = slice_days(points, days)
    fig = go.Figure(go.Scatter(x=_dates(pts), y=[p[1] for p in pts], mode="lines", line=dict(color=color, width=2),
                               fill="tozeroy", fillcolor="rgba(94,234,212,0.10)",
                               hovertemplate="%{x|%d %b %Y}<br>" + title_fmt + "<extra></extra>"))
    return _base(fig, 240)


def bars(points, color=ACCENT, days=90):
    pts = slice_days(points, days)
    fig = go.Figure(go.Bar(x=_dates(pts), y=[p[1] for p in pts], marker_color=color,
                           hovertemplate="%{x|%d %b %Y}<br>US$ %{y:,.4s}<extra></extra>"))
    return _base(fig, 240)


def treemap(df):
    d = df[df["market_cap"].fillna(0) > 0]
    ch = d["price_change_percentage_24h_in_currency"].fillna(0).clip(-12, 12)
    fig = go.Figure(go.Treemap(
        labels=d["symbol"].str.upper(), parents=[""] * len(d), values=d["market_cap"], customdata=ch,
        text=d["name"], textinfo="label", texttemplate="<b>%{label}</b><br>%{customdata:+.1f}%",
        marker=dict(colors=ch, colorscale=[[0, "#7F1D1D"], [0.5, "#1F2937"], [1, "#065F46"]], cmid=0, cmin=-12, cmax=12,
                    line=dict(width=1.5, color="#0A0F1C"), pad=dict(t=0, l=0, r=0, b=0)),
        hovertemplate="<b>%{text}</b> (%{label})<br>Cap.: US$ %{value:,.4s}<br>24 h: %{customdata:+.2f}%<extra></extra>",
        pathbar=dict(visible=False), tiling=dict(pad=0), root_color="rgba(0,0,0,0)", textfont=dict(color="#F4F7FB")))
    fig.update_layout(height=430, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def fear_gauge(value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, number=dict(font=dict(size=40, color=TEXT, family="Bricolage Grotesque, sans-serif")),
        gauge=dict(axis=dict(range=[0, 100], tickcolor=MUTED, tickfont=dict(size=10)), bar=dict(color=TEXT, thickness=0.22),
                   bgcolor="rgba(0,0,0,0)", borderwidth=0,
                   steps=[dict(range=[0, 25], color="#7F1D1D"), dict(range=[25, 45], color="#9A3412"),
                          dict(range=[45, 55], color="#374151"), dict(range=[55, 75], color="#166534"),
                          dict(range=[75, 100], color="#065F46")])))
    fig.update_layout(height=170, margin=dict(l=18, r=18, t=18, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def compare_chart(series, days=90):
    """series: {nombre: [(ts_ms, precio)]}. Se normaliza a base 100 desde el inicio del período."""
    fig = go.Figure()
    for i, (name, pts) in enumerate(series.items()):
        pts = slice_days(pts, days)
        if len(pts) < 2 or not pts[0][1]:
            continue
        base = pts[0][1]
        fig.add_trace(go.Scatter(x=_dates(pts), y=[p[1] / base * 100 for p in pts], mode="lines", name=name,
                                 line=dict(color=PALETTE[i % len(PALETTE)], width=2.2),
                                 hovertemplate=name + "<br>%{x|%d %b %Y}<br>%{y:.1f}<extra></extra>"))
    _base(fig, 380).update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, font=dict(color=TEXT)))
    fig.add_hline(y=100, line_dash="dot", line_color=MUTED, opacity=0.5)
    return fig

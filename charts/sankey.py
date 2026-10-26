"""
FinanceFlow - Income Statement Sankey (pro styling, data-driven layout)
pip install plotly kaleido
"""
import plotly.graph_objects as go

# =============================================================
# 1. INPUT DATA  (swap this dict per company / period)
# =============================================================
DATA = {
    "company": "Safaricom PLC",
    "period": "FY2025",
    "currency": "KES",
    "unit": "B",
    "revenue": 388.0,
    "cost_of_revenue": 180.0,
    "opex": 120.0,
    "tax": 23.0,
    # Optional revenue breakdown (must sum to revenue). {} hides the column.
    # Values below are PLACEHOLDERS - replace with reported segment figures.
    "segments": {
        "M-PESA": 160.0,
        "Mobile Data": 70.0,
        "Voice": 75.0,
        "Other": 83.0,
    },
    "source": "Source: company filings. Figures illustrative.",
}

THEME = {
    "bg": "#FFFFFF",
    "card": "#F4F6F8",
    "text": "#111827",
    "muted": "#6B7280",
    "revenue": "#1E3A5F",
    "segment": "#3B6EA5",
    "profit": "#15803D",
    "cost": "#B91C1C",
    "tax": "#64748B",
    "font": "Inter, Segoe UI, Helvetica, Arial, sans-serif",
}

WIDTH, HEIGHT = 1600, 900
MARGIN = dict(l=40, r=40, t=30, b=60)
DOMAIN_X = [0.10, 0.86]   # sankey area (paper coords) - room for labels
DOMAIN_Y = [0.06, 0.68]   # room for title + KPI cards above
GAP = 0.06                # vertical gap between stacked nodes (fraction of sankey height)


# =============================================================
# 2. HELPERS
# =============================================================
def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def money(v, d):
    return f"{d['currency']} {v:,.1f}{d['unit']}"


# =============================================================
# 3. BUILD NODES / LINKS FROM DATA
# =============================================================
def build_model(d, t):
    rev = d["revenue"]
    gp = rev - d["cost_of_revenue"]
    op = gp - d["opex"]
    ni = op - d["tax"]

    seg = d.get("segments") or {}
    if seg and abs(sum(seg.values()) - rev) > 1e-6:
        raise ValueError(f"Segments sum to {sum(seg.values())}, revenue is {rev}")

    nodes, links = [], []

    def node(label, value, col, color, kind, sub=""):
        nodes.append(dict(label=label, value=value, col=col, color=color, kind=kind, sub=sub))
        return len(nodes) - 1

    def link(s, tgt, v, color, alpha):
        links.append(dict(s=s, t=tgt, v=v, color=rgba(color, alpha)))

    c = 1 if seg else 0
    seg_ids = [node(k, v, 0, t["segment"], "segment", f"{v / rev:.0%} of revenue")
               for k, v in seg.items()]

    # Creation order matters: Plotly builds its initial layout from node order,
    # which decides where ribbons attach. Main chain first, then sinks with the
    # largest cost last -> profit ribbons leave from the top of each node.
    R = node("Revenue", rev, c, t["revenue"], "profit")
    GP = node("Gross Profit", gp, c + 1, t["profit"], "profit", f"{gp / rev:.1%} margin")
    OP = node("Operating Profit", op, c + 2, t["profit"], "profit", f"{op / rev:.1%} margin")
    NI = node("Net Income", ni, c + 3, t["profit"], "last", f"{ni / rev:.1%} margin")
    TX = node("Tax", d["tax"], c + 3, t["tax"], "last")
    OPX = node("Operating Expenses", d["opex"], c + 2, t["cost"], "cost")
    COR = node("Cost of Revenue", d["cost_of_revenue"], c + 1, t["cost"], "cost")

    for i in seg_ids:
        link(i, R, nodes[i]["value"], t["segment"], 0.30)
    link(R, COR, d["cost_of_revenue"], t["cost"], 0.30)
    link(R, GP, gp, t["profit"], 0.35)
    link(GP, OPX, d["opex"], t["cost"], 0.30)
    link(GP, OP, op, t["profit"], 0.35)
    link(OP, TX, d["tax"], t["tax"], 0.30)
    link(OP, NI, ni, t["profit"], 0.45)

    return nodes, links, dict(rev=rev, gp=gp, op=op, ni=ni)


# =============================================================
# 4. DETERMINISTIC LAYOUT (no overlaps, profits on top)
# =============================================================
def layout_nodes(nodes, total):
    ncols = max(n["col"] for n in nodes) + 1
    xs = [0.001 + i * 0.998 / (ncols - 1) for i in range(ncols)]

    cols = {}
    for i, n in enumerate(nodes):
        cols.setdefault(n["col"], []).append(i)
    maxn = max(len(v) for v in cols.values())
    scale = (1 - GAP * (maxn - 1)) / total     # sankey-height per unit of value

    order = {"segment": 0, "profit": 0, "last": 0, "cost": 1}
    for c, ids in cols.items():
        ids = sorted(ids, key=lambda i: (order[nodes[i]["kind"]], nodes[i]["label"] == "Tax"))
        top = 0.0
        for i in ids:
            h = nodes[i]["value"] * scale
            nodes[i].update(x=xs[c], y=min(0.999, max(0.001, top + h / 2)), h=h)
            top += h + GAP
    return nodes


def to_paper(x, y):
    px = DOMAIN_X[0] + x * (DOMAIN_X[1] - DOMAIN_X[0])
    py = DOMAIN_Y[1] - y * (DOMAIN_Y[1] - DOMAIN_Y[0])
    return px, py


# =============================================================
# 5. FIGURE
# =============================================================
def build_figure(d=DATA, t=THEME):
    nodes, links, k = build_model(d, t)
    nodes = layout_nodes(nodes, k["rev"])
    sankey_px_h = (HEIGHT - MARGIN["t"] - MARGIN["b"]) * (DOMAIN_Y[1] - DOMAIN_Y[0])

    fig = go.Figure(go.Sankey(
        arrangement="fixed",
        domain=dict(x=DOMAIN_X, y=DOMAIN_Y),
        node=dict(
            label=[""] * len(nodes),               # custom labels drawn below
            customdata=[n["label"] for n in nodes],
            hovertemplate="<b>%{customdata}</b><br>" + d["currency"] + " %{value:,.1f}"
                          + d["unit"] + "<extra></extra>",
            x=[n["x"] for n in nodes],
            y=[n["y"] for n in nodes],
            color=[n["color"] for n in nodes],
            thickness=18,
            pad=GAP * sankey_px_h,
            line=dict(width=0),
        ),
        link=dict(
            source=[l["s"] for l in links],
            target=[l["t"] for l in links],
            value=[l["v"] for l in links],
            color=[l["color"] for l in links],
            hovertemplate="%{source.customdata} → %{target.customdata}<br>"
                          + d["currency"] + " %{value:,.1f}" + d["unit"] + "<extra></extra>",
        ),
    ))

    # ---- node labels ----
    hpaper = DOMAIN_Y[1] - DOMAIN_Y[0]
    for n in nodes:
        px, py = to_paper(n["x"], n["y"])
        sub = f"<br><span style='color:{t['muted']}'>{n['sub']}</span>" if n["sub"] else ""
        text = f"<b>{n['label']}</b><br><span style='color:{n['color']}'>{money(n['value'], d)}</span>{sub}"
        half = n["h"] * hpaper / 2
        if n["kind"] == "last":
            pos = dict(x=px, y=py, xanchor="left", yanchor="middle", xshift=26, align="left")
        elif n["kind"] == "segment":
            pos = dict(x=px, y=py, xanchor="right", yanchor="middle", xshift=-8, align="right")
        elif n["kind"] == "cost":
            pos = dict(x=px, y=py - half, xanchor="center", yanchor="top", yshift=-6, xshift=9)
        else:
            pos = dict(x=px, y=py + half, xanchor="center", yanchor="bottom", yshift=6, xshift=9)
        fig.add_annotation(xref="paper", yref="paper", showarrow=False, text=text,
                           font=dict(size=14, color=t["text"]), **pos)

    # ---- title ----
    fig.add_annotation(
        xref="paper", yref="paper", x=0, y=1.0, xanchor="left", yanchor="top",
        showarrow=False, align="left",
        text=(f"<span style='font-size:30px'><b>{d['company']}</b></span>"
              f"<span style='font-size:30px;color:{t['muted']}'>  ·  {d['period']} Income Statement</span>"),
    )

    # ---- KPI cards ----
    kpis = [
        ("Revenue", money(k["rev"], d), t["revenue"]),
        ("Gross Margin", f"{k['gp'] / k['rev']:.1%}", t["profit"]),
        ("Operating Margin", f"{k['op'] / k['rev']:.1%}", t["profit"]),
        ("Net Margin", f"{k['ni'] / k['rev']:.1%}", t["profit"]),
    ]
    n, gap, y0, y1 = len(kpis), 0.015, 0.78, 0.90
    w = (1 - gap * (n - 1)) / n
    for i, (name, val, color) in enumerate(kpis):
        x0 = i * (w + gap)
        fig.add_shape(type="rect", xref="paper", yref="paper", x0=x0, x1=x0 + w, y0=y0, y1=y1,
                      fillcolor=t["card"], line=dict(width=0), layer="below")
        fig.add_shape(type="rect", xref="paper", yref="paper", x0=x0, x1=x0 + 0.004, y0=y0, y1=y1,
                      fillcolor=color, line=dict(width=0))
        fig.add_annotation(xref="paper", yref="paper", x=x0 + 0.015, y=y1 - 0.015,
                           xanchor="left", yanchor="top", showarrow=False,
                           font=dict(size=12, color=t["muted"]), text=name.upper())
        fig.add_annotation(xref="paper", yref="paper", x=x0 + 0.015, y=y0 + 0.015,
                           xanchor="left", yanchor="bottom", showarrow=False,
                           font=dict(size=26, color=t["text"]), text=f"<b>{val}</b>")

    # ---- footer ----
    fig.add_annotation(xref="paper", yref="paper", x=0, y=-0.04, xanchor="left", showarrow=False,
                       font=dict(size=12, color=t["muted"]), text=d["source"])
    fig.add_annotation(xref="paper", yref="paper", x=1, y=-0.04, xanchor="right", showarrow=False,
                       font=dict(size=13, color=t["muted"]),
                       text="<b>FinanceFlow</b> · Automated Financial Visuals")

    fig.update_layout(width=WIDTH, height=HEIGHT, margin=MARGIN,
                      paper_bgcolor=t["bg"], plot_bgcolor=t["bg"],
                      font=dict(family=t["font"], color=t["text"]),
                      hoverlabel=dict(bgcolor="white", font_family=t["font"]))
    return fig


# =============================================================
# 6. RUN / EXPORT
# =============================================================
if __name__ == "__main__":
    fig = build_figure()
    fig.write_html("income_sankey.html", include_plotlyjs="cdn")
    try:
        fig.write_image("income_sankey.png", scale=2)   # needs kaleido
    except Exception as e:
        print("PNG export skipped:", e)
    fig.show()
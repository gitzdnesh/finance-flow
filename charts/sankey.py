"""
FinanceFlow - "How they make money" style income statement Sankey
Custom ribbon engine on Plotly: every ribbon is a hand-built Bezier path,
so you control flow order, curvature, spacing and labels exactly.

pip install plotly kaleido
"""
import base64
import mimetypes
import os

import plotly.graph_objects as go

# =============================================================
# 1. INPUT  (feed this from SQL / Excel per company & period)
#    leaf = value  or  (value, yoy)   e.g. (161.0, 0.15) = +15% Y/Y
#    ALL FIGURES BELOW ARE PLACEHOLDERS - replace with reported numbers
# =============================================================
PNL = {
    "company": "Safaricom",
    "period": "FY2025",
    "currency": "KES",
    "unit": "B",
    "logo": "safaricom_logo.png",        # your logo file; badge drawn if missing
    "segments": {                        # nested dict -> extra column on the left
        "Mobile Services": {
            "Voice": (76.0, -0.03),
            "Mobile Data": (72.0, 0.12),
            "Messaging": (9.0, -0.05),
        },
        "M-PESA": (161.0, 0.15),
        "Fixed & Other": (70.0, 0.06),
    },
    "cost_of_revenue": 180.0,
    "opex": {                            # dict -> fans out on the right; or a single number
        "Network & IT": 45.0,
        "Staff costs": 25.0,
        "Sales & marketing": 20.0,
        "Other opex": 30.0,
    },
    "tax": 23.0,
    "yoy": {                             # optional growth for computed lines
        "Mobile Services": 0.04,
        "Revenue": 0.11,
        "Gross Profit": 0.09,
        "Operating Profit": 0.07,
        "Net Income": 0.05,
    },
    "footnote": "Sample figures for illustration.",
}

THEME = {
    "brand": "#00843D",                  # title colour (company brand)
    "text": "#1F2937",
    "muted": "#6B7280",
    "revenue": "#1F2937",
    "profit": "#2E9E4F",
    "cost": "#D64545",
    "tax": "#8A94A6",
    "up": "#2E9E4F",
    "down": "#D64545",
    "segments": ["#3B6FD6", "#00A651", "#F2A900", "#8E5CD9", "#E86F2C"],
    "bg": "#FFFFFF",
    "font": "Inter, Segoe UI, Helvetica, Arial, sans-serif",
}

# Canvas & geometry (pixels)
W, H = 1600, 920
X_LEFT, X_RIGHT = 190, 1330      # first / last node column
Y_TOP = 320                      # top of the revenue bar
REV_H = 390                      # revenue bar height -> sets the scale
NW = 20                          # node width
GAP = 22                         # min gap between stacked nodes
DROP = 34                        # extra drop for cost branches
SEG_GAP = 34                     # gap between left-side segments
LINE_H = 19                      # label line height (px) for 14px text


# =============================================================
# 2. HELPERS
# =============================================================
def rgba(hex_color, a):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{a})"


def split(v):
    return (v[0], v[1]) if isinstance(v, (tuple, list)) else (v, None)


def money(v, p, negative=False):
    s = f"{p['currency']} {v:,.1f}{p['unit']}"
    return f"({s})" if negative else s


def yoy_text(y, t):
    if y is None:
        return ""
    c = t["up"] if y >= 0 else t["down"]
    return f"<span style='color:{c}'>{y:+.0%} Y/Y</span>"


def logo_uri(path):
    if path and os.path.exists(path):
        mime = mimetypes.guess_type(path)[0] or "image/png"
        with open(path, "rb") as f:
            return f"data:{mime};base64," + base64.b64encode(f.read()).decode()
    return None


# =============================================================
# 3. P&L -> NODES / LINKS
# =============================================================
def build_model(p, t):
    nodes, links = [], []
    yoy = p.get("yoy", {})

    def add(label, value, col, kind, color, y=None, sub=None):
        nodes.append(dict(label=label, value=value, col=col, kind=kind,
                          color=color, yoy=y, sub=sub))
        return len(nodes) - 1

    def link(s, tg, v):
        links.append(dict(s=s, t=tg, v=v))

    segs = p["segments"]
    nested = any(isinstance(v, dict) for v in segs.values())
    rc = 2 if nested else 1                      # revenue column

    groups = []
    for i, (name, v) in enumerate(segs.items()):
        color = t["segments"][i % len(t["segments"])]
        if isinstance(v, dict):
            kids = [(cn, *split(cv)) for cn, cv in v.items()]
            g = add(name, sum(k[1] for k in kids), rc - 1, "group", color, yoy.get(name))
            for cn, cv, cy in kids:
                link(add(cn, cv, 0, "leaf", color, cy), g, cv)
        else:
            val, vy = split(v)
            g = add(name, val, rc - 1, "group", color, vy)
        groups.append(g)

    rev = sum(nodes[g]["value"] for g in groups)
    R = add("Revenue", rev, rc, "revenue", t["revenue"], yoy.get("Revenue"))
    for g in groups:
        link(g, R, nodes[g]["value"])
    for n in nodes:
        if n["kind"] in ("leaf", "group"):
            n["sub"] = f"{n['value'] / rev:.0%} of revenue"

    cor = p["cost_of_revenue"]
    gp = rev - cor
    GP = add("Gross Profit", gp, rc + 1, "profit", t["profit"], yoy.get("Gross Profit"),
             f"{gp / rev:.0%} margin")
    COR = add("Cost of Revenue", cor, rc + 1, "cost", t["cost"], None,
              f"{cor / rev:.0%} of revenue")
    link(R, GP, gp)
    link(R, COR, cor)

    opex = p["opex"]
    opx = sum(opex.values()) if isinstance(opex, dict) else opex
    op = gp - opx
    OP = add("Operating Profit", op, rc + 2, "profit", t["profit"], yoy.get("Operating Profit"),
             f"{op / rev:.0%} margin")
    OPX = add("Operating Expenses", opx, rc + 2, "cost", t["cost"], None,
              f"{opx / rev:.0%} of revenue")
    link(GP, OP, op)
    link(GP, OPX, opx)

    ni = op - p["tax"]
    NI = add("Net Income", ni, rc + 3, "profit", t["profit"], yoy.get("Net Income"),
             f"{ni / rev:.0%} margin")
    TX = add("Tax", p["tax"], rc + 3, "tax", t["tax"], None, f"{p['tax'] / op:.0%} effective rate")
    link(OP, NI, ni)
    link(OP, TX, p["tax"])

    if isinstance(opex, dict):
        for name, v in opex.items():
            link(OPX, add(name, v, rc + 3, "cost", t["cost"], None,
                          f"{v / rev:.0%} of revenue"), v)

    return nodes, links, rc, rev


# =============================================================
# 4. LAYOUT  (children follow their parent's ribbon, then de-overlap)
# =============================================================
def layout(nodes, links, rc, rev):
    k = REV_H / rev
    ncols = max(n["col"] for n in nodes) + 1
    xs = [X_LEFT + c * (X_RIGHT - X_LEFT) / (ncols - 1) for c in range(ncols)]

    cols, pos = {}, {}
    for i, n in enumerate(nodes):
        n["h"] = max(n["value"] * k, 2)
        n["lines"] = 2 + bool(n["sub"]) + (n["yoy"] is not None)
        n["x"] = xs[n["col"]]
        pos[i] = len(cols.setdefault(n["col"], []))
        cols[n["col"]].append(i)
    out = {i: [l for l in links if l["s"] == i] for i in range(len(nodes))}
    inn = {i: [l for l in links if l["t"] == i] for i in range(len(nodes))}

    def resolve(ids, desired, gap, side_labels):
        prev_bot = prev_c = prev_lines = None
        for i in ids:
            y, h = desired[i], nodes[i]["h"]
            if prev_bot is not None:
                y = max(y, prev_bot + gap)
                # keep side labels from colliding: spacing scales with line count
                min_dy = (prev_lines + nodes[i]["lines"]) / 2 * LINE_H + 10
                if side_labels and y + h / 2 < prev_c + min_dy:
                    y = prev_c + min_dy - h / 2
            nodes[i]["y"] = y
            prev_bot, prev_c, prev_lines = y + h, y + h / 2, nodes[i]["lines"]

    nodes[cols[rc][0]]["y"] = Y_TOP

    for c in range(rc + 1, ncols):                    # forward (right side)
        desired = {}
        for i in cols[c]:
            l = inn[i][0]
            sibs = sorted(out[l["s"]], key=lambda L: pos[L["t"]])
            off = sum(L["v"] for L in sibs[:sibs.index(l)]) * k
            drop = 0 if nodes[i]["kind"] == "profit" else DROP
            desired[i] = nodes[l["s"]]["y"] + off + drop
        resolve(cols[c], desired, GAP, c == ncols - 1)

    for c in range(rc - 1, -1, -1):                   # backward (left side)
        desired = {}
        for i in cols[c]:
            l = out[i][0]
            sibs = sorted(inn[l["t"]], key=lambda L: pos[L["s"]])
            desired[i] = nodes[l["t"]]["y"] + sum(L["v"] for L in sibs[:sibs.index(l)]) * k
        resolve(cols[c], desired, SEG_GAP, True)
        shift = sum(nodes[i]["y"] - desired[i] for i in cols[c]) / len(cols[c])
        for i in cols[c]:
            nodes[i]["y"] -= shift

    # ribbon attachment points, ordered by the other end's height -> no crossings
    for i, n in enumerate(nodes):
        off = n["y"]
        for L in sorted(out[i], key=lambda L: nodes[L["t"]]["y"]):
            L["sy"], off = off, off + L["v"] * k
        off = n["y"]
        for L in sorted(inn[i], key=lambda L: nodes[L["s"]]["y"]):
            L["ty"], off = off, off + L["v"] * k
        n["has_in"] = bool(inn[i])
        n["pos"] = pos[i]
    return k, ncols


# =============================================================
# 5. RENDER
# =============================================================
def ribbon_path(x0, x1, sy, ty, h, curve=0.5):
    xm0 = x0 + (x1 - x0) * curve
    xm1 = x1 - (x1 - x0) * curve
    return (f"M{x0},{sy} C{xm0},{sy} {xm1},{ty} {x1},{ty} "
            f"L{x1},{ty + h} C{xm1},{ty + h} {xm0},{sy + h} {x0},{sy + h} Z")


def label_html(n, p, t):
    name_color = t["text"] if n["kind"] == "revenue" else n["color"]
    lines = [f"<b><span style='color:{name_color}'>{n['label']}</span></b>",
             f"<span style='color:{t['text']}'>{money(n['value'], p, n['kind'] in ('cost', 'tax'))}</span>"]
    if n["sub"]:
        lines.append(f"<span style='color:{t['muted']}'>{n['sub']}</span>")
    if n["yoy"] is not None:
        lines.append(yoy_text(n["yoy"], t))
    return "<br>".join(lines)


def render(p=PNL, t=THEME):
    nodes, links, rc, rev = build_model(p, t)
    k, ncols = layout(nodes, links, rc, rev)
    shapes, ann = [], []

    # ribbons
    for L in links:
        s, tg = nodes[L["s"]], nodes[L["t"]]
        base = s["color"] if tg["kind"] in ("revenue", "group") else tg["color"]
        shapes.append(dict(type="path", layer="below", line=dict(width=0),
                           fillcolor=rgba(base, 0.38),
                           path=ribbon_path(s["x"] + NW, tg["x"], L["sy"], L["ty"], L["v"] * k)))
    # nodes
    for n in nodes:
        shapes.append(dict(type="rect", x0=n["x"], x1=n["x"] + NW, y0=n["y"], y1=n["y"] + n["h"],
                           fillcolor=n["color"], line=dict(width=0)))

    # labels
    for n in nodes:
        cx, cy = n["x"] + NW / 2, n["y"] + n["h"] / 2
        base = dict(text=label_html(n, p, t), showarrow=False, font=dict(size=14))
        last = n["col"] == ncols - 1
        if last:
            pos = dict(x=n["x"] + NW + 10, y=cy, xanchor="left", yanchor="middle", align="left")
        elif n["kind"] in ("leaf", "group") and not (n["has_in"]):
            pos = dict(x=n["x"] - 10, y=cy, xanchor="right", yanchor="middle", align="right")
        elif n["kind"] in ("revenue", "profit") or (n["kind"] == "group" and n["pos"] == 0):
            pos = dict(x=cx, y=n["y"] - 8, xanchor="center", yanchor="bottom", align="center")
        else:
            pos = dict(x=cx, y=n["y"] + n["h"] + 8, xanchor="center", yanchor="top", align="center")
        ann.append({**base, **pos})

    # title
    ann.append(dict(x=W / 2, y=62, showarrow=False, xanchor="center", yanchor="middle",
                    text=f"<b>{p['company']} {p['period']} Income Statement</b>",
                    font=dict(size=40, color=t["brand"])))

    # logo above the revenue label
    R = next(n for n in nodes if n["kind"] == "revenue")
    logo_bottom = R["y"] - 8 - R["lines"] * LINE_H - 12
    images = []
    uri = logo_uri(p.get("logo"))
    if uri:
        images.append(dict(source=uri, xref="x", yref="y", x=R["x"] + NW / 2, y=logo_bottom,
                           sizex=130, sizey=90, xanchor="center", yanchor="bottom",
                           sizing="contain", layer="above"))
    else:   # fallback badge with initials
        cx, r = R["x"] + NW / 2, 36
        shapes.append(dict(type="circle", x0=cx - r, x1=cx + r, y0=logo_bottom - 2 * r,
                           y1=logo_bottom, fillcolor=t["brand"], line=dict(width=0)))
        ann.append(dict(x=cx, y=logo_bottom - r, showarrow=False,
                        text=f"<b>{p['company'][:2].upper()}</b>",
                        font=dict(size=26, color="white")))

    # footer
    ann.append(dict(x=40, y=H - 30, xanchor="left", showarrow=False,
                    font=dict(size=12, color=t["muted"]), text=p.get("footnote", "")))
    ann.append(dict(x=W - 40, y=H - 30, xanchor="right", showarrow=False,
                    font=dict(size=14, color=t["muted"]),
                    text="<b>FinanceFlow</b> · Automated Financial Visuals"))

    # invisible markers for hover
    hover = go.Scatter(
        x=[n["x"] + NW / 2 for n in nodes], y=[n["y"] + n["h"] / 2 for n in nodes],
        mode="markers", marker=dict(size=[max(12, min(n["h"], 60)) for n in nodes], opacity=0),
        hovertext=[f"<b>{n['label']}</b><br>{money(n['value'], p)}"
                   + (f"<br>{n['sub']}" if n["sub"] else "") for n in nodes],
        hoverinfo="text", showlegend=False)

    fig = go.Figure(hover)
    fig.update_layout(
        width=W, height=H, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=t["bg"], plot_bgcolor=t["bg"],
        font=dict(family=t["font"], color=t["text"]),
        xaxis=dict(range=[0, W], visible=False, fixedrange=True),
        yaxis=dict(range=[H, 0], visible=False, fixedrange=True),
        shapes=shapes, annotations=ann, images=images,
        hoverlabel=dict(bgcolor="white", font_family=t["font"]),
    )
    return fig


# =============================================================
# 6. RUN / EXPORT
# =============================================================
if __name__ == "__main__":
    fig = render()
    stem = f"{PNL['company']}_{PNL['period']}_income".replace(" ", "_").lower()
    fig.write_html(f"{stem}.html", include_plotlyjs="cdn")
    try:
        fig.write_image(f"{stem}.png", scale=2)          # needs kaleido + Chrome
    except Exception as e:
        print("PNG export skipped:", e)
    fig.show()
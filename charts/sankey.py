import plotly.graph_objects as go

# -----------------------------
# Financial Data
# -----------------------------
company = "Safaricom FY2025"

revenue = 388
cost_of_service = 180
gross_profit = revenue - cost_of_service

operating_expenses = 120
operating_profit = gross_profit - operating_expenses

tax = 23
net_income = operating_profit - tax

# -----------------------------
# Sankey
# -----------------------------

fig = go.Figure(
    data=[
        go.Sankey(
            arrangement="fixed",
            node=dict(
                pad=35,
                thickness=28,
                line=dict(color="white", width=0),
                label=[
                    "Revenue",
                    "Cost of Service",
                    "Gross Profit",
                    "Operating Expenses",
                    "Operating Profit",
                    "Tax",
                    "Net Income"
                ],
                color=[
                    "#000000",  # Revenue
                    "#d62728",  # Cost
                    "#2ca02c",  # GP
                    "#d62728",  # Opex
                    "#2ca02c",  # Op Profit
                    "#888888",  # Tax
                    "#1f9d55"   # Net Income
                ],

                # Manual positions
                x=[0.15, 0.55, 0.40, 0.75, 0.65, 0.85, 0.92],
                y=[0.50, 0.70, 0.35, 0.35, 0.15, 0.10, 0.15]
            ),
            link=dict(
                source=[0,0,2,2,4,4],
                target=[1,2,3,4,5,6],
                value=[
                    cost_of_service,
                    gross_profit,
                    operating_expenses,
                    operating_profit,
                    tax,
                    net_income
                ],
                color=[
                    "rgba(255,0,0,0.35)",
                    "rgba(50,180,50,0.45)",
                    "rgba(255,0,0,0.35)",
                    "rgba(50,180,50,0.45)",
                    "rgba(180,180,180,0.4)",
                    "rgba(50,180,50,0.65)"
                ]
            )
        )
    ]
)

# -----------------------------
# Layout
# -----------------------------

fig.update_layout(
    title={
        "text": f"<b>{company} Income Statement</b>",
        "font": {"size": 30},
        "x": 0.5
    },
    font=dict(
        family="Arial",
        size=14,
        color="#222"
    ),
    width=1600,
    height=900,
    paper_bgcolor="white",
    plot_bgcolor="white"
)

# -----------------------------
# KPI BOXES
# -----------------------------

gross_margin = gross_profit / revenue * 100
op_margin = operating_profit / revenue * 100
net_margin = net_income / revenue * 100

fig.add_annotation(
    x=0.05,
    y=1.03,
    xref="paper",
    yref="paper",
    showarrow=False,
    align="left",
    text=(
        f"<b>Revenue</b><br>${revenue}B"
        f"<br><br><b>Gross Margin</b><br>{gross_margin:.1f}%"
    )
)

fig.add_annotation(
    x=0.50,
    y=1.03,
    xref="paper",
    yref="paper",
    showarrow=False,
    text=(
        f"<b>Operating Profit</b><br>${operating_profit}B"
        f"<br><br><b>Operating Margin</b><br>{op_margin:.1f}%"
    )
)

fig.add_annotation(
    x=0.92,
    y=1.03,
    xref="paper",
    yref="paper",
    showarrow=False,
    text=(
        f"<b>Net Income</b><br>${net_income}B"
        f"<br><br><b>Net Margin</b><br>{net_margin:.1f}%"
    )
)

# Footer

fig.add_annotation(
    x=0.5,
    y=-0.08,
    xref="paper",
    yref="paper",
    showarrow=False,
    font=dict(size=18),
    text="<b>FinanceFlow</b> • Automated Financial Visuals"
)

fig.show()

# Optional export
# fig.write_html("safaricom_report.html")
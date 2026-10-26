import plotly.graph_objects as go
import json

with open("data/safaricom.json") as f:
    d = json.load(f)

fig = go.Figure(
    go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=[
                "Revenue",
                "Cost of Service",
                "Gross Profit",
                "Operating Expense",
                "Operating Profit",
                "Tax",
                "Net Income"
            ]
        ),
        link=dict(
            source=[0,0,2,2,4],
            target=[1,2,3,4,5],
            value=[
                d["cost_of_service"],
                d["gross_profit"],
                d["operating_expense"],
                d["operating_profit"],
                d["tax"]
            ]
        )
    )
)

# fig.write_image("safaricom.png")
fig.show()
from dash import dcc, html

# import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

import pandas as pd
import plotly.express as px
from example.models import entity_with_float_on_mysql

with entity_with_float_on_mysql.session() as session:
    db_model = entity_with_float_on_mysql.sql_model_db()
    entities = session.query(db_model).all()

df = pd.DataFrame.from_dict(
    {
        "id": [1, 2, 3, 4],
        "float_value": [1.0, 2.0, 3.0, 4.0],
    }
)
fig = px.scatter(df, x="id", y="float_value")
# fig.layout.template = "plotly_white"
# fig.layout.template = "darkly"

fig.update_layout(
    {
        "template": "plotly_white",
        "plot_bgcolor": "rgba(0, 0, 0, 0)",
        "paper_bgcolor": "rgba(0, 0, 0, 0)",
    }
)


entities = {
    "link": {
        "label": "Entities",
        "id": "entities-1-navlink",
        "href": "/entities",
        "variant": "light",
        "refresh": False,
        "icon": DashIconify(icon="tabler:gauge"),
        "rightSection": DashIconify(icon="tabler-chevron-right"),
        "n_clicks": 0,
    },
    "html": html.Div(
        [
            dmc.Card(
                children=[
                    html.H1("Entities", id="entities-1-title"),
                    html.Div(dcc.Input(id="input-on-submit", type="text")),
                    dmc.Button("Submit", id="submit-val", n_clicks=0),
                    dcc.Graph(
                        id="entities-1-graph",
                        animate=True,
                        figure=fig,
                    ),
                ],
                shadow="sm",
                withBorder=True,
            ),
        ]
    ),
}

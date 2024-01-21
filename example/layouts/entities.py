from dash import dcc, html
import dash_bootstrap_components as dbc

# import pandas as pd
# import plotly.express as px
from example.models import entity_with_float_on_mysql

with entity_with_float_on_mysql.session() as session:
    db_model = entity_with_float_on_mysql.sql_model_db()
    entities = session.query(db_model).all()


# df = pd.DataFrame({})
# fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

entities = {
    "path": "/entities",
    "html": html.Div(
        [
            dbc.Card(
                children=[
                    html.H1("Entities", id="entities-1-title"),
                    html.Div(dcc.Input(id="input-on-submit", type="text")),
                    dbc.Button("Submit", id="submit-val", n_clicks=0),
                    dcc.Graph(
                        id="entities-1-graph",
                        # figure=fig
                    ),
                ],
                className="bg-light",
                style={
                    "padding": "18px",
                    "margin": "18px",
                },
            ),
        ]
    ),
}

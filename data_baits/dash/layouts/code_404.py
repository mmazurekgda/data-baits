import dash_mantine_components as dmc
from dash import html


def create_default_404_layout(**kwargs) -> html.Div:
    return html.Div(
        dmc.Card(
            children=[
                dmc.Group(
                    [
                        dmc.Text(
                            children="404! Page not found!",
                            size=60,
                            weight=800,
                            variant="text",
                        ),
                    ],
                    position="center",
                ),
                html.Br(),
                html.Br(),
                html.Br(),
            ],
            shadow="lg",
            withBorder=True,
            style={
                "backgroundColor": "dimmed",
            },
        )
    )

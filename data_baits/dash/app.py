import dash
from dash.dependencies import Input, Output
from dash import dcc
from dash import html
from dash import callback
import dash_bootstrap_components as dbc
from data_baits.core.settings import settings


def main_layout(
    name: str,
    layouts: dict[str, dict],
):
    navbar_items = [
        dbc.NavItem(
            dbc.NavLink(
                layout_name,
                href=layout["path"],
            )
        )
        for layout_name, layout in layouts.items()
    ]

    # sidebar = dbc.Offcanvas(
    #     children=[
    #         html.H1(
    #             name,
    #             className="my-2",
    #         ),
    #         dbc.Nav(
    #             navbar_items,
    #             vertical=True,
    #             pills=True,
    #         ),

    #     ],
    #     # title=name,
    #     scrollable=False,
    #     is_open=True,
    #     id="offcanvas",
    #     className="bg-dark text-white",
    #     backdrop=False,
    #     close_button=False,
    #     style={
    #         "transform": "none",
    #         "top": "56px",
    #     },
    # )
    # sidebar = dbc.Navbar(
    #     children=navbar_items,
    #     # color="primary",
    #     dark=True,
    #     className="bg-dark",
    #     vertical=True,
    # )

    navbar = dbc.NavbarSimple(
        children=navbar_items,
        brand=name,
        brand_href="/",
        # color="primary",
        dark=True,
        links_left=True,
        sticky="top",
        className="bg-dark",
    )
    scaffolding = dbc.Row(
        [
            dbc.Col(
                children=[
                    html.Div(
                        id="page-content",
                    ),
                ],
                md=12,
                lg=6,
            ),
        ],
        justify="center",
    )
    return html.Div(
        [
            dcc.Location(
                id="url",
                refresh=False,
            ),
            navbar,
            # sidebar,
            scaffolding,
        ],
        # className="bg-secondary",
        style={
            "height": "100vh",
            "background-color": "#343a40",
            # "data-bs-theme": "dark",
        },
    )


def main_callback(layouts):
    @callback(Output("page-content", "children"), Input("url", "pathname"))
    def show_pages(pathname):
        for layout in layouts.values():
            if pathname == layout["path"]:
                return layout["html"]
        return "404"

    return show_pages


def create_dash_app(
    layouts: dict[str, dict],
    callbacks_generator: callable = lambda: None,
    name: str = settings.PROJECT_NAME,
    main_layout: callable = main_layout,
    main_callback: callable = main_callback,
    main_dbc_theme: str = dbc.themes.BOOTSTRAP,
    suppress_callback_exceptions: bool = True,
) -> dash.Dash:
    app = dash.Dash(
        __name__,
        external_stylesheets=[main_dbc_theme],
        suppress_callback_exceptions=suppress_callback_exceptions,
    )

    app.layout = main_layout(
        name=name,
        layouts=layouts,
    )

    main_callback(layouts)

    callbacks_generator()

    return app

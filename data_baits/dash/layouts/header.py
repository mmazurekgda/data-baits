from dash import dcc
from dash_iconify import DashIconify
import dash_mantine_components as dmc


def create_default_header(**kwargs) -> dmc.Header:
    avatar_box = dmc.Grid(
        children=[
            dmc.Col(
                children=[
                    dcc.Link(
                        dmc.Avatar(**kwargs["avatar_options"]),
                        href="/",
                        refresh=False,
                        style={
                            "height": "35px",
                        },
                    ),
                    dmc.Text(
                        children=kwargs["app_name"],
                        size=35,
                        weight=700,
                        # inherit=True,
                        variant="gradient",
                        style={
                            "color": "dark",
                            "paddingLeft": "10px",
                            # "paddingTop": "2px",
                        },
                        className="hidden-below-width",
                    ),
                    dmc.Text(
                        children=f"v{kwargs['app_version']}",
                        size=15,
                        weight=1000,
                        # inherit=True,
                        variant="text",
                        style={
                            "color": "dark",
                            "verticalAlign": "bottom",
                            "paddingTop": "17px",
                        },
                        className="hidden-below-width",
                    ),
                    dmc.Text(
                        children=kwargs["app_version_dev"],
                        size=10,
                        weight=1000,
                        # inherit=True,
                        variant="text",
                        style={
                            "color": "red",
                            "verticalAlign": "bottom",
                            "paddingTop": "0px",
                        },
                        className="hidden-below-width",
                    ),
                    dmc.Button(
                        DashIconify(
                            icon="radix-icons:text-align-justify",
                            height=30,
                        ),
                        id="left-navbar-toggler",
                        style={
                            "padding": "5px",
                            "marginLeft": "15px",
                        },
                        variant="outline",
                        className="hidden-above-width",
                        n_clicks=0,
                    ),
                ],
                span="content",
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "minHeight": "70px",
                },
            ),
            dmc.Col(
                children=[
                    dmc.Group(
                        [
                            dmc.Switch(
                                id="color-scheme-switch",
                                size="md",
                                radius="lg",
                                checked=(kwargs["color_scheme"] == "dark"),
                                onLabel=DashIconify(
                                    icon="ic:round-dark-mode",
                                    height=15,
                                ),
                                offLabel=DashIconify(
                                    icon="ic:round-light-mode",
                                    height=15,
                                ),
                                disabled=True,
                            ),
                            dmc.Button(
                                "Log in",
                                leftIcon=DashIconify(icon="mdi:login"),
                                id="log-in-button-from-header",
                                variant="subtle",
                                # fullWidth=True,
                                size="sm",
                                n_clicks=0,
                                style={
                                    "marginRight": "15px",
                                    "display": "block",
                                },
                            ),
                            dmc.Button(
                                "Log out",
                                leftIcon=DashIconify(icon="mdi:logout"),
                                id="log-out-button-from-header",
                                # loading=True,
                                variant="subtle",
                                # fullWidth=True,
                                size="sm",
                                n_clicks=0,
                                style={
                                    "marginRight": "15px",
                                    "display": "none",
                                },
                            ),
                        ],
                        position="center",
                    )
                ],
                span="content",
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "flex-end",
                },
                # className="hidden-above-width",
            ),
        ],
        justify="space-between",
        gutter="sm",
        align="center",
        style={
            # "width": "300px",
            "height": "50px",
            "paddingLeft": "15px",
            "mx": "auto",
            # "marginBottom": "-20px",
        },
    )
    return dmc.Header(
        children=[
            avatar_box,
        ],
        height=60,
        withBorder=True,
        # fixed=True,
        style={
            # "display": "flex",
            # "justifyContent": "space-between",
            # "ml": "auto",
            # "alignItems": "center",
        },
    )

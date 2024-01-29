from dash import html
import dash_mantine_components as dmc
from dash_iconify import DashIconify


def create_login_modal(**kwargs) -> dmc.Modal:
    return dmc.Modal(
        title="Log in",
        id="log-in-modal",
        zIndex=10000,
        children=[
            dmc.LoadingOverlay(
                dmc.Stack(
                    id="loading-form",
                    children=[
                        dmc.TextInput(
                            label="Username",
                            id="log-in-modal-username-input",
                            placeholder="Your username",
                            icon=DashIconify(icon="radix-icons:person"),
                            required=True,
                        ),
                        dmc.PasswordInput(
                            label="Password",
                            id="log-in-modal-password-input",
                            placeholder="Your password",
                            icon=DashIconify(icon="radix-icons:lock-closed"),
                            required=True,
                        ),
                        dmc.Checkbox(
                            label="Remember me",
                            checked=True,
                            disabled=True,
                        ),
                        dmc.Group(
                            [
                                dmc.Button(
                                    "Submit",
                                    id="log-in-modal-submit-button",
                                    n_clicks=0,
                                ),
                                dmc.Button(
                                    "Close",
                                    color="red",
                                    variant="outline",
                                    id="log-in-modal-close-button",
                                ),
                            ],
                            position="right",
                        ),
                    ],
                )
            )
        ],
    )


def create_default_not_logged_in_layout(**kwargs) -> html.Div:
    return html.Div(
        dmc.Card(
            children=[
                dmc.Group(
                    [
                        dmc.Text(
                            children="Welcome to the",
                            size=60,
                            weight=800,
                            variant="text",
                        ),
                        dmc.Text(
                            children=kwargs["app_name"],
                            size=60,
                            weight=800,
                            variant="gradient",
                        ),
                        dmc.Text(
                            children="project!",
                            size=60,
                            weight=800,
                            variant="text",
                        ),
                    ],
                    position="center",
                ),
                dmc.Group(
                    [
                        html.Img(
                            src=kwargs["avatar_options"]["src"],
                            style={
                                "width": "30%",
                                "height": "auto",
                                "text-align": "center",
                            },
                        ),
                    ],
                    position="center",
                ),
                dmc.Group(
                    [
                        dmc.Text(
                            children="Log in to access the app.",
                            size=40,
                        ),
                    ],
                    position="center",
                ),
                html.Br(),
                html.Br(),
                html.Br(),
                dmc.Group(
                    [
                        dmc.Button(
                            "Log in",
                            id="log-in-button-from-card",
                            # loading=True,
                            variant="gradient",
                            # fullWidth=True,
                            size="xl",
                            n_clicks=0,
                        )
                    ],
                    position="center",
                ),
            ],
            shadow="lg",
            withBorder=True,
            style={
                "background-color": "dimmed",
            },
        )
    )

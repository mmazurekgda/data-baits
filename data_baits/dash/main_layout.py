import dash_mantine_components as dmc
from dash import html
from typing import Any
from collections.abc import Callable
from typing import Dict
from data_baits.dash.layouts.navbar import create_default_main_navbar
from data_baits.dash.layouts.header import create_default_header
from data_baits.dash.layouts.login import create_login_modal


def create_default_scaffolding(**kwargs) -> html.Div:
    return html.Div(
        children=[
            create_login_modal(**kwargs),
            dmc.Alert(
                "You must log in to see this page!",
                title="Oooops!",
                id="failed-login-alert",
                color="red",
                withCloseButton=True,
                hide=True,
            ),
            dmc.Alert(
                "You have been logged out!",
                title="Success!",
                id="successful-logout-alert",
                # color="",
                withCloseButton=True,
                hide=True,
            ),
            html.Br(),
            dmc.LoadingOverlay(
                html.Div([], id="page-content"),
            ),
        ]
    )


def create_default_main_layout(
    layouts: dict[str, dict],
    create_main_navbar: Callable[
        [Dict[str, dict], str, str, ...], dmc.Navbar
    ] = create_default_main_navbar,
    create_main_header: Callable[
        [Dict[str, str], ...], dmc.Header
    ] = create_default_header,
    create_main_scaffolding: Callable[
        [...], html.Div
    ] = create_default_scaffolding,
    **kwargs
) -> Any:
    return dmc.MantineProvider(
        id="mantine-provider",
        theme={
            "colorScheme": kwargs["color_scheme"],
            "primaryColor": kwargs["primary_color"],
            "fontFamily": "Dosis, sans-serif",
        },
        inherit=True,
        children=[
            dmc.AppShell(
                id="",
                children=[
                    create_main_scaffolding(**kwargs),
                ],
                navbar=create_main_navbar(layouts, **kwargs),
                header=create_main_header(**kwargs),
            )
        ],
        withGlobalStyles=True,
        withCSSVariables=True,
        withNormalizeCSS=True,
    )

from typing import Literal
from dash.dependencies import Input, Output, State
from flask_login import current_user
from dash import callback
from enum import Flag


def generate_display_content_callback(core_layouts, layouts, **kwargs):
    navlink_order = {}

    def create_navlink_actions(action: Literal["Output", "State"]):
        actions = []
        for index, layout in enumerate(layouts.values()):
            if "id" in layout["link"]:
                if action == "Output":
                    actions.append(Output(layout["link"]["id"], "active"))
                    actions.append(Output(layout["link"]["id"], "style"))
                elif action == "State":
                    actions.append(State(layout["link"]["id"], "active"))
                    actions.append(State(layout["link"]["id"], "style"))
                    navlink_order[layout["link"]["id"]] = index
        return actions

    @callback(
        Output("page-content", "children"),
        Output("failed-login-alert", "hide"),
        Output("left-navbar-header", "style"),
        *create_navlink_actions("Output"),
        Input("url", "pathname"),
        State("page-content", "children"),
        State("failed-login-alert", "hide"),
        State("left-navbar-header", "style"),
        *create_navlink_actions("State"),
        prevent_initial_call=True,
    )
    def display_content(
        pathname,
        page_content,
        failed_login_alert_hidden,
        navbar_header_style,
        *navlink_args,
    ):
        is_core = True
        grouped_args_no = len(navlink_args) // 2
        visible = {"display": "flex"}
        invisible = {"display": "none"}
        navlink_outputs = [False, invisible] * grouped_args_no
        # enable navlinks if user is logged in and role is correct
        role: Flag | None = None
        if current_user.is_authenticated:
            role = kwargs["get_role"]()
            navbar_header_style.update(invisible)
        else:
            navbar_header_style.update(visible)
        for layout in layouts.values():
            access_ok = role is not None and role & layout["role"]
            base_index = 2 * navlink_order[layout["link"]["id"]]
            if access_ok:
                navlink_outputs[base_index + 1] = visible
            if pathname == layout["link"]["href"]:
                if access_ok:
                    page_content = layout["html"]
                    # activate navlink
                    navlink_outputs[base_index] = True
                else:
                    failed_login_alert_hidden = False
                    if not page_content:
                        page_content = core_layouts["main_not_logged"]["html"]
                is_core = False
        if is_core:
            if pathname == "/":
                if current_user.is_authenticated:
                    page_content = core_layouts["main_logged"]["html"]
                else:
                    page_content = core_layouts["main_not_logged"]["html"]
            else:
                page_content = core_layouts["404"]["html"]
        return (
            page_content,
            failed_login_alert_hidden,
            navbar_header_style,
            *navlink_outputs,
        )

    return display_content


def generate_toggle_color_scheme_callback():
    @callback(
        Output("mantine-provider", "theme"),
        Output("color_theme", "data"),
        Output("color-scheme-switch", "disabled"),
        Output("color-scheme-switch", "checked"),
        Input("url", "pathname"),
        Input("color-scheme-switch", "checked"),
        State("color-scheme-switch", "disabled"),
        State("mantine-provider", "theme"),
        State("color_theme", "data")
        # prevent_initial_call=True,
    )
    def toggle_color_scheme(_, on, disabled, theme, theme_session):
        if disabled and theme_session:
            theme["colorScheme"] = theme_session
            return theme, theme_session, False, theme_session == "dark"
        if on:
            theme["colorScheme"] = "dark"
            theme_session = "dark"
        else:
            theme["colorScheme"] = "light"
            theme_session = "light"
        return theme, theme_session, False, theme_session == "dark"

    return toggle_color_scheme

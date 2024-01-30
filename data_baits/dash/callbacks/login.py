from dash import callback
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from flask_login import (
    current_user,
    login_user,
    logout_user,
)
import dash


def generate_toggle_login_modal_callback():
    def toggle_login_modal(btn, opened):
        if not btn:
            raise PreventUpdate
        if current_user.is_authenticated:
            return False
        else:
            return not opened

    @callback(
        Output("log-in-modal", "opened", allow_duplicate=True),
        Input("log-in-button-from-card", "n_clicks"),
        State("log-in-modal", "opened"),
        prevent_initial_call=True,
    )
    def toggle_login_modal_by_card(btn, opened):
        return toggle_login_modal(btn, opened)

    @callback(
        Output("log-in-modal", "opened", allow_duplicate=True),
        Input("log-in-button-from-header", "n_clicks"),
        State("log-in-modal", "opened"),
        prevent_initial_call=True,
    )
    def toggle_login_modal_by_header(btn, opened):
        return toggle_login_modal(btn, opened)

    @callback(
        Output("log-in-modal", "opened", allow_duplicate=True),
        Input("log-in-modal-close-button", "n_clicks"),
        State("log-in-modal", "opened"),
        prevent_initial_call=True,
    )
    def toggle_modal_close_button(btn, opened):
        return toggle_login_modal(btn, opened)

    return (
        toggle_login_modal_by_card,
        toggle_login_modal_by_header,
        toggle_modal_close_button,
    )


def generate_login_user_callback(**kwargs):
    @callback(
        Output("url", "pathname", allow_duplicate=True),
        Output("log-in-modal-username-input", "error"),
        Output("log-in-modal-password-input", "error"),
        Output("log-in-modal", "opened", allow_duplicate=True),
        Input("log-in-modal-submit-button", "n_clicks"),
        State("log-in-modal-username-input", "value"),
        State("log-in-modal-password-input", "value"),
        prevent_initial_call=True,
    )
    def login_user_call(submit, username, password):
        if not submit:
            raise PreventUpdate
        username_error = ""
        password_error = ""
        if not username:
            username_error = "Username is required"
        if not password:
            password_error = "Password is required"
        if username_error or password_error:
            return (
                dash.no_update,
                username_error,
                password_error,
                True,
            )
        user_id = kwargs["authenticate"](
            username=username,
            password=password,
        )
        if not user_id:
            return (
                dash.no_update,
                "Wrong username or password!",
                "",
                True,
            )
        login_user(kwargs["user_class"](user_id))
        return "/", "", "", False

    return login_user_call


def generate_logout_user_callback():
    @callback(
        Output("url", "pathname", allow_duplicate=True),
        Output("successful-logout-alert", "hide"),
        Input("log-out-button-from-header", "n_clicks"),
        prevent_initial_call=True,
    )
    def logout_user_call(btn):
        if not btn:
            raise PreventUpdate
        logout_user()
        return "/", False

    return logout_user_call


def generate_toggle_logging_buttons():
    @callback(
        Output("log-in-button-from-header", "style"),
        Output("log-out-button-from-header", "style"),
        Input("url", "pathname"),
        State("log-in-button-from-header", "style"),
        State("log-out-button-from-header", "style"),
        prevent_initial_call=True,
    )
    def toggle_login__buttons(_, in_style, out_style):
        if current_user.is_authenticated:
            in_style["display"] = "none"
            out_style["display"] = "block"
        else:
            in_style["display"] = "block"
            out_style["display"] = "none"
        return in_style, out_style

    return toggle_login__buttons

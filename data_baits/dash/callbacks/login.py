from dash import callback
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash


def generate_toggle_login_modal_callback():
    def toggle_login_modal(btn, opened, user):
        if not btn:
            raise PreventUpdate
        if user:
            return False
        else:
            return not opened

    @callback(
        Output("log-in-modal", "opened", allow_duplicate=True),
        Input("log-in-button-from-card", "n_clicks"),
        State("log-in-modal", "opened"),
        State("user", "data"),
        prevent_initial_call=True,
    )
    def toggle_login_modal_by_card(btn, opened, user):
        return toggle_login_modal(btn, opened, user)

    @callback(
        Output("log-in-modal", "opened", allow_duplicate=True),
        Input("log-in-button-from-header", "n_clicks"),
        State("log-in-modal", "opened"),
        State("user", "data"),
        prevent_initial_call=True,
    )
    def toggle_login_modal_by_header(btn, opened, user):
        return toggle_login_modal(btn, opened, user)

    @callback(
        Output("log-in-modal", "opened", allow_duplicate=True),
        Input("log-in-modal-close-button", "n_clicks"),
        State("log-in-modal", "opened"),
        State("user", "data"),
        prevent_initial_call=True,
    )
    def toggle_modal_close_button(btn, opened, user):
        return toggle_login_modal(btn, opened, user)

    return (
        toggle_login_modal_by_card,
        toggle_login_modal_by_header,
        toggle_modal_close_button,
    )


def generate_login_user_callback(**kwargs):
    @callback(
        Output("user", "data"),
        Output("url", "pathname", allow_duplicate=True),
        Output("log-in-modal-username-input", "error"),
        Output("log-in-modal-password-input", "error"),
        Output("log-in-modal", "opened", allow_duplicate=True),
        Input("log-in-modal-submit-button", "n_clicks"),
        State("log-in-modal-username-input", "value"),
        State("log-in-modal-password-input", "value"),
        State("user", "data"),
        prevent_initial_call=True,
    )
    def login_user(submit, username, password, user):
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
                dash.no_update,
                username_error,
                password_error,
                True,
            )
        if not kwargs["authenticate"](
            username=username,
            password=password,
        ):
            return (
                dash.no_update,
                dash.no_update,
                "Wrong username or password!",
                "",
                True,
            )
        user = {
            "username": username,
            "role": kwargs["get_role"](),
        }
        return user, "/", "", "", False

    return login_user


def generate_logout_user_callback():
    @callback(
        Output("user", "data", allow_duplicate=True),
        Output("url", "pathname", allow_duplicate=True),
        Output("successful-logout-alert", "hide"),
        Input("log-out-button-from-header", "n_clicks"),
        # State("user", "data"),
        prevent_initial_call=True,
    )
    def logout_user(btn):
        if not btn:
            raise PreventUpdate
        return None, "/", False

    return logout_user


def generate_toggle_logging_buttons():
    @callback(
        Output("log-in-button-from-header", "style"),
        Output("log-out-button-from-header", "style"),
        Input("url", "pathname"),
        State("user", "data"),
        State("log-in-button-from-header", "style"),
        State("log-out-button-from-header", "style"),
        prevent_initial_call=True,
    )
    def toggle_login__buttons(_, user, in_style, out_style):
        if user:
            in_style["display"] = "none"
            out_style["display"] = "block"
        else:
            in_style["display"] = "block"
            out_style["display"] = "none"
        return in_style, out_style

    return toggle_login__buttons

from dash.dependencies import Input, Output, State
from dash import callback


def generate_toggle_navbar_collapse_callback():
    @callback(
        Output("left-navbar", "className"),
        Input("left-navbar-toggler", "n_clicks"),
        State("left-navbar", "className"),
        prevent_initial_call=True,
    )
    def toggle_navbar_collapse(_, className):
        if "hidden-below-sm" in className:
            className = className.replace("hidden-below-sm", "")
        else:
            className += " hidden-below-sm"
        return className

    return toggle_navbar_collapse

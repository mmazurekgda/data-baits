from dash import Output, callback, Input, State


def callback_generator():
    @callback(
        Output(component_id="entities-1-title", component_property="children"),
        Input(component_id="submit-val", component_property="n_clicks"),
        State("input-on-submit", "value"),
        prevent_initial_call=True,
    )
    def graph(n_clicks, value):
        return f'You\'ve entered "{value}" and clicked {n_clicks} times'

from data_baits.dash.callbacks.login import (
    generate_login_user_callback,
    generate_toggle_login_modal_callback,
    generate_toggle_logging_buttons,
    generate_logout_user_callback,
)
from data_baits.dash.callbacks.main_content import (
    generate_display_content_callback,
    generate_toggle_color_scheme_callback,
)
from data_baits.dash.callbacks.navbar import (
    generate_toggle_navbar_collapse_callback,
)


def create_default_main_callbacks(core_layouts, layouts, **kwargs):
    return [
        generate_toggle_navbar_collapse_callback(),
        generate_toggle_color_scheme_callback(),
        generate_login_user_callback(**kwargs),
        generate_toggle_login_modal_callback(),
        generate_toggle_logging_buttons(),
        generate_logout_user_callback(),
        generate_display_content_callback(core_layouts, layouts, **kwargs),
    ]

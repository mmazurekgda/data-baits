import dash
from typing import Literal
import os
from dash import dcc, html
from typing import Type, Dict
from flask_login import UserMixin
from flask_login import LoginManager
from flask import Flask
from typing import Callable

from data_baits.core.settings import settings, Environments
from data_baits.dash.common.theme import THEME
from data_baits.dash.main_layout import (
    create_default_main_layout,
    create_default_main_navbar,
    create_default_scaffolding,
)
from data_baits.dash.layouts.login import create_default_not_logged_in_layout
from data_baits.dash.main_callback import (
    create_default_main_callbacks,
)
from data_baits.dash.layouts.code_404 import (
    create_default_404_layout,
)

this_file_dir = os.path.dirname(os.path.realpath(__file__))


def create_dash_app(
    layouts: dict[str, dict],
    user_class: Type[UserMixin],
    callbacks_generator: callable = lambda: None,
    name: str = settings.PROJECT_NAME,
    version: str = settings.PROJECT_VERSION,
    environment: str = settings.ENVIRONMENT,
    create_main_layout: callable = create_default_main_layout,
    create_main_scaffolding: callable = create_default_scaffolding,
    create_main_callback: callable = create_default_main_callbacks,
    create_main_navbar: callable = create_default_main_navbar,
    authenticate: Callable[[str, str], bool] = lambda **__: True,
    get_role: Callable[[], int | None] = lambda: None,
    main_dmc_theme: dict = THEME,
    suppress_callback_exceptions: bool = True,
    color_scheme: Literal["light", "dark"] = "dark",
    primary_color: str = "indigo",
    avatar_options: Dict[str, str] = {
        "src": "https://avatars.githubusercontent.com/u/37097697?v=4",
        "size": "md",
        "radius": "md",
    },
    external_stylesheets: list[str] = [],
    server_name: str = __name__,
    **add_kwargs,
) -> dash.Dash:
    server = Flask(server_name)
    if not settings.DASH_SECRET_KEY:
        raise ValueError("DASH_SECRET_KEY must be set in the environment")
    server.config.update(SECRET_KEY=settings.DASH_SECRET_KEY)

    login_manager = LoginManager()
    login_manager.init_app(server)

    @login_manager.user_loader
    def load_user(id):
        return user_class(id)

    app = dash.Dash(
        server_name,
        server=server,
        external_stylesheets=[
            main_dmc_theme,
            *external_stylesheets,
            f"{this_file_dir}/assets/stylesheets.css",
        ],
        suppress_callback_exceptions=suppress_callback_exceptions,
        **add_kwargs,
    )

    # dmc.Stack(
    #     spacing="xs",
    #     children=[
    #         dmc.Skeleton(height=50, circle=True),
    #         dmc.Skeleton(height=8),
    #         dmc.Skeleton(height=8),
    #         dmc.Skeleton(height=8, width="70%"),
    #     ],
    # )

    # load_figure_template(["darkly"])

    version_dev = ""
    if environment == Environments.dev.value:
        version_dev = " DEV"

    kwargs = {
        "color_scheme": color_scheme,
        "primary_color": primary_color,
        "version_color": "dimmed",
        "app_version_dev": version_dev,
        "app_name": name,
        "app_version": version,
        "app_environment": environment,
        "authenticate": authenticate,
        "avatar_options": avatar_options,
        "user_class": user_class,
        "get_role": get_role,
    }

    core_layouts = {
        "main_not_logged": {
            "path": "/",
            "html": create_default_not_logged_in_layout(**kwargs),
        },
        "404": {
            "path": "/",
            "html": create_default_404_layout(**kwargs),
        },
    }

    app.layout = html.Div(
        [
            dcc.Location(id="url", refresh=False),
            dcc.Store("user", storage_type="session"),
            dcc.Store("color_theme", storage_type="session"),
            create_main_layout(
                layouts=layouts,
                create_main_navbar=create_main_navbar,
                create_main_scaffolding=create_main_scaffolding,
                **kwargs,
            ),
        ]
    )

    create_main_callback(core_layouts, layouts, **kwargs)

    callbacks_generator()

    return app

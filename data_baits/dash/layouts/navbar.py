import dash_mantine_components as dmc
from dash import html


def create_default_main_navbar(
    layouts: dict[str, dict] = {},
    # user: str = "user",
    # role: str = "role",
    **kwargs
) -> dmc.Navbar:
    navbar = dmc.Navbar(
        id="left-navbar",
        p="md",
        height="100vh",
        width={
            "sm": 300,
        },
        children=[
            html.H3(
                "Log in to see the menu!",
                id="left-navbar-header",
                style={
                    "text-align": "center",
                },
            ),
        ],
        withBorder=True,
        className="hidden-below-sm",
        style={
            "background-color": "dimmed",
        },
    )
    for layout_opts in layouts.values():
        navbar.children.append(dmc.NavLink(**layout_opts["link"]))

    return navbar

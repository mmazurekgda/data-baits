import dash_mantine_components as dmc


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
        children=[],
        withBorder=True,
        className="hidden-below-sm",
        style={
            "background-color": "dimmed",
        },
    )
    for layout_opts in layouts.values():
        navbar.children.append(dmc.NavLink(**layout_opts["link"]))

    return navbar

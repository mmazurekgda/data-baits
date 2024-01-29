import dash_mantine_components as dmc
from typing import Literal, List

THEME = dmc.theme.DEFAULT_COLORS


def get_main_colors(color_scheme: Literal["light", "dark"]) -> List[str]:
    colors = THEME["dark"]
    if color_scheme == "dark":
        colors = list(reversed(colors))
    return colors

"""CEMC business style library.

``STYLE_PATHS`` points at the YAML style files (one per element) loaded by
``cedarkit.plots.style.StyleRegistry.default()`` through the
``cedarkit.plots.styles`` entry point. Named RGB tables shared by several
styles are registered here at import time; complex composed tables (NCL
subsets concatenated with extra colors) are built with cedarkit-plots
colormap helpers so the YAML files stay declarative.
"""
from pathlib import Path

import numpy as np

from cedarkit.plots.colormap import generate_colormap_using_ncl_colors, get_ncl_colormap
from cedarkit.plots.style import register_rgb_table


STYLE_PATHS = [Path(__file__).parent / "cn"]


# 500 hPa height / MSLP shared table (h_500, psl)
register_rgb_table("cn_hgt20", np.array([
    (255, 255, 255),
    (0, 0, 0),
    (20, 100, 210),
    (40, 130, 240),
    (80, 165, 245),
    (150, 210, 250),
    (180, 240, 250),
    (203, 248, 253),
    (255, 255, 255),
    (180, 250, 170),
    (120, 245, 115),
    (55, 210, 60),
    (30, 180, 30),
    (15, 160, 15),
    (0, 0, 255),
    (255, 0, 0),
    (255, 140, 0),
    (238, 18, 137),
    (255, 121, 121),
    (211, 211, 211),
], dtype=float) / 255)


# 10m wind speed / 850 hPa wind speed shared table (ws_10m, ws_850)
register_rgb_table("cn_ws15", np.array([
    (255, 255, 255),
    (0, 0, 0),
    (255, 255, 255),
    (0, 200, 200),
    (0, 210, 140),
    (0, 220, 0),
    (160, 230, 50),
    (230, 220, 50),
    (230, 175, 45),
    (240, 130, 40),
    (250, 60, 60),
    (240, 0, 130),
    (0, 0, 255),
    (255, 140, 0),
    (238, 18, 137)
], dtype=float) / 255)


# composite radar reflectivity table (cdbz)
register_rgb_table("cn_cr19", np.array([
    (255, 255, 255),
    (0, 0, 0),
    (216, 216, 216),
    (1, 160, 246),
    (0, 236, 236),
    (0, 216, 0),
    (1, 144, 0),
    (255, 255, 0),
    (231, 192, 0),
    (255, 144, 0),
    (255, 0, 0),
    (214, 0, 0),
    (192, 0, 0),
    (255, 0, 240),
    (150, 0, 180),
    (173, 144, 240),
    (255, 140, 0),
    (238, 18, 137),
    (0, 0, 128)
], dtype=float) / 255)


# pseudo-equivalent potential temperature (pte): NCL subset + appended white
_pte_colormap = get_ncl_colormap(
    "BkBlAqGrYeOrReViWh200",
    index=np.array([175, 160, 156, 140, 125, 110, 100, 90, 80, 60]) - 2,
)
register_rgb_table("cn_pte", list(_pte_colormap.colors) + [[1, 1, 1, 1]])


# dew point depression (t_dew_t): NCL testcmap + two extra colors
_tdew_colormap = get_ncl_colormap("testcmap")
register_rgb_table("cn_tdew", list(_tdew_colormap.colors) + [
    (255 / 255, 0, 255 / 255),
    (77 / 255, 77 / 255, 77 / 255),
])


# vertical wind shear (shr): NCL table + user named colors
_shr_ncl_colormap = get_ncl_colormap("WhViBlGrYeOrRe")
_shr_user_colormap = generate_colormap_using_ncl_colors(
    [
        "aquamarine",
        "RoyalBlue",
        "LightSkyBlue",
        "blue",
        "PowderBlue",
        "lightseagreen",
        "PaleGreen",
        "Wheat",
        "Brown",
        "DarkOliveGreen3",
        "red",
        "Green",
        "forestgreen",
        "deepSkyBlue",
        "Blue",
        "mediumpurple1",
        "Magenta",
        "darkorange3",
    ],
    "user",
)
register_rgb_table(
    "cn_shr",
    np.concatenate((_shr_ncl_colormap.colors, _shr_user_colormap.colors), axis=0),
)

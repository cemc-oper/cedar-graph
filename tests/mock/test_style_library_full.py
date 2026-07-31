"""Full style library vs hardcoded styles: item-by-item comparison (T-2.5).

Covers every style migrated from the 18 plot modules beyond the T-2.4
pilots: rh2m, ws_10m/ws_850, rain (all interval variants + cn/cn_prep),
sf, rain_snow, cdbz, bli, cape, cin, div, qdiv, pte_diff, t_dew_t, shr.
"""
import numpy as np
import matplotlib.colors as mcolors
import pandas as pd
import pytest

from cedarkit.plots.colormap import generate_colormap_using_ncl_colors, get_ncl_colormap
from cedarkit.plots.style import ColorbarStyle, ContourLabelStyle, ContourStyle, StyleRegistry

from .test_style_library import assert_contour_style_equal


@pytest.fixture(scope="module")
def registry() -> StyleRegistry:
    return StyleRegistry.default()


CN_WS15 = np.array([
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
], dtype=float) / 255


class TestRh2m:
    """plots/cn/rh_2m/default.py"""

    def test_cn(self, registry):
        color_map = get_ncl_colormap("rainbow+white+gray")
        color_index = np.arange(90, 236, 20)
        color_index[0] = 236
        expected = ContourStyle(
            colors=mcolors.ListedColormap(color_map(color_index)),
            levels=np.linspace(70, 100, 7, endpoint=True),
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("rh2m"), expected)


class TestWindSpeed:
    def test_ws_10m(self, registry):
        """plots/cn/wind_10m/default.py"""
        colormap = mcolors.ListedColormap(CN_WS15)
        expected = ContourStyle(
            colors=mcolors.ListedColormap(colormap(np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 11]))),
            levels=np.array([3.4, 5.5, 8, 10.8, 13.9, 17.2, 20.8, 24.5, 28.5]),
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("ws_10m"), expected)

    def test_ws_850(self, registry):
        """plots/cn/height_500_wind_850/default.py"""
        colormap = mcolors.ListedColormap(CN_WS15)
        expected = ContourStyle(
            colors=mcolors.ListedColormap(colormap(np.array([2, 4, 5, 6, 7, 9, 10, 11]))),
            levels=np.array([12, 15, 18, 21, 24, 27, 30], dtype=int),
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("ws_850"), expected)


class TestRain:
    def test_cn(self, registry):
        """plots/cn/rain_24h/default.py"""
        expected = ContourStyle(
            colors=generate_colormap_using_ncl_colors(
                ["transparent", "White", "DarkOliveGreen3", "forestgreen",
                 "deepSkyBlue", "Blue", "Magenta", "deeppink4"],
                name="rain",
            ),
            levels=np.array([0.1, 10, 25, 50, 100, 200]),
            fill=True,
            colorbar_style=ColorbarStyle(label="rain"),
        )
        actual = registry.get_style("rain", "cn")
        assert_contour_style_equal(actual, expected)
        assert actual.colorbar_style.label == "rain"

    def test_cn_prep(self, registry):
        """plots/cn/prep_24h/default.py (rain)"""
        expected = ContourStyle(
            colors=generate_colormap_using_ncl_colors(
                ["transparent", "PaleGreen2", "ForestGreen", "DeepSkyBlue",
                 "blue1", "magenta1", "DeepPink3", "DarkOrchid4"],
                name="rain",
            ),
            levels=np.array([0.1, 10, 25, 50, 100, 250]),
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("rain", "cn_prep"), expected)

    @pytest.mark.parametrize("hours,colors,levels", [
        (1, ["White", "DarkOliveGreen1", "DarkOliveGreen3", "forestgreen", "deepSkyBlue",
             "Blue", "darkgreen", "Magenta", "darkorange", "deeppink4"],
         [0.1, 1, 2, 4, 6, 8, 10, 20, 50]),
        (3, ["White", "paleGreen2", "forestgreen", "deepSkyBlue", "Blue", "Magenta", "deeppink4"],
         [0.1, 3, 10, 20, 50, 70]),
        (6, ["White", "paleGreen2", "forestgreen", "deepSkyBlue", "Blue", "Magenta"],
         [0.1, 4, 13, 25, 60]),
        (12, ["White", "paleGreen2", "forestgreen", "deepSkyBlue", "Blue", "Magenta", "deeppink4"],
         [0.1, 5, 15, 30, 70, 140]),
        (24, ["transparent", "White", "paleGreen2", "forestgreen", "deepSkyBlue",
              "Blue", "Magenta", "deeppink4"],
         [0.1, 10, 25, 50, 100, 200]),
    ])
    def test_interval_variants(self, registry, hours, colors, levels):
        """plots/cn/rain_wind_10m/default.py"""
        expected = ContourStyle(
            colors=generate_colormap_using_ncl_colors(colors, f"rain_{hours}h_colormap"),
            levels=np.array(levels),
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("rain", f"cn_{hours}h"), expected)


class TestPrep24h:
    def test_snow(self, registry):
        """plots/cn/prep_24h/default.py (snow)"""
        expected = ContourStyle(
            colors=get_ncl_colormap("mch_default", index=np.array([0, 7, 6, 5, 4, 3, 1])),
            levels=np.array([0.1, 2.5, 5, 10, 20, 30]),
            fill=True,
        )
        actual = registry.get_style("sf")
        assert_contour_style_equal(actual, expected)
        assert actual.colorbar_style.label == "snow"

    def test_rain_snow(self, registry):
        """plots/cn/prep_24h/default.py (mix)"""
        expected = ContourStyle(
            colors=get_ncl_colormap("precip_diff_12lev", index=np.array([6, 5, 4, 3, 2, 1])),
            levels=np.array([0.1, 10, 25, 50, 100]),
            fill=True,
        )
        actual = registry.get_style("rain_snow")
        assert_contour_style_equal(actual, expected)
        assert actual.colorbar_style.label == "mix"


class TestCdbz:
    """plots/cn/radar_reflectivity/default.py"""

    CN_CR19 = np.array([
        (255, 255, 255), (0, 0, 0), (216, 216, 216), (1, 160, 246), (0, 236, 236),
        (0, 216, 0), (1, 144, 0), (255, 255, 0), (231, 192, 0), (255, 144, 0),
        (255, 0, 0), (214, 0, 0), (192, 0, 0), (255, 0, 240), (150, 0, 180),
        (173, 144, 240), (255, 140, 0), (238, 18, 137), (0, 0, 128)
    ], dtype=float) / 255

    def test_cn(self, registry):
        colormap = mcolors.ListedColormap(self.CN_CR19)
        expected = ContourStyle(
            colors=mcolors.ListedColormap(colormap(np.array([0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]))),
            levels=np.arange(10, 75, 5),
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("cdbz"), expected)


class TestBli:
    """plots/cn/bli_wind/default.py"""

    LEVELS = np.array([-48, -42, -36, -30, -24, -18, -12, -6, 0])

    def test_cn_fill(self, registry):
        colormap_index = np.array([20, 19, 18, 16, 14, 12, 10, 8, 6, 4]) - 2
        expected = ContourStyle(
            colors=get_ncl_colormap("prcp_3", index=colormap_index),
            levels=self.LEVELS,
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("bli", "cn_fill"), expected)

    def test_cn_line(self, registry):
        expected = ContourStyle(
            colors="black",
            levels=self.LEVELS,
            linewidths=0.5,
            fill=False,
            label=True,
            label_style=ContourLabelStyle(fontsize=7, background_color="white"),
        )
        assert_contour_style_equal(registry.get_style("bli", "cn_line"), expected)


class TestCape:
    """plots/cn/cape_wind/default.py"""

    LEVELS = np.array([
        0, 10, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000,
        1100, 1200, 1300, 1400, 1500, 1750, 2000, 2250, 2500
    ])

    def test_cn_fill(self, registry):
        color_index = np.array([2, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52, 57, 62, 67, 72, 77, 82, 87, 90, 93, 96, 99, 101]) - 2
        expected = ContourStyle(
            colors=get_ncl_colormap("WhBlGrYeRe", index=color_index),
            levels=self.LEVELS,
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("cape", "cn_fill"), expected)

    def test_cn_line(self, registry):
        color_index = np.array([2, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52, 57, 62, 67, 72, 77, 82, 87, 90, 93, 96, 99, 101]) - 2
        cape_colormap = get_ncl_colormap("WhBlGrYeRe", index=color_index)
        expected = ContourStyle(
            colors=[cape_colormap.colors[0]],
            levels=self.LEVELS,
            linewidths=0.15,
            fill=False,
        )
        actual = registry.get_style("cape", "cn_line")
        # built as a 1-color ListedColormap; equivalent single color
        np.testing.assert_allclose(
            np.asarray(actual.colors.colors), np.asarray([expected.colors[0]])
        )
        np.testing.assert_allclose(actual.levels, expected.levels)
        assert actual.linewidths == 0.15
        assert actual.fill is False


class TestCin:
    """plots/cn/cin_wind/default.py"""

    def test_cn(self, registry):
        color_index = np.array([0, 64, 67, 70, 73, 76, 79, 82, 85, 88, 91, 94, 97])
        expected = ContourStyle(
            colors=get_ncl_colormap("WhViBlGrYeOrRe", index=color_index),
            levels=np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 100, 150, 200]),
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("cin"), expected)


class TestDiv:
    """plots/cn/div_wind/default.py"""

    LEVELS = np.arange(-50, -5 + 5, 5)

    def test_cn_fill(self, registry):
        expected = ContourStyle(
            colors=get_ncl_colormap("WhBlGrYeRe", count=len(self.LEVELS) + 1, spread_start=98, spread_end=0),
            levels=self.LEVELS,
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("div", "cn_fill"), expected)

    def test_cn_line(self, registry):
        expected = ContourStyle(
            colors="black",
            levels=self.LEVELS,
            linewidths=0.5,
            linestyles="solid",
            fill=False,
            label=True,
            label_style=ContourLabelStyle(fontsize=7, background_color="white"),
        )
        actual = registry.get_style("div", "cn_line")
        assert_contour_style_equal(actual, expected)
        assert actual.linestyles == "solid"


class TestQvDiv:
    """plots/cn/qv_div/default.py"""

    LEVELS = np.arange(-50, -5 + 5, step=5)

    def test_cn_fill(self, registry):
        expected = ContourStyle(
            colors=get_ncl_colormap("WhBlGrYeRe", count=len(self.LEVELS) + 1, spread_start=100 - 2, spread_end=2 - 2),
            levels=self.LEVELS,
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("qdiv", "cn_fill"), expected)

    def test_cn_line(self, registry):
        expected = ContourStyle(
            colors="black",
            levels=self.LEVELS,
            linewidths=0.2,
            linestyles="-",
            fill=False,
        )
        actual = registry.get_style("qdiv", "cn_line")
        assert_contour_style_equal(actual, expected)
        assert actual.linestyles == "-"


class TestPteDiff:
    """plots/cn/pte_wind/default.py"""

    LEVELS = np.array([-40, -35, -30, -25, -20, -15, -10, -5, 0, 5])

    def _color_map(self):
        color_index = np.array([175, 160, 156, 140, 125, 110, 100, 90, 80, 60]) - 2
        ncl_color_map = get_ncl_colormap("BkBlAqGrYeOrReViWh200", index=color_index)
        ncl_colors = ncl_color_map.colors
        ncl_colors.append([1, 1, 1, 1])
        return mcolors.ListedColormap(ncl_colors, "plot_colormap")

    def test_cn_fill(self, registry):
        expected = ContourStyle(
            colors=self._color_map(),
            levels=self.LEVELS,
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("pte_diff", "cn_fill"), expected)

    def test_cn_line(self, registry):
        expected = ContourStyle(
            colors="black",
            levels=self.LEVELS,
            fill=False,
            linestyles="solid",
            linewidths=0.6,
            label=True,
            label_style=ContourLabelStyle(colors="black", background_color="white", fontsize=8),
        )
        actual = registry.get_style("pte_diff", "cn_line")
        assert_contour_style_equal(actual, expected)
        assert actual.linestyles == "solid"


class TestTDewT:
    """plots/cn/t_dew_t/default.py"""

    LEVELS = np.array([1, 3, 5, 7, 9, 11, 15, 17, 21, 25, 29, 33])

    def _color_map(self):
        map_colors = np.array([(255, 0, 255), (77, 77, 77)], dtype=float) / 255.0
        ncl_color_map = get_ncl_colormap("testcmap")
        return mcolors.ListedColormap(
            np.concatenate((ncl_color_map.colors, map_colors), axis=0),
            "plot_colormap",
        )

    def test_cn_fill(self, registry):
        color_map = self._color_map()
        color_index = np.array([65, 70, 75, 80, 85, 100, 115, 130, 150, 160, 170, 180, 190]) - 2
        expected = ContourStyle(
            colors=mcolors.ListedColormap(color_map(color_index), "t_dew_t_diff_colormap"),
            levels=self.LEVELS,
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("t_dew_t", "cn_fill"), expected)

    def test_cn_line(self, registry):
        color_map = self._color_map()
        line_color_index = np.array([65, 70, 201, 80, 85, 100, 115, 130, 150, 160, 170, 180, 190]) - 2
        expected = ContourStyle(
            levels=self.LEVELS,
            colors=mcolors.ListedColormap(color_map(line_color_index), "t_dew_t_diff_line_colormap"),
            linewidths=np.array([0.1, 0.1, 2.0, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]),
        )
        assert_contour_style_equal(registry.get_style("t_dew_t", "cn_line"), expected)

    def test_cn_t(self, registry):
        color_map = self._color_map()
        t_levels = np.linspace(start=-80, stop=80, num=81, endpoint=True)
        t_lines_color = color_map(30 - 2)
        t_line_colors = [
            (0, 0, 0, 0) if current_level == 0 else t_lines_color
            for current_level in t_levels
        ]
        expected = ContourStyle(
            colors=t_line_colors,
            levels=t_levels,
            linewidths=np.where(t_levels == 0, 2.0, 1.0),
            linestyles="solid",
            fill=False,
            label=True,
            label_style=ContourLabelStyle(colors=t_line_colors, background_color="white"),
        )
        actual = registry.get_style("t_dew_t", "cn_t")
        assert_contour_style_equal(actual, expected)
        assert actual.linestyles == "solid"
        np.testing.assert_allclose(np.asarray(actual.label_style.colors), np.asarray(t_line_colors))


class TestShr:
    """plots/cn/shr/default.py — levels computed at runtime; colormap from library."""

    def test_cn_fill_colormap(self, registry):
        ncl_colormap = get_ncl_colormap("WhViBlGrYeOrRe")
        user_colormap = generate_colormap_using_ncl_colors(
            ["aquamarine", "RoyalBlue", "LightSkyBlue", "blue", "PowderBlue",
             "lightseagreen", "PaleGreen", "Wheat", "Brown", "DarkOliveGreen3",
             "red", "Green", "forestgreen", "deepSkyBlue", "Blue",
             "mediumpurple1", "Magenta", "darkorange3"],
            "user",
        )
        color_map = mcolors.ListedColormap(
            np.concatenate((ncl_colormap.colors, user_colormap.colors), axis=0),
            "color_map",
        )
        color_index = np.array([2, 4, 5, 6, 8, 13, 69, 73, 76, 79, 65, 64, 63, 62, 60, 58, 35]) - 2
        expected_colors = mcolors.ListedColormap(color_map(color_index), "vwsh_color_map")

        actual = registry.get_style("shr", "cn_fill")
        assert actual.fill is True
        assert actual.levels is None
        np.testing.assert_allclose(np.asarray(actual.colors.colors), np.asarray(expected_colors.colors))

    def test_cn_line(self, registry):
        actual = registry.get_style("shr", "cn_line")
        assert actual.colors == "blue"
        assert actual.linewidths == 0.3
        assert actual.levels is None

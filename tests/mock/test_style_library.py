"""Pilot style library vs hardcoded styles: item-by-item comparison (T-2.4).

Rebuilds the style constructions currently hardcoded in the plot modules
(t_2m, height_500_mslp, k_wind, wind barbs) and compares them with the
styles built from ``cedar_graph/styles/cn/*.yml`` through the default
StyleRegistry.
"""
import numpy as np
import matplotlib.colors as mcolors
import pytest

from cedarkit.plots.colormap import get_ncl_colormap
from cedarkit.plots.style import (
    BarbStyle,
    ContourLabelStyle,
    ContourStyle,
    StyleRegistry,
)


@pytest.fixture(scope="module")
def registry() -> StyleRegistry:
    return StyleRegistry.default()


def assert_colormap_equal(actual, expected):
    if isinstance(expected, mcolors.Colormap):
        assert isinstance(actual, mcolors.Colormap)
        # normalize rows: NCL color lists may mix RGB and RGBA rows
        actual_rgba = np.asarray([mcolors.to_rgba(c) for c in actual.colors])
        expected_rgba = np.asarray([mcolors.to_rgba(c) for c in expected.colors])
        np.testing.assert_allclose(actual_rgba, expected_rgba)
    elif isinstance(actual, mcolors.Colormap):
        # the library builds a Colormap where the original passed a plain
        # color list; layer.contour converts one to the other — equivalent.
        actual_rgba = np.asarray([mcolors.to_rgba(c) for c in actual.colors])
        expected_rgba = np.asarray([mcolors.to_rgba(c) for c in expected])
        np.testing.assert_allclose(actual_rgba, expected_rgba)
    else:
        assert actual == expected


def assert_contour_style_equal(actual: ContourStyle, expected: ContourStyle):
    assert actual.fill == expected.fill
    assert actual.label == expected.label
    if expected.levels is not None:
        np.testing.assert_allclose(np.asarray(actual.levels, dtype=float), np.asarray(expected.levels, dtype=float))
    else:
        assert actual.levels is None
    assert_colormap_equal(actual.colors, expected.colors)
    if expected.linewidths is not None:
        np.testing.assert_allclose(np.asarray(actual.linewidths, dtype=float), np.asarray(expected.linewidths, dtype=float))
    else:
        assert actual.linewidths is None
    if expected.label_style is not None:
        assert_label_style_equal(actual.label_style, expected.label_style)


def assert_label_style_equal(actual: ContourLabelStyle, expected: ContourLabelStyle):
    assert actual.inline == expected.inline
    assert actual.fontsize == expected.fontsize
    assert actual.background_color == expected.background_color
    if expected.fmt is not None:
        assert actual.fmt(588.0) == expected.fmt(588.0)
    if expected.colors is not None:
        if isinstance(expected.colors, str):
            assert actual.colors == expected.colors
        else:
            np.testing.assert_allclose(np.asarray(actual.colors), np.asarray(expected.colors))


CN_HGT20 = np.array([
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
], dtype=float) / 255


class TestT2m:
    """plots/cn/t_2m/default.py"""

    @pytest.mark.parametrize("month", [6, 1])
    def test_seasonal_style(self, registry, month):
        color_map = get_ncl_colormap("BlAqGrYeOrReVi200")
        if 5 <= month <= 9:
            levels = [-12, -8, -4, 0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44]
            color_index = np.array([2, 18, 34, 50, 66, 82, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]) - 2
            variant = "cn_summer"
        else:
            levels = [-24, -20, -16, -12, -8, -4, 0, 4, 8, 12, 16, 20, 24, 28, 32]
            color_index = np.array([2, 12, 22, 32, 42, 52, 62, 72, 82, 92, 102, 112, 122, 132, 142, 152]) - 2
            variant = "cn_winter"
        expected = ContourStyle(
            colors=mcolors.ListedColormap(color_map(color_index)),
            levels=levels,
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("t2m", variant), expected)


class TestH500:
    """plots/cn/height_500_mslp/default.py (hgt_style)"""

    def test_cn_dagpm(self, registry):
        colormap = mcolors.ListedColormap(CN_HGT20)
        levels = np.linspace(500, 588, endpoint=True, num=23)
        expected = ContourStyle(
            levels=levels,
            colors=mcolors.ListedColormap(colormap(np.where(levels == 588, 1, 14))),
            linewidths=np.where(levels == 588, 1.4, 0.7),
            label=True,
            label_style=ContourLabelStyle(
                manual=False,
                inline=True,
                fontsize=7,
                fmt="{:.0f}".format,
                colors=colormap([15]),
            ),
        )
        assert_contour_style_equal(registry.get_style("h_500", "cn_dagpm"), expected)

    def test_cn_ws(self, registry):
        """plots/cn/height_500_wind_850/default.py (hgt_style)"""
        colormap = mcolors.ListedColormap(CN_HGT20)
        levels = np.linspace(500, 588, endpoint=True, num=23)
        expected = ContourStyle(
            levels=levels,
            colors=mcolors.ListedColormap(colormap(np.full(len(levels), 12))),
            linewidths=np.where(levels == 588, 1.4, 0.7),
            label=True,
            label_style=ContourLabelStyle(
                manual=False,
                inline=True,
                fontsize=7,
                fmt="{:.0f}".format,
            ),
        )
        assert_contour_style_equal(registry.get_style("h_500", "cn_ws"), expected)


class TestPsl:
    """plots/cn/height_500_mslp/default.py (mslp_style)"""

    def test_cn(self, registry):
        colormap = mcolors.ListedColormap(CN_HGT20)
        expected = ContourStyle(
            colors=mcolors.ListedColormap(colormap(np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]))),
            levels=np.array([980, 985, 990, 995, 1000, 1005, 1020, 1025, 1030, 1035, 1040]),
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("psl", "cn"), expected)


class TestKidx:
    """plots/cn/k_wind/default.py"""

    LEVELS = np.array([20, 25, 30, 35, 40, 45, 50])

    def test_cn_fill(self, registry):
        expected = ContourStyle(
            colors=get_ncl_colormap("WhBlGrYeRe", index=[0, 15, 45, 55, 65, 75, 85, 95, 100]),
            levels=self.LEVELS,
            fill=True,
        )
        assert_contour_style_equal(registry.get_style("kidx", "cn_fill"), expected)

    def test_cn_line(self, registry):
        expected = ContourStyle(
            colors="black",
            levels=self.LEVELS,
            linewidths=0.5,
            fill=False,
            label=True,
            label_style=ContourLabelStyle(
                fontsize=7,
                background_color="white",
            ),
        )
        assert_contour_style_equal(registry.get_style("kidx", "cn_line"), expected)


class TestWind:
    """BarbStyle shared by wind_10m, k_wind, rain_wind_10m, ..."""

    def test_cn(self, registry):
        style = registry.get_style("wind", "cn")
        assert isinstance(style, BarbStyle)
        expected = BarbStyle(barbcolor="black", flagcolor="black", linewidth=0.3)
        assert style.barbcolor == expected.barbcolor
        assert style.flagcolor == expected.flagcolor
        assert style.linewidth == expected.linewidth
        assert style.length == expected.length
        assert style.pivot == expected.pivot
        assert style.barb_increments == expected.barb_increments

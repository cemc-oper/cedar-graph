"""
Mock data source for tests and documentation examples.

The :class:`MockDataSource` defined here generates synthetic
:class:`xarray.DataArray` objects on a regular latitude/longitude grid
covering the East Asia domain. Field values are computed from
deterministic analytic patterns keyed by ``field_info.name``, so that
both the unit tests and the docs gallery produce identical output
without requiring access to real NWP data files on CMA-HPC.

The patterns are not full atmospheric simulations but are designed to
be **physically plausible** at first glance:

- Pressure-level fields (``t``, ``dpt``, ``h``) depend on
  ``field_info.level`` with a realistic lapse rate / hypsometric
  scaling, so the same plot called at 850 hPa and 500 hPa gives
  visibly different and reasonable results.
- Wind components (``u``, ``v``) differ between 10 m and pressure
  levels (boundary-layer monsoonal flow vs. mid-latitude jet plus
  low-level southwesterly).
- ``t2m`` follows seasonal magnitudes derived from ``start_time``.
- ``mslp`` carries a summer East Asian pattern (continental thermal
  low + Pacific subtropical high) by default.
- Convective fields (``cape``, ``cin``, ``cr``, ``apcp``) are masked
  to a localized "active region" so the rest of the domain looks
  quiescent, the way a real diagnostic field usually does.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import xarray as xr

from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import FieldInfo
from cedar_graph.data.source import DataSource


class MockDataSource(DataSource):
    """
    A mock data source that generates synthetic 2D fields.

    The generated fields cover the East Asia domain
    (60°E–150°E, 0°–70°N) at the requested resolution and produce
    smooth spatial patterns suitable for exercising the full plotting
    pipeline.

    Parameters
    ----------
    resolution
        Grid spacing in degrees for both longitude and latitude.
        Defaults to ``0.25``.
    """

    def __init__(self, resolution: float = 0.25):
        super().__init__()
        self.resolution = resolution
        # Grid covering East Asia + buffer
        self.lon = np.arange(60, 150 + resolution, resolution)
        self.lat = np.arange(70, 0 - resolution, -resolution)
        self._lon2d, self._lat2d = np.meshgrid(self.lon, self.lat)

    def retrieve(
            self,
            field_info: FieldInfo,
            start_time: pd.Timestamp,
            forecast_time: pd.Timedelta,
            **kwargs,
    ) -> xr.DataArray:
        """
        Generate a synthetic field based on ``field_info``.

        Different field types produce different value ranges and spatial
        structures, so the plot styles (colormaps, contour levels) and
        physical sanity checks both pass.

        Parameters
        ----------
        field_info
            Field descriptor. The mock consults ``field_info.name`` as
            the primary key; for fields where the name is reused
            (e.g. ``cape`` is shared by CAPE and CIN), the
            ``parameter.wgrib2_name`` is used as a tiebreaker.
            ``level_type`` and ``level`` select boundary-layer vs.
            pressure-level branches.
        start_time
            Forecast start time. Used for seasonality of ``t2m`` and
            ``mslp``.
        forecast_time
            Forecast lead time. Used by accumulated fields (e.g. APCP,
            ASNOW) so that ``F(t) - F(t - dt)`` is non-zero and the
            rain plots show meaningful coverage.

        Returns
        -------
        xarray.DataArray
            Two-dimensional array with ``latitude`` and ``longitude``
            coordinates.
        """
        return self._generate_field(
            field_info,
            start_time=start_time,
            forecast_time=forecast_time,
        )

    def _generate_field(
            self,
            field_info: FieldInfo,
            start_time: Optional[pd.Timestamp] = None,
            forecast_time: pd.Timedelta = pd.Timedelta(0),
    ) -> xr.DataArray:
        """Generate a synthetic field with values appropriate for the field type."""
        lon2d = self._lon2d
        lat2d = self._lat2d
        # Hours of lead time (used by accumulated fields).
        hours = float(forecast_time / pd.Timedelta(hours=1)) if forecast_time is not None else 0.0
        month = start_time.month if start_time is not None else 7

        name = field_info.name
        # Use deterministic seed based on field name for reproducibility.
        seed = sum(ord(c) for c in name)
        rng = np.random.default_rng(seed)

        if name == "t2m":
            values = self._t2m(lat2d, lon2d, month=month)
        elif name == "t":
            values = self._t_pressure(lat2d, lon2d, level=field_info.level)
        elif name == "rh2m":
            values = self._rh2m(lat2d, lon2d)
        elif name == "h":
            values = self._geopotential_height(lat2d, lon2d, level=field_info.level)
        elif name == "mslp":
            values = self._mslp(lat2d, lon2d, month=month)
        elif name in ("u", "v"):
            values = self._wind_component(
                component=name,
                level_type=field_info.level_type,
                level=field_info.level,
                lat2d=lat2d,
                lon2d=lon2d,
            )
        elif name == "cr":
            values = self._radar_reflectivity(lat2d, lon2d)
        elif name == "apcp":
            values = self._accumulated_precip(lat2d, lon2d, hours=hours, rng=rng)
        elif name == "asnow":
            values = self._accumulated_snow(lat2d, lon2d, hours=hours)
        elif name == "div":
            values = self._divergence(lat2d, lon2d)
        elif name == "k":
            values = self._k_index(lat2d, lon2d)
        elif name == "cape":
            # Both CAPE and CIN share name="cape"; distinguish by the
            # WGRIB2 name carried in ``Parameter``.
            wgrib2_name = (
                field_info.parameter.wgrib2_name
                if field_info.parameter is not None else None
            )
            if wgrib2_name == "CIN":
                values = self._cin(lat2d, lon2d)
            else:
                values = self._cape(lat2d, lon2d)
        elif name == "bli":
            values = self._best_lifted_index(lat2d, lon2d)
        elif name == "qv_div":
            values = self._moisture_flux_divergence(lat2d, lon2d)
        elif name == "pte":
            values = self._pte(lat2d, lon2d, level=field_info.level)
        elif name == "vwsh":
            values = self._vertical_wind_shear(lat2d, lon2d)
        elif name == "dpt":
            values = self._dew_point(lat2d, lon2d, level=field_info.level)
        else:
            # Generic field
            values = 10.0 * np.sin(np.deg2rad(lat2d * 2)) * np.cos(np.deg2rad(lon2d * 2))

        da = xr.DataArray(
            values,
            dims=["latitude", "longitude"],
            coords={"latitude": self.lat, "longitude": self.lon},
            name=name,
        )
        return da

    # ------------------------------------------------------------------
    # Field-specific generators
    # ------------------------------------------------------------------

    @staticmethod
    def _t2m(lat2d: np.ndarray, lon2d: np.ndarray, month: int) -> np.ndarray:
        """
        2 m temperature (K).

        Roughly follows seasonal mean magnitudes over East Asia. The
        ``cn.t_2m`` plot style uses [-12, 44] °C bands for warm season
        (May–Sep) and [-24, 32] °C for the cold half-year, so we shift
        the latitude curve accordingly.
        """
        warm = 5 <= month <= 9
        # Warm season: ~30 °C at the equator, ~12 °C at 70°N.
        # Cold season: ~22 °C at the equator, ~−18 °C at 70°N.
        if warm:
            base_c = 30.0 - 0.30 * lat2d
        else:
            base_c = 22.0 - 0.55 * lat2d

        # Land-sea / continental contrast: stronger amplitude over land
        # (continent peaks roughly between 80°E and 130°E in this domain).
        continental = np.exp(-((lon2d - 105.0) / 25.0) ** 2)
        # In summer the continent is hotter than the ocean at the same
        # latitude; in winter it is colder.
        contrast = (4.0 if warm else -8.0) * continental * np.cos(
            np.deg2rad(np.clip(lat2d - 35.0, -45.0, 45.0))
        )

        # Mesoscale waviness so the gallery field is not flat.
        wave = 1.5 * np.sin(np.deg2rad(lat2d * 4)) * np.cos(
            np.deg2rad(lon2d * 3)
        )

        return 273.15 + base_c + contrast + wave

    @staticmethod
    def _t_pressure(
            lat2d: np.ndarray, lon2d: np.ndarray, level
    ) -> np.ndarray:
        """
        Air temperature on a pressure surface (K).

        Implements a crude but level-aware thermal profile so the same
        plot at 850 / 700 / 500 hPa returns visibly different fields:
        ``T(p) ≈ T_sfc − Γ · z(p)`` with ``Γ = 6.5 K/km`` and
        ``z(p) ≈ 8000 · ln(1000/p)``.
        """
        level_value = MockDataSource._level_value(level, default=850.0)

        # Surface temperature in K, with a strong meridional gradient
        # plus a small east-west wave pattern.
        t_surface = 300.0 - 0.5 * lat2d + 2.0 * np.sin(np.deg2rad(lon2d * 2))
        # Altitude in metres above the 1000 hPa "surface" via the
        # hypsometric approximation.
        altitude = 8000.0 * np.log(1000.0 / max(level_value, 1.0))
        # Standard tropospheric lapse rate of 6.5 K/km.
        return t_surface - 6.5e-3 * altitude

    @staticmethod
    def _rh2m(lat2d: np.ndarray, lon2d: np.ndarray) -> np.ndarray:
        """
        2 m relative humidity (%).

        Higher humidity over the south-east monsoon region; lower over
        the inland north-west. Clipped to a realistic 25–98 % range.
        """
        # Decreases away from the moist south-east corner.
        moisture = 70.0 + 25.0 * np.exp(-((lat2d - 25.0) / 18.0) ** 2) * np.exp(
            -((lon2d - 115.0) / 25.0) ** 2
        )
        # Add some synoptic structure.
        moisture += 8.0 * np.sin(np.deg2rad(lat2d * 2)) * np.cos(
            np.deg2rad(lon2d)
        )
        return np.clip(moisture, 25.0, 98.0)

    @staticmethod
    def _geopotential_height(
            lat2d: np.ndarray, lon2d: np.ndarray, level
    ) -> np.ndarray:
        """
        Geopotential height (gpm).

        Built from the hypsometric mean ``Z(p) ≈ 8000 · ln(1000/p)``
        plus a meridional gradient (poles lower, subtropics higher) and
        a synoptic-scale ridge/trough wave train.
        """
        level_value = MockDataSource._level_value(level, default=500.0)

        base = 8000.0 * np.log(1000.0 / max(level_value, 1.0))
        # Meridional gradient: highest at low latitudes, lowest at the
        # pole. Amplitude scales with height so 500 hPa varies more
        # than 850 hPa.
        meridional_amp = 100.0 + 1.2 * (1000.0 - level_value)
        meridional = meridional_amp * (1.0 - lat2d / 70.0)
        # Synoptic wave train (zonal wavenumber ~3) for ridges/troughs.
        wave = 80.0 * np.cos(np.deg2rad(lon2d * 3.0)) * np.sin(
            np.deg2rad(np.clip(lat2d, 10.0, 60.0) * 2.5)
        )
        return base + meridional + wave

    @staticmethod
    def _mslp(lat2d: np.ndarray, lon2d: np.ndarray, month: int) -> np.ndarray:
        """
        Mean sea level pressure (Pa).

        Default summer (NH) configuration: a continental thermal low
        over inland Asia and the Pacific subtropical high south-east of
        Japan. In winter the centres flip sign (Siberian high +
        Aleutian low).
        """
        warm = 5 <= month <= 9

        # Continental thermal low / Siberian high (centre over inland Asia).
        cont_lat, cont_lon = 45.0, 95.0
        cont_amp = -1500.0 if warm else 2500.0
        continental = cont_amp * np.exp(
            -((lat2d - cont_lat) / 14.0) ** 2
            - ((lon2d - cont_lon) / 20.0) ** 2
        )

        # Pacific subtropical high / Aleutian low (centre over the ocean).
        pac_lat, pac_lon = 30.0, 145.0
        pac_amp = 1800.0 if warm else -1200.0
        pacific = pac_amp * np.exp(
            -((lat2d - pac_lat) / 10.0) ** 2
            - ((lon2d - pac_lon) / 18.0) ** 2
        )

        # Mid-latitude wave train.
        wave = 350.0 * np.cos(np.deg2rad(lon2d * 2.5)) * np.sin(
            np.deg2rad(np.clip(lat2d, 30.0, 60.0) * 3.0)
        )
        return 101325.0 + continental + pacific + wave

    @staticmethod
    def _wind_component(
            component: str,
            level_type,
            level,
            lat2d: np.ndarray,
            lon2d: np.ndarray,
    ) -> np.ndarray:
        """
        Wind component (m/s) tailored to surface vs. pressure level.

        - 10 m wind (``level_type='heightAboveGround'``): weaker,
          dominated by a monsoonal southerly low-level flow with a
          land-sea contrast.
        - Pressure-level wind: a mid-latitude westerly jet centred near
          40°N, plus a low-level southwesterly tongue over south-east
          China that fades above 600 hPa. Higher levels (e.g. 200 hPa)
          have a broader, faster jet without the SW tongue.
        """
        is_surface = (
            level_type == "heightAboveGround"
            or (level_type is None and level == 10)
        )

        if is_surface:
            land_factor = 0.5 + 0.5 * np.tanh((25.0 - lat2d) / 8.0)
            if component == "u":
                return (
                    3.0
                    + 4.0 * land_factor * np.sin(np.deg2rad(lon2d - 100.0))
                )
            return 8.0 * land_factor + 2.0 * np.cos(
                np.deg2rad((lon2d - 110.0) * 1.5)
            )

        # Pressure-level branch.
        level_value = MockDataSource._level_value(level, default=850.0)

        # Mid-latitude westerly jet centred near 40°N.
        jet_lat = 40.0
        jet_width = 9.0 + (850.0 - level_value) / 100.0
        jet_strength = 18.0 + 0.04 * (850.0 - level_value)
        jet = jet_strength * np.exp(
            -((lat2d - jet_lat) ** 2) / (2.0 * jet_width ** 2)
        )

        # Low-level southwesterly tongue over SE China (only ≤700 hPa).
        ll_factor = np.clip((level_value - 600.0) / (850.0 - 600.0), 0.0, 1.0)
        sw_envelope = ll_factor * np.exp(
            -((lat2d - 28.0) / 6.0) ** 2
            - ((lon2d - 113.0) / 12.0) ** 2
        )

        if component == "u":
            return jet + 14.0 * sw_envelope + 1.5 * np.sin(
                np.deg2rad(lon2d * 1.5)
            )
        return (
            14.0 * sw_envelope
            + 3.0 * np.cos(np.deg2rad(lat2d * 1.5))
            * np.sin(np.deg2rad(lon2d * 2))
        )

    @staticmethod
    def _radar_reflectivity(
            lat2d: np.ndarray, lon2d: np.ndarray
    ) -> np.ndarray:
        """
        Composite radar reflectivity (dBZ).

        Most of the domain stays below the plot's 10 dBZ threshold
        (effectively no echo). A SW–NE oriented convective band over
        25–35°N brings 30–60 dBZ, with two embedded strong cells.
        """
        # Convective band aligned roughly along the Mei-yu/Baiu front.
        band_axis = lat2d - (28.0 + 0.18 * (lon2d - 100.0))
        band = np.exp(-(band_axis ** 2) / (2.0 * 2.5 ** 2))

        # A couple of intense embedded cells.
        cell1 = np.exp(
            -((lat2d - 30.0) / 1.5) ** 2 - ((lon2d - 112.0) / 2.0) ** 2
        )
        cell2 = np.exp(
            -((lat2d - 27.0) / 1.5) ** 2 - ((lon2d - 122.0) / 2.0) ** 2
        )

        # Stippled background to break up the smoothness.
        stipple = 0.5 + 0.5 * np.cos(np.deg2rad(lat2d * 12)) * np.sin(
            np.deg2rad(lon2d * 14)
        )

        values = (
            5.0  # baseline below the 10 dBZ plotting threshold
            + 35.0 * band * stipple
            + 25.0 * cell1
            + 25.0 * cell2
        )
        return np.clip(values, 0.0, 70.0)

    @staticmethod
    def _accumulated_precip(
            lat2d: np.ndarray,
            lon2d: np.ndarray,
            hours: float,
            rng: np.random.Generator,
    ) -> np.ndarray:
        """
        Accumulated precipitation since model initialisation (mm).

        Two structures:

        - A widespread light-rain band along the Mei-yu/Baiu axis
          (~10–30 mm in 24 h) that exercises the lower fill bands.
        - A localized heavy-precipitation core that exceeds 100 mm in
          24 h and lights up the top fill bands.

        The result depends on ``hours`` so the difference of two
        accumulations is non-zero (rain plots compute
        ``apcp(t) - apcp(t - dt)``).
        """
        band_axis = lat2d - (28.0 + 0.18 * (lon2d - 100.0))
        # Light rain over a broad band.
        light_rate = 1.2 * np.exp(-(band_axis ** 2) / (2.0 * 4.0 ** 2))  # mm/h

        # Heavy core embedded in the band (south-central China).
        heavy = np.exp(
            -((lat2d - 28.0) / 2.0) ** 2 - ((lon2d - 115.0) / 4.0) ** 2
        )
        heavy_rate = 7.0 * heavy  # peak ~7 mm/h => 168 mm in 24 h

        # Background drizzle so wide areas show up at the 0.1 mm band.
        drizzle = 0.05 * np.maximum(
            0.0, np.cos(np.deg2rad(lat2d * 2)) * np.sin(np.deg2rad(lon2d * 2))
        )

        rate = light_rate + heavy_rate + drizzle
        # Small noise so contour lines look natural.
        values = rate * hours + rng.uniform(0.0, 0.8, rate.shape)
        return np.clip(values, 0.0, None)

    @staticmethod
    def _accumulated_snow(
            lat2d: np.ndarray, lon2d: np.ndarray, hours: float
    ) -> np.ndarray:
        """
        Accumulated snow (m).

        Confined to mid- and high-latitude regions; the equatorward
        portion of the domain is snow-free, which lets the
        ``prep_24h`` plot decide which cells are rain vs. snow.
        """
        lat_factor = np.clip((lat2d - 30.0) / 30.0, 0.0, 1.0)
        rate = lat_factor * (
            0.5 * np.cos(np.deg2rad(lon2d * 2)) + 0.6
        ) * 4e-4  # m/hour
        return rate * hours

    @staticmethod
    def _divergence(lat2d: np.ndarray, lon2d: np.ndarray) -> np.ndarray:
        """
        Divergence (s⁻¹).

        Built as a dipole: strong convergence (negative) collocated
        with the precipitation band, weak divergence to the south. The
        ``div_wind`` plot multiplies by 1e5 and fills only negative
        bands (-50e-5 .. -5e-5 s⁻¹), so the converging part of the
        dipole is what shows up.
        """
        band_axis = lat2d - (28.0 + 0.18 * (lon2d - 100.0))
        convergence = -45e-5 * np.exp(-(band_axis ** 2) / (2.0 * 3.0 ** 2))
        divergence = 15e-5 * np.exp(
            -((lat2d - 18.0) / 5.0) ** 2 - ((lon2d - 115.0) / 12.0) ** 2
        )
        small_scale = 8e-5 * np.sin(np.deg2rad(lat2d * 4)) * np.cos(
            np.deg2rad(lon2d * 3)
        )
        return convergence + divergence + small_scale

    @staticmethod
    def _k_index(lat2d: np.ndarray, lon2d: np.ndarray) -> np.ndarray:
        """K index (°C). Higher values south, lower north."""
        base = 35.0 - 0.35 * lat2d
        wave = 6.0 * np.sin(np.deg2rad(lat2d * 2)) * np.cos(np.deg2rad(lon2d))
        return np.clip(base + wave, 0.0, 50.0)

    @staticmethod
    def _cape(lat2d: np.ndarray, lon2d: np.ndarray) -> np.ndarray:
        """
        Convective available potential energy (J/kg).

        Localized hot core south-east of the domain centre, sitting on
        a small-scale background. Lights up the high CAPE bands of
        ``cn.cape_wind`` while the rest stays in the 0..200 J/kg range.
        """
        gauss = np.exp(
            -((lat2d - 25.0) / 12.0) ** 2 - ((lon2d - 110.0) / 18.0) ** 2
        )
        background = 70.0 * (
            0.5 * np.sin(np.deg2rad(lat2d * 6)) * np.cos(np.deg2rad(lon2d * 5))
            + 0.5
        )
        return np.clip(background + 2200.0 * gauss, 0.0, 2500.0)

    @staticmethod
    def _cin(lat2d: np.ndarray, lon2d: np.ndarray) -> np.ndarray:
        """
        Convective inhibition (J/kg, magnitude).

        CIN suppresses convection where it is large, so we place it as
        a complementary pattern to CAPE: small (<20 J/kg) over the
        active core, larger (50–180 J/kg) on the periphery. This
        exercises the ``cn.cin_wind`` fill levels [0, 10, 20, 30, 40,
        50, 60, 70, 80, 100, 150, 200].
        """
        cap_core = np.exp(
            -((lat2d - 25.0) / 12.0) ** 2 - ((lon2d - 110.0) / 18.0) ** 2
        )
        # High CIN on the periphery of the active region.
        ring = (1.0 - cap_core) * (
            0.6 + 0.4 * np.sin(np.deg2rad(lat2d * 3))
            * np.cos(np.deg2rad(lon2d * 2))
        )
        values = 20.0 + 130.0 * ring - 20.0 * cap_core
        return np.clip(values, 0.0, 200.0)

    @staticmethod
    def _best_lifted_index(
            lat2d: np.ndarray, lon2d: np.ndarray
    ) -> np.ndarray:
        """
        Best lifted index (K).

        Most-negative (most-unstable) values south, tending toward zero
        in the cooler, drier north. Lights up the negative bands of
        ``cn.bli_wind`` (−48..0).
        """
        base = -25.0 + 0.5 * lat2d
        wave = 5.0 * np.cos(np.deg2rad(lat2d * 2)) * np.sin(
            np.deg2rad(lon2d * 1.5)
        )
        return np.clip(base + wave, -48.0, 5.0)

    @staticmethod
    def _moisture_flux_divergence(
            lat2d: np.ndarray, lon2d: np.ndarray
    ) -> np.ndarray:
        """
        Moisture flux divergence (s⁻¹·g/kg).

        Negative (convergence) over the precipitation band, positive
        elsewhere. The ``cn.qv_div`` plot multiplies by 1e7 and fills
        only the negative bands (-50e-7 .. -5e-7).
        """
        band_axis = lat2d - (28.0 + 0.18 * (lon2d - 100.0))
        convergence = -45e-7 * np.exp(-(band_axis ** 2) / (2.0 * 3.5 ** 2))
        background = 8e-7 * np.sin(np.deg2rad(lat2d * 3)) * np.cos(
            np.deg2rad(lon2d * 2)
        )
        return convergence + background

    @staticmethod
    def _pte(
            lat2d: np.ndarray, lon2d: np.ndarray, level
    ) -> np.ndarray:
        """
        Pseudo-equivalent potential temperature (K).

        Designed so that ``PTE(500 hPa) − PTE(850 hPa)`` covers most of
        the ``cn.pte_wind`` plot's fill range of (-40, 5).
        """
        level_value = MockDataSource._level_value(level, default=700.0)
        # Linear: 850 hPa -> 0, 500 hPa -> -20.
        level_offset = -20.0 * (850.0 - level_value) / (850.0 - 500.0)
        # Pattern that is the same at every level (cancels in the diff).
        common = (
            15.0 * np.cos(np.deg2rad(lat2d * 2))
            + 5.0 * np.sin(np.deg2rad(lon2d * 3))
        )
        # Pattern that differs per level so the difference has structure.
        per_level = 12.0 * np.cos(np.deg2rad(level_value / 2.5)) * (
            np.sin(np.deg2rad(lat2d * 3)) * np.cos(np.deg2rad(lon2d * 2))
        )
        return 340.0 + level_offset + common + per_level

    @staticmethod
    def _vertical_wind_shear(
            lat2d: np.ndarray, lon2d: np.ndarray
    ) -> np.ndarray:
        """
        Vertical wind shear magnitude (m/s).

        Larger in mid-latitudes (where the jet sits) and smaller near
        the equator and at high latitudes.
        """
        midlat_envelope = np.exp(-((lat2d - 38.0) / 12.0) ** 2)
        base = 4.0 + 18.0 * midlat_envelope
        wave = 3.0 * np.sin(np.deg2rad(lat2d * 3)) * np.cos(
            np.deg2rad(lon2d * 2)
        )
        return np.clip(base + wave, 0.0, 30.0)

    @staticmethod
    def _dew_point(
            lat2d: np.ndarray, lon2d: np.ndarray, level
    ) -> np.ndarray:
        """
        Dew point temperature (K) on a pressure surface.

        Constructed so that ``T − Td`` ranges roughly 0..30 K over the
        domain, with the smallest depression (most saturated air) over
        the south-east monsoon region. The level dependence mirrors
        :meth:`_t_pressure` so that the depression is a reasonable
        function of height.
        """
        depression = 14.0 + 14.0 * (
            0.5 * np.sin(np.deg2rad(lat2d * 3))
            + 0.5 * np.cos(np.deg2rad(lon2d * 2))
        )
        # Reduce depression in the moist south-east (more saturated).
        moist_core = np.exp(
            -((lat2d - 25.0) / 18.0) ** 2 - ((lon2d - 115.0) / 25.0) ** 2
        )
        depression = depression - 8.0 * moist_core
        depression = np.clip(depression, 0.5, 32.0)
        t_field = MockDataSource._t_pressure(lat2d, lon2d, level)
        return t_field - depression

    @staticmethod
    def _level_value(level, default: float) -> float:
        """Coerce a possibly-None level to a float, with a fallback."""
        if level is None:
            return default
        try:
            return float(level)
        except (TypeError, ValueError):
            return default


def build_mock_data_loader(resolution: float = 0.25) -> DataLoader:
    """
    Convenience helper that returns a :class:`DataLoader` wrapping a
    :class:`MockDataSource`.

    Parameters
    ----------
    resolution
        Mock grid resolution in degrees.

    Returns
    -------
    DataLoader
        Ready-to-use loader, identical to what production code uses with
        :class:`~cedar_graph.data.LocalDataSource`.
    """
    return DataLoader(data_source=MockDataSource(resolution=resolution))

"""Ground-track map segments stop at the international date line."""

import numpy as np
import pytest

from orbit_wizard_blue.ground_track import ground_track_plot
from orbit_wizard_blue.models import ValidationError


def test_date_line_jump_inserts_nan_break_without_losing_samples():
    coordinates = np.array([[10., 170., 500.], [11., 179., 500.],
                            [12., 181., 500.], [13., -170., 500.]])
    lon, lat = ground_track_plot(coordinates)
    np.testing.assert_allclose(lon, [170., 179., np.nan, -179., -170.], equal_nan=True)
    np.testing.assert_allclose(lat, [10., 11., np.nan, 12., 13.], equal_nan=True)
    np.testing.assert_allclose(coordinates[:, 1], [170., 179., 181., -170.])
    with pytest.raises(ValueError):
        lon[0] = 0


def test_wrapped_longitudes_without_large_jump_stay_connected():
    lon, lat = ground_track_plot([[0., 361., 0.], [1., 362., 0.]])
    np.testing.assert_allclose(lon, [1., 2.])
    np.testing.assert_allclose(lat, [0., 1.])


def test_missing_empty_and_invalid_geodetic_inputs():
    assert ground_track_plot(None) is None
    longitude, latitude = ground_track_plot(np.empty((0, 3)))
    assert len(longitude) == len(latitude) == 0
    with pytest.raises(ValidationError, match="shape"):
        ground_track_plot([[1., 2.]])
    with pytest.raises(ValidationError, match="finite"):
        ground_track_plot([[1., float("nan"), 0.]])
    with pytest.raises(ValidationError, match="latitude"):
        ground_track_plot([[91., 0., 0.]])

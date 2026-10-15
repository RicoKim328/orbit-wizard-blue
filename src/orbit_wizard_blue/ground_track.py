"""Prepare WGS84 geodetic samples for a longitude/latitude line plot."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .models import ValidationError


def ground_track_plot(geodetic_deg_km: ArrayLike | None) -> tuple[NDArray[np.float64], NDArray[np.float64]] | None:
    """Return read-only ``(longitude, latitude)`` arrays with NaN line breaks.

    Input columns are latitude degrees, longitude degrees, ellipsoidal height km.
    ``None`` means unavailable Earth-fixed coordinates and returns ``None``.
    Empty input returns two empty arrays. Invalid shape, non-finite values, or
    latitude outside [-90, 90] raises ``ValidationError``.
    """
    if geodetic_deg_km is None:
        return None
    try:
        coordinates = np.asarray(geodetic_deg_km, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Geodetic coordinates must be numeric") from exc
    if coordinates.ndim != 2 or coordinates.shape[1] != 3:
        raise ValidationError("Geodetic coordinates must have shape (N, 3)")
    if not np.isfinite(coordinates).all():
        raise ValidationError("Geodetic coordinates must contain only finite values")
    lat = coordinates[:, 0]
    if np.any((lat < -90) | (lat > 90)):
        raise ValidationError("Geodetic latitude must be within [-90, 90] degrees")
    lon = (coordinates[:, 1] + 180.0) % 360.0 - 180.0
    if len(lon) == 0:
        return np.empty(0, dtype=np.float64), np.empty(0, dtype=np.float64)
    jumps = np.flatnonzero(np.abs(np.diff(lon)) > 180.0) + 1
    length = len(lon) + len(jumps)
    longitude = np.empty(length, dtype=np.float64)
    latitude = np.empty(length, dtype=np.float64)
    indices = np.arange(len(lon)) + np.searchsorted(jumps, np.arange(len(lon)), side="right")
    longitude[:] = np.nan
    latitude[:] = np.nan
    longitude[indices] = lon
    latitude[indices] = lat
    longitude.setflags(write=False)
    latitude.setflags(write=False)
    return longitude, latitude

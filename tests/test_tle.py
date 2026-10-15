"""Strict source preservation and propagation equivalence for local TLEs."""

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest
from astropy.time import Time
from sgp4.api import Satrec
from sgp4.io import fix_checksum

from orbit_wizard_blue.models import DataSnapshot, OrbitRequest, ValidationError
from orbit_wizard_blue.orbit import compute_ephemeris
from orbit_wizard_blue.tle import parse_tle


# Vallado et al., AIAA 2006-6753 Rev 1, Appendix D/E; also sgp4's test set.
LINE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
LINE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"
REFERENCE_POSITION = [7022.46529266, -1400.08296755, 0.03995155]
REFERENCE_VELOCITY = [1.893841015, 6.405893759, 4.534807250]


def test_named_and_multiple_tle_records_preserve_source_order_and_lines():
    first = "0 VANGUARD 1\n" + LINE1 + "\n" + LINE2
    records = parse_tle(first + "\n\n" + LINE1 + "\n" + LINE2 + "\n")
    assert len(records) == 2
    assert records[0].payload["OBJECT_NAME"] == "VANGUARD 1"
    assert records[0].metadata["raw_tle"] == first
    assert records[0].metadata["catalog_id"] == 5
    assert records[1].payload["OBJECT_NAME"] == "NORAD 5"
    assert records[1].metadata["raw_tle"] == LINE1 + "\n" + LINE2


@pytest.mark.parametrize("text, message", [
    ("", "empty"),
    (LINE1, "no following"),
    (LINE2, "Unexpected"),
    ("name\nother\n" + LINE1 + "\n" + LINE2, "Multiple"),
    (LINE1[:-1] + "0\n" + LINE2, "checksum"),
    (LINE1 + "\n" + LINE2[:-1], "69 characters"),
    (LINE1 + "\n" + fix_checksum(LINE2[:2] + "00006" + LINE2[7:]), "catalog numbers differ"),
])
def test_rejects_malformed_tle_before_propagation(text, message):
    with pytest.raises(ValidationError, match=message):
        parse_tle(text)


def test_omm_roundtrip_matches_original_tle_and_published_vallado_vector():
    record = parse_tle(LINE1 + "\n" + LINE2)[0]
    original = Satrec.twoline2rv(LINE1, LINE2)
    epoch = datetime.fromisoformat(record.payload["EPOCH"]).replace(tzinfo=timezone.utc)
    request = OrbitRequest(epoch, epoch + timedelta(minutes=360), 21600)
    source = DataSnapshot(record.payload, "local://vanguard", "2000-06-27T00:00:00Z",
                          "2000-06-27T00:00:00Z", "hash", source_kind="local",
                          source_format="tle", source_metadata=record.metadata)
    result = compute_ephemeris(source, request, None)
    times = Time([epoch, epoch + timedelta(minutes=360)], scale="utc")
    errors, positions, velocities = original.sgp4_array(np.asarray(times.jd1), np.asarray(times.jd2))
    assert not np.any(errors)
    np.testing.assert_allclose(result.teme_position_km, positions, atol=0.001)
    np.testing.assert_allclose(result.teme_velocity_km_s, velocities, atol=1e-6)
    np.testing.assert_allclose(result.teme_position_km[0], REFERENCE_POSITION, atol=0.03)
    np.testing.assert_allclose(result.teme_velocity_km_s[0], REFERENCE_VELOCITY, atol=3e-5)


def test_blank_international_designator_remains_blank():
    line1 = fix_checksum(LINE1[:9] + "        " + LINE1[17:])
    parsed = parse_tle(line1 + "\n" + LINE2)[0]
    assert parsed.payload["OBJECT_ID"] == ""
    assert parsed.metadata["line1"] == line1


def test_second_record_error_reports_record_number():
    source = LINE1 + "\n" + LINE2 + "\n" + LINE1 + "\n" + LINE2[:-1] + "0"
    with pytest.raises(ValidationError, match=r"record #2:.*checksum"):
        parse_tle(source)


@pytest.mark.parametrize("line1, line2", [
    (fix_checksum(LINE1[:23] + "X" + LINE1[24:]), LINE2),
    (LINE1, fix_checksum(LINE2[:17] + "ABCDEFGH" + LINE2[25:])),
])
def test_rejects_bad_fixed_columns_even_with_recomputed_checksum(line1, line2):
    with pytest.raises(ValidationError, match="Invalid TLE orbital elements"):
        parse_tle(line1 + "\n" + line2)


def test_rejects_nonfinite_numeric_field_with_valid_checksum():
    line2 = fix_checksum(LINE2[:52] + "        nan" + LINE2[63:])
    with pytest.raises(ValidationError, match="MEAN_MOTION must be finite"):
        parse_tle(LINE1 + "\n" + line2)


def test_alpha_five_catalog_number_is_preserved():
    line1 = fix_checksum(LINE1[:2] + "A0001" + LINE1[7:])
    line2 = fix_checksum(LINE2[:2] + "A0001" + LINE2[7:])
    record = parse_tle(line1 + "\n" + line2)[0]
    assert record.metadata["catalog_id"] == 100001
    assert record.payload["NORAD_CAT_ID"] == 100001

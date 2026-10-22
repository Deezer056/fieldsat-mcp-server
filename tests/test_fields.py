"""Field registry tests."""

from dataclasses import replace

import pytest

from fieldsat.domain.fields import (
    REGISTERED_FIELDS,
    find_registered_field,
    normalize_field_id,
    validate_field_registry,
)
from fieldsat.domain.geometry import PolygonGeometry, centroid, polygon


def test_production_registry_contains_the_demo_field_and_four_agricultural_zones() -> None:
    assert [(field.id, field.crop) for field in REGISTERED_FIELDS] == [
        ("SL-PADDY-MINNERIYA", "paddy"),
        ("SL-PADDY-SAMMANTHURAI", "paddy"),
        ("SL-PADDY-KALA-WEWA", "paddy"),
        ("SL-TEA-PEDRO", "tea"),
    ]


def test_field_lookup_normalizes_without_changing_record() -> None:
    assert normalize_field_id(" sl-paddy-minneriya ") == "SL-PADDY-MINNERIYA"
    assert (
        find_registered_field(" sl-paddy-minneriya ").id  # type: ignore[union-attr]
        == "SL-PADDY-MINNERIYA"
    )
    assert find_registered_field("SL-PADDY-UNKNOWN") is None


def test_every_geometry_has_a_closed_polygon_ring() -> None:
    for field in REGISTERED_FIELDS:
        ring = field.geometry.coordinates[0]
        assert len(ring) >= 4
        assert ring[0] == ring[-1]


def test_registered_geometries_have_expected_centroids() -> None:
    expected_centroids = {
        "SL-PADDY-MINNERIYA": (80.930, 8.035),
        "SL-PADDY-SAMMANTHURAI": (81.810, 7.370),
        "SL-PADDY-KALA-WEWA": (80.475, 8.015),
        "SL-TEA-PEDRO": (80.7975, 6.965),
    }
    for field in REGISTERED_FIELDS:
        assert centroid(field.geometry) == pytest.approx(expected_centroids[field.id])
    validate_field_registry(REGISTERED_FIELDS)


@pytest.mark.parametrize(
    ("geometry", "message"),
    [
        (polygon((80.0, 7.0), (81.0, 7.0), (81.0, 8.0), (80.0, 8.0)), "closed"),
        (
            polygon((181.0, 7.0), (182.0, 7.0), (182.0, 8.0), (181.0, 7.0)),
            "WGS84",
        ),
        (
            polygon((80.0, 7.0), (81.0, 8.0), (80.0, 8.0), (81.0, 7.0), (80.0, 7.0)),
            "non-zero area",
        ),
        (
            PolygonGeometry(
                type="Polygon",
                coordinates=(
                    (
                        (80.0, 7.0),
                        (82.0, 7.0),
                        (81.0, 8.0),
                        (82.0, 9.0),
                        (80.0, 9.0),
                        (81.0, 8.0),
                        (80.0, 7.0),
                    ),
                ),
            ),
            "self-intersect",
        ),
    ],
)
def test_rejects_invalid_live_geometry(geometry: PolygonGeometry, message: str) -> None:
    field = replace(REGISTERED_FIELDS[0], geometry=geometry)
    with pytest.raises(ValueError, match=message):
        validate_field_registry((field,))


def test_rejects_duplicate_or_non_normalized_field_ids() -> None:
    field = REGISTERED_FIELDS[0]
    with pytest.raises(ValueError, match="normalized"):
        validate_field_registry((replace(field, id="sl-paddy-04"),))
    with pytest.raises(ValueError, match="Duplicate"):
        validate_field_registry((field, replace(field)))

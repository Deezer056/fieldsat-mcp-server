"""The field registry: which agricultural zones the server knows about."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from fieldsat.domain.geometry import (
    PolygonGeometry,
    centroid,
    point_in_ring,
    polygon,
    validate_ring,
)

type Crop = Literal["paddy", "tea"]


@dataclass(frozen=True, slots=True)
class RegisteredField:
    id: str
    name: str
    crop: Crop
    time_zone: Literal["Asia/Colombo"]
    geometry: PolygonGeometry


type FieldLookup = Callable[[str], RegisteredField | None]


def validate_field_registry(fields: tuple[RegisteredField, ...]) -> None:
    seen_ids: set[str] = set()
    for field in fields:
        if not field.id or field.id != normalize_field_id(field.id):
            raise ValueError("Registered field IDs must be non-empty and normalized.")
        if field.id in seen_ids:
            raise ValueError(f'Duplicate registered field ID "{field.id}".')
        seen_ids.add(field.id)
        if not field.name.strip():
            raise ValueError("Registered field names must be non-empty.")
        if field.crop not in ("paddy", "tea") or field.time_zone != "Asia/Colombo":
            raise ValueError(
                "Registered fields must use a supported crop and remain in Asia/Colombo."
            )
        if field.geometry.type != "Polygon" or not field.geometry.coordinates:
            raise ValueError("Registered field geometry must be a Polygon.")
        for ring in field.geometry.coordinates:
            validate_ring(ring)
        if not point_in_ring(centroid(field.geometry), field.geometry.coordinates[0]):
            raise ValueError("The field centroid must fall inside the exterior polygon ring.")


REGISTERED_FIELDS: tuple[RegisteredField, ...] = (
    RegisteredField(
        id="SL-PADDY-MINNERIYA",
        name="Minneriya Paddy Fields",
        crop="paddy",
        time_zone="Asia/Colombo",
        geometry=polygon(
            (80.910, 8.050),
            (80.950, 8.050),
            (80.950, 8.020),
            (80.910, 8.020),
            (80.910, 8.050),
        ),
    ),
    RegisteredField(
        id="SL-PADDY-SAMMANTHURAI",
        name="Sammanthurai Plains / Gal Oya Scheme",
        crop="paddy",
        time_zone="Asia/Colombo",
        geometry=polygon(
            (81.780, 7.400),
            (81.840, 7.400),
            (81.840, 7.340),
            (81.780, 7.340),
            (81.780, 7.400),
        ),
    ),
    RegisteredField(
        id="SL-PADDY-KALA-WEWA",
        name="Mahaweli System H / Kala Wewa Basin",
        crop="paddy",
        time_zone="Asia/Colombo",
        geometry=polygon(
            (80.450, 8.040),
            (80.500, 8.040),
            (80.500, 7.990),
            (80.450, 7.990),
            (80.450, 8.040),
        ),
    ),
    RegisteredField(
        id="SL-TEA-PEDRO",
        name="Pedro Tea Estate",
        crop="tea",
        time_zone="Asia/Colombo",
        geometry=polygon(
            (80.785, 6.975),
            (80.810, 6.975),
            (80.810, 6.955),
            (80.785, 6.955),
            (80.785, 6.975),
        ),
    ),
)


def normalize_field_id(field_id: str) -> str:
    return field_id.strip().upper()


def find_registered_field(field_id: str) -> RegisteredField | None:
    normalized = normalize_field_id(field_id)
    return next((field for field in REGISTERED_FIELDS if field.id == normalized), None)


validate_field_registry(REGISTERED_FIELDS)

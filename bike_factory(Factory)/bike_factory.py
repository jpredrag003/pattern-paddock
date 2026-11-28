from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
import json
import math
from types import MappingProxyType
from typing import TypedDict

__all__ = [
    "BikeSpec",
    "BikeSpecDict",
    "Manufacturer",
    "Motorcycle",
    "MotorcycleDict",
    "MotorcycleFactory",
    "Rider",
    "RiderDict",
    "UnknownManufacturerError",
]


class UnknownManufacturerError(KeyError):
    """Raised when a manufacturer is unknown or absent from the catalog."""


class BikeSpecDict(TypedDict):
    """Serialized dictionary shape for a motorcycle performance specification."""

    model: str
    max_speed: int
    acceleration: float


class MotorcycleDict(TypedDict):
    """Serialized dictionary shape for a motorcycle."""

    manufacturer: str
    model: str
    max_speed: int
    acceleration: float


class RiderDict(TypedDict):
    """Serialized dictionary shape for a rider."""

    name: str
    country: str
    bike: MotorcycleDict


class Manufacturer(StrEnum):
    """Supported motorcycle manufacturers."""

    DUCATI = "Ducati"
    APRILIA = "Aprilia"
    KTM = "KTM"
    HONDA = "Honda"
    YAMAHA = "Yamaha"

    @classmethod
    def from_input(cls, value: object) -> Manufacturer:
        """Parse a string (case-insensitively, ignoring surrounding whitespace) into a Manufacturer."""
        if not isinstance(value, str):
            raise TypeError(
                f"Manufacturer must be a str, got {type(value).__name__}."
            )
        normalized = value.strip().casefold()
        for member in cls:
            if member.value.casefold() == normalized:
                return member
        raise UnknownManufacturerError(f"Unknown motorcycle manufacturer: {value!r}")

    @classmethod
    def coerce(cls, value: Manufacturer | str) -> Manufacturer:
        """Return an existing Manufacturer instance or parse a string via from_input."""
        return value if isinstance(value, cls) else cls.from_input(value)


def _validate_non_empty_str(value: object, field_label: str) -> str:
    """Validate that value is a non-empty string and return its stripped form."""
    if not isinstance(value, str):
        raise TypeError(f"{field_label} must be a str, got {type(value).__name__}.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_label} must not be empty.")
    return cleaned


def _validate_strict_int(
    value: object,
    field_label: str,
    *,
    min_exclusive: int | None = None,
) -> int:
    """Validate that value is an int (excluding bool) and optionally strictly greater than min_exclusive."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_label} must be an int, got {type(value).__name__}.")
    if min_exclusive is not None and value <= min_exclusive:
        raise ValueError(f"{field_label} must be greater than {min_exclusive}.")
    return value


def _validate_positive_finite_float(value: object, field_label: str) -> float:
    """Validate that value is a finite positive number (excluding bool) and return it as float."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(
            f"{field_label} must be a number (int or float), got {type(value).__name__}."
        )
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{field_label} must be a finite number greater than 0.")
    return number


def _validate_mapping_arg(data: object, label: str) -> Mapping[str, object]:
    """Validate that data implements Mapping."""
    if not isinstance(data, Mapping):
        raise TypeError(f"{label} must be a Mapping, got {type(data).__name__}.")
    return data


def _require_key(mapping: Mapping[str, object], key: str, label: str) -> object:
    """Ensure a required key exists in mapping and return its value."""
    if key not in mapping:
        raise KeyError(f"Missing required field {key!r} for {label}.")
    return mapping[key]


@dataclass(frozen=True, slots=True)
class BikeSpec:
    """Immutable performance specification for a motorcycle model.

    Attributes:
        model: Model name.
        max_speed: Top speed in km/h (strictly positive integer).
        acceleration: 0-100 km/h acceleration time in seconds (strictly positive finite float).
    """

    model: str
    max_speed: int
    acceleration: float

    def __post_init__(self) -> None:
        cleaned_model = _validate_non_empty_str(self.model, "Model")
        valid_speed = _validate_strict_int(self.max_speed, "Max speed", min_exclusive=0)
        valid_acceleration = _validate_positive_finite_float(
            self.acceleration, "Acceleration"
        )

        object.__setattr__(self, "model", cleaned_model)
        object.__setattr__(self, "max_speed", valid_speed)
        object.__setattr__(self, "acceleration", valid_acceleration)

    def with_overrides(
        self,
        *,
        model: str | None = None,
        max_speed: int | None = None,
        acceleration: float | None = None,
    ) -> BikeSpec:
        """Return a new BikeSpec with validated overrides, or self if no overrides are given."""
        if model is None and max_speed is None and acceleration is None:
            return self
        return BikeSpec(
            model=model if model is not None else self.model,
            max_speed=max_speed if max_speed is not None else self.max_speed,
            acceleration=acceleration if acceleration is not None else self.acceleration,
        )

    def to_dict(self) -> BikeSpecDict:
        """Serialize the specification to a dictionary."""
        return {
            "model": self.model,
            "max_speed": self.max_speed,
            "acceleration": self.acceleration,
        }

    @classmethod
    def from_dict(cls, data: object) -> BikeSpec:
        """Construct a BikeSpec from a mapping, delegating field validation to __post_init__."""
        mapping = _validate_mapping_arg(data, "specification data")
        return cls(
            model=_require_key(mapping, "model", "specification"),  # type: ignore[arg-type]
            max_speed=_require_key(mapping, "max_speed", "specification"),  # type: ignore[arg-type]
            acceleration=_require_key(mapping, "acceleration", "specification"),  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class Motorcycle:
    """Immutable motorcycle combining a Manufacturer and a BikeSpec."""

    manufacturer: Manufacturer
    spec: BikeSpec

    def __post_init__(self) -> None:
        if not isinstance(self.manufacturer, Manufacturer):
            raise TypeError(
                f"manufacturer must be a Manufacturer, got {type(self.manufacturer).__name__}."
            )
        if not isinstance(self.spec, BikeSpec):
            raise TypeError(
                f"spec must be a BikeSpec, got {type(self.spec).__name__}."
            )

    @classmethod
    def from_fields(
        cls,
        manufacturer: Manufacturer | str,
        model: str,
        max_speed: int,
        acceleration: float,
    ) -> Motorcycle:
        """Construct a Motorcycle from primitive fields."""
        return cls(
            manufacturer=Manufacturer.coerce(manufacturer),
            spec=BikeSpec(
                model=model,
                max_speed=max_speed,
                acceleration=acceleration,
            ),
        )

    @property
    def model(self) -> str:
        """Motorcycle model name."""
        return self.spec.model

    @property
    def max_speed(self) -> int:
        """Top speed in km/h."""
        return self.spec.max_speed

    @property
    def acceleration(self) -> float:
        """0-100 km/h acceleration time in seconds."""
        return self.spec.acceleration

    def to_dict(self) -> MotorcycleDict:
        """Serialize the motorcycle to a dictionary."""
        return {
            "manufacturer": self.manufacturer.value,
            "model": self.model,
            "max_speed": self.max_speed,
            "acceleration": self.acceleration,
        }

    @classmethod
    def from_dict(cls, data: object) -> Motorcycle:
        """Construct a Motorcycle from a mapping."""
        mapping = _validate_mapping_arg(data, "motorcycle data")
        raw_manufacturer = _require_key(mapping, "manufacturer", "motorcycle")
        manufacturer = Manufacturer.coerce(raw_manufacturer)  # type: ignore[arg-type]
        spec = BikeSpec.from_dict(mapping)
        return cls(manufacturer=manufacturer, spec=spec)

    def __str__(self) -> str:
        return (
            f"Manufacturer: {self.manufacturer.value}\n"
            f"Model: {self.model}\n"
            f"Max speed: {self.max_speed} km/h, Acceleration: {self.acceleration:g}s"
        )


@dataclass(frozen=True, slots=True)
class Rider:
    """Immutable rider entity paired with a Motorcycle."""

    name: str
    country: str
    bike: Motorcycle

    def __post_init__(self) -> None:
        cleaned_name = _validate_non_empty_str(self.name, "Rider name")
        cleaned_country = _validate_non_empty_str(self.country, "Rider country")
        if not isinstance(self.bike, Motorcycle):
            raise TypeError(
                f"bike must be a Motorcycle, got {type(self.bike).__name__}."
            )
        object.__setattr__(self, "name", cleaned_name)
        object.__setattr__(self, "country", cleaned_country)

    def to_dict(self) -> RiderDict:
        """Serialize the rider and motorcycle to a dictionary."""
        return {
            "name": self.name,
            "country": self.country,
            "bike": self.bike.to_dict(),
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serialize the rider to a JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: object) -> Rider:
        """Construct a Rider from a mapping."""
        mapping = _validate_mapping_arg(data, "rider data")
        return cls(
            name=_require_key(mapping, "name", "rider"),  # type: ignore[arg-type]
            country=_require_key(mapping, "country", "rider"),  # type: ignore[arg-type]
            bike=Motorcycle.from_dict(_require_key(mapping, "bike", "rider")),
        )

    @classmethod
    def from_json(cls, payload: str) -> Rider:
        """Construct a Rider from a JSON string."""
        if not isinstance(payload, str):
            raise TypeError(f"JSON payload must be a str, got {type(payload).__name__}.")
        parsed: object = json.loads(payload)
        return cls.from_dict(parsed)

    def __str__(self) -> str:
        return f"Rider: {self.name} ({self.country})\n{self.bike}"


class MotorcycleFactory:
    """Factory for creating, filtering, and sorting motorcycles from a catalog."""

    DEFAULT_CATALOG: Mapping[Manufacturer, BikeSpec] = MappingProxyType(
        {
            Manufacturer.DUCATI: BikeSpec("Panigale V4", 320, 2.7),
            Manufacturer.APRILIA: BikeSpec("RSV4", 315, 2.8),
            Manufacturer.KTM: BikeSpec("1290 Super Duke R", 290, 2.9),
            Manufacturer.HONDA: BikeSpec("CBR1000RR-R", 305, 2.8),
            Manufacturer.YAMAHA: BikeSpec("YZF-R1", 299, 2.9),
        }
    )

    def __init__(self, catalog: Mapping[Manufacturer, BikeSpec] | None = None) -> None:
        source = catalog if catalog is not None else self.DEFAULT_CATALOG
        mapping = _validate_mapping_arg(source, "catalog")

        validated_catalog: dict[Manufacturer, BikeSpec] = {}
        for key, spec in mapping.items():
            if not isinstance(key, Manufacturer):
                raise TypeError(
                    f"Catalog key must be a Manufacturer, got {type(key).__name__}."
                )
            if not isinstance(spec, BikeSpec):
                raise TypeError(
                    f"Catalog value must be a BikeSpec, got {type(spec).__name__}."
                )
            validated_catalog[key] = spec

        self._catalog: dict[Manufacturer, BikeSpec] = validated_catalog

    @property
    def catalog(self) -> Mapping[Manufacturer, BikeSpec]:
        """Return a read-only view of the catalog."""
        return MappingProxyType(self._catalog)

    def _build_bikes(self, entries: Iterable[tuple[Manufacturer, BikeSpec]]) -> list[Motorcycle]:
        return [
            Motorcycle(manufacturer=manufacturer, spec=spec)
            for manufacturer, spec in entries
        ]

    def get_spec(self, manufacturer: Manufacturer | str) -> BikeSpec:
        """Return the BikeSpec for manufacturer from the catalog."""
        resolved = Manufacturer.coerce(manufacturer)
        spec = self._catalog.get(resolved)
        if spec is None:
            raise UnknownManufacturerError(
                f"Manufacturer is not in catalog: {resolved.value}"
            )
        return spec

    def create_motorcycle(
        self,
        manufacturer: Manufacturer | str,
        *,
        model: str | None = None,
        max_speed: int | None = None,
        acceleration: float | None = None,
    ) -> Motorcycle:
        """Create a Motorcycle from the catalog with optional field overrides."""
        resolved_manufacturer = Manufacturer.coerce(manufacturer)
        base_spec = self.get_spec(resolved_manufacturer)
        resolved_spec = base_spec.with_overrides(
            model=model,
            max_speed=max_speed,
            acceleration=acceleration,
        )
        return Motorcycle(manufacturer=resolved_manufacturer, spec=resolved_spec)

    def create_all_catalog_bikes(self, *, sort_by_speed_desc: bool = False) -> list[Motorcycle]:
        """Create one Motorcycle for each entry in the catalog."""
        bikes = self._build_bikes(self._catalog.items())
        if sort_by_speed_desc:
            bikes.sort(key=lambda bike: bike.max_speed, reverse=True)
        return bikes

    def find_faster_than(self, min_speed: int) -> list[Motorcycle]:
        """Return catalog motorcycles whose top speed is strictly greater than min_speed."""
        valid_min_speed = _validate_strict_int(min_speed, "Minimum speed")
        matching = (
            (manufacturer, spec)
            for manufacturer, spec in self._catalog.items()
            if spec.max_speed > valid_min_speed
        )
        return self._build_bikes(matching)


def main() -> None:
    """Demonstrate model and factory usage."""
    factory = MotorcycleFactory()

    bike1 = factory.create_motorcycle("ducati")
    bike2 = factory.create_motorcycle(
        Manufacturer.APRILIA,
        model="RS 660",
        max_speed=240,
        acceleration=3.6,
    )
    bike3 = Motorcycle.from_fields("yamaha", "MT-09", 225, 3.8)

    print(bike1)
    print("---")
    print(bike2)
    print("---")
    print(bike3)
    print("---")

    rider = Rider(" Marko ", " Srbija ", bike1)
    print(rider)
    print("---")

    json_payload = rider.to_json()
    rebuilt_rider = Rider.from_json(json_payload)
    print("JSON round-trip equal:", rider == rebuilt_rider)
    print("---")
    print("Faster than 305 km/h:", [b.model for b in factory.find_faster_than(305)])
    print(
        "Sorted by speed (desc):",
        [b.model for b in factory.create_all_catalog_bikes(sort_by_speed_desc=True)],
    )


if __name__ == "__main__":
    main()


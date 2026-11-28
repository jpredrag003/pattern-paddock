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
    """Proizvođač nije pronađen u katalogu."""


class BikeSpecDict(TypedDict):
    """Format rečnika za performanse motocikla."""

    model: str
    max_speed: int
    acceleration: float


class MotorcycleDict(TypedDict):
    """Format rečnika za motocikl."""

    manufacturer: str
    model: str
    max_speed: int
    acceleration: float


class RiderDict(TypedDict):
    """Format rečnika za vozača."""

    name: str
    country: str
    bike: MotorcycleDict


class Manufacturer(StrEnum):
    """Proizvođači motocikala."""

    DUCATI = "Ducati"
    APRILIA = "Aprilia"
    KTM = "KTM"
    HONDA = "Honda"
    YAMAHA = "Yamaha"

    @classmethod
    def from_input(cls, value: object) -> Manufacturer:
        """Pretvara tekst u proizvođača."""
        if not isinstance(value, str):
            raise TypeError(
                f"Manufacturer must be a str, got {type(value).__name__}."
            )
        normalized = value.strip().casefold()
        for member in cls:
            if member.value.casefold() == normalized:
                return member
        raise UnknownManufacturerError(f"Proizvođač nije prepoznat: {value!r}")

    @classmethod
    def coerce(cls, value: Manufacturer | str) -> Manufacturer:
        """Vraća postojećeg proizvođača ili pretvara tekst u njega."""
        return value if isinstance(value, cls) else cls.from_input(value)


def _validate_non_empty_str(value: object, field_label: str) -> str:
    """Validira da vrednost nije prazan tekst i vraća očišćen oblik bez ivica."""
    if not isinstance(value, str):
        raise TypeError(f"{field_label} mora biti tipa str, umesto {type(value).__name__}.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_label} ne sme biti prazno.")
    return cleaned


def _validate_strict_int(
    value: object,
    field_label: str,
    *,
    min_exclusive: int | None = None,
) -> int:
    """Proverava da je vrednost int (bez bool) i po želji strogo veća od min_exclusive."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_label} mora biti tipa int, umesto {type(value).__name__}.")
    if min_exclusive is not None and value <= min_exclusive:
        raise ValueError(f"{field_label} mora biti veće od {min_exclusive}.")
    return value


def _validate_positive_finite_float(value: object, field_label: str) -> float:
    """Proverava da je vrednost konačan pozitivan broj (bez bool) i vraća je kao float."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(
            f"{field_label} mora biti broj (int ili float), umesto {type(value).__name__}."
        )
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{field_label} mora biti konačan broj veći od 0.")
    return number


def _validate_mapping_arg(data: object, label: str) -> Mapping[str, object]:
    """Proverava da li data funkcioniše kao mapa (rečnik)."""
    if not isinstance(data, Mapping):
        raise TypeError(f"{label} mora biti Mapping, umesto {type(data).__name__}.")
    return data


def _require_key(mapping: Mapping[str, object], key: str, label: str) -> object:
    """Proverava da li obavezni ključ postoji u mapi i vraća njegovu vrednost."""
    if key not in mapping:
        raise KeyError(f"Obavezno polje {key!r} nedostaje u {label}.")
    return mapping[key]


@dataclass(frozen=True, slots=True)
class BikeSpec:
    """ 
    Specifikacija performansi modela motora:
        - model – naziv modela motora.
        - max_speed – maksimalna brzina u km/h (ceo broj veći od 0).
        - acceleration – vreme ubrzanja od 0 do 100 km/h u sekundama (pozitivan decimalni broj).
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
        """Vraća novi BikeSpec sa validiranim izmenama, odnosno self ako izmene nisu zadate."""
        if model is None and max_speed is None and acceleration is None:
            return self
        return BikeSpec(
            model=model if model is not None else self.model,
            max_speed=max_speed if max_speed is not None else self.max_speed,
            acceleration=acceleration if acceleration is not None else self.acceleration,
        )

    def to_dict(self) -> BikeSpecDict:
        """Pretvara specifikaciju u rečnik."""
        return {
            "model": self.model,
            "max_speed": self.max_speed,
            "acceleration": self.acceleration,
        }

    @classmethod
    def from_dict(cls, data: object) -> BikeSpec:
        """Kreira BikeSpec iz mape, prepuštajući proveru polja metodi __post_init__."""
        mapping = _validate_mapping_arg(data, "specification data")
        return cls(
            model=_require_key(mapping, "model", "specification"),  # type: ignore[arg-type]
            max_speed=_require_key(mapping, "max_speed", "specification"),  # type: ignore[arg-type]
            acceleration=_require_key(mapping, "acceleration", "specification"),  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class Motorcycle:
    """Nepromenljivi motocikl koji spaja Manufacturer i BikeSpec."""

    manufacturer: Manufacturer
    spec: BikeSpec

    def __post_init__(self) -> None:
        if not isinstance(self.manufacturer, Manufacturer):
            raise TypeError(
                f"manufacturer mora biti Manufacturer, umesto {type(self.manufacturer).__name__}."
            )
        if not isinstance(self.spec, BikeSpec):
            raise TypeError(
                f"spec mora biti BikeSpec, umesto {type(self.spec).__name__}."
            )

    @classmethod
    def from_fields(
        cls,
        manufacturer: Manufacturer | str,
        model: str,
        max_speed: int,
        acceleration: float,
    ) -> Motorcycle:
        """Konstruiše Motorcycle iz primitivnih polja."""
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
        """Naziv modela motocikla."""
        return self.spec.model

    @property
    def max_speed(self) -> int:
        """Najveća brzina u km/h."""
        return self.spec.max_speed

    @property
    def acceleration(self) -> float:
        """Ubrzanje 0–100 km/h u sekundama."""
        return self.spec.acceleration

    def to_dict(self) -> MotorcycleDict:
        """Pretvara motocikl u rečnik."""
        return {
            "manufacturer": self.manufacturer.value,
            "model": self.model,
            "max_speed": self.max_speed,
            "acceleration": self.acceleration,
        }

    @classmethod
    def from_dict(cls, data: object) -> Motorcycle:
        """Kreira Motorcycle iz mape."""
        mapping = _validate_mapping_arg(data, "motorcycle data")
        raw_manufacturer = _require_key(mapping, "manufacturer", "motorcycle")
        manufacturer = Manufacturer.coerce(raw_manufacturer)  # type: ignore[arg-type]
        spec = BikeSpec.from_dict(mapping)
        return cls(manufacturer=manufacturer, spec=spec)

    def __str__(self) -> str:
        return (
            f"Proizvođač: {self.manufacturer.value}\n"
            f"Model: {self.model}\n"
            f"Maksimalna brzina : {self.max_speed} km/h, Acceleration: {self.acceleration:g}s"
        )


@dataclass(frozen=True, slots=True)
class Rider:
    """Nepromenljivi vozač uparen sa objektom Motorcycle."""

    name: str
    country: str
    bike: Motorcycle

    def __post_init__(self) -> None:
        cleaned_name = _validate_non_empty_str(self.name, "Rider name")
        cleaned_country = _validate_non_empty_str(self.country, "Rider country")
        if not isinstance(self.bike, Motorcycle):
            raise TypeError(
                f"bike mora biti Motorcycle, umesto {type(self.bike).__name__}."
            )
        object.__setattr__(self, "name", cleaned_name)
        object.__setattr__(self, "country", cleaned_country)

    def to_dict(self) -> RiderDict:
        """Pretvara vozača i motocikl u rečnik."""
        return {
            "name": self.name,
            "country": self.country,
            "bike": self.bike.to_dict(),
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        """Pretvara vozača u JSON tekst."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: object) -> Rider:
        """Kreira Rider iz mape."""
        mapping = _validate_mapping_arg(data, "rider data")
        return cls(
            name=_require_key(mapping, "name", "rider"),  # type: ignore[arg-type]
            country=_require_key(mapping, "country", "rider"),  # type: ignore[arg-type]
            bike=Motorcycle.from_dict(_require_key(mapping, "bike", "rider")),
        )

    @classmethod
    def from_json(cls, payload: str) -> Rider:
        """Kreira Rider iz JSON teksta."""
        if not isinstance(payload, str):
            raise TypeError(f"JSON podatak mora biti str, umesto {type(payload).__name__}.")
        parsed: object = json.loads(payload)
        return cls.from_dict(parsed)

    def __str__(self) -> str:
        return f"Vozač: {self.name} ({self.country})\n{self.bike}"


class MotorcycleFactory:
    """Fabrika za kreiranje, filtriranje i sortiranje motocikala iz kataloga."""

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
                    f"Ključ kataloga mora biti Manufacturer, umesto {type(key).__name__}."
                )
            if not isinstance(spec, BikeSpec):
                raise TypeError(
                    f"Vrednost kataloga mora biti BikeSpec, umesto {type(spec).__name__}."
                )
            validated_catalog[key] = spec

        self._catalog: dict[Manufacturer, BikeSpec] = validated_catalog

    @property
    def catalog(self) -> Mapping[Manufacturer, BikeSpec]:
        """Vraća read-only prikaz kataloga."""
        return MappingProxyType(self._catalog)

    def _build_bikes(self, entries: Iterable[tuple[Manufacturer, BikeSpec]]) -> list[Motorcycle]:
        return [
            Motorcycle(manufacturer=manufacturer, spec=spec)
            for manufacturer, spec in entries
        ]

    def get_spec(self, manufacturer: Manufacturer | str) -> BikeSpec:
        """Vraća BikeSpec za proizvođača iz kataloga."""
        resolved = Manufacturer.coerce(manufacturer)
        spec = self._catalog.get(resolved)
        if spec is None:
            raise UnknownManufacturerError(
                f"Proizvođač nije u katalogu: {resolved.value}."
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
        """Kreira Motorcycle iz kataloga uz opcionu izmenu polja."""
        resolved_manufacturer = Manufacturer.coerce(manufacturer)
        base_spec = self.get_spec(resolved_manufacturer)
        resolved_spec = base_spec.with_overrides(
            model=model,
            max_speed=max_speed,
            acceleration=acceleration,
        )
        return Motorcycle(manufacturer=resolved_manufacturer, spec=resolved_spec)

    def create_all_catalog_bikes(self, *, sort_by_speed_desc: bool = False) -> list[Motorcycle]:
        """Pravi po jedan Motorcycle za svaki unos u katalogu."""
        bikes = self._build_bikes(self._catalog.items())
        if sort_by_speed_desc:
            bikes.sort(key=lambda bike: bike.max_speed, reverse=True)
        return bikes

    def find_faster_than(self, min_speed: int) -> list[Motorcycle]:
        """Vraća motocikle iz kataloga čija je maksimalna brzina veća od min_speed."""
        valid_min_speed = _validate_strict_int(min_speed, "Minimum speed")
        matching = (
            (manufacturer, spec)
            for manufacturer, spec in self._catalog.items()
            if spec.max_speed > valid_min_speed
        )
        return self._build_bikes(matching)


def main() -> None:
    """Prikazuje korišćenje modela i fabrike."""
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
    print("Preko 305 km/h:", [b.model for b in factory.find_faster_than(305)])
    print(
        "Sortirano po brzini (desc):",
        [b.model for b in factory.create_all_catalog_bikes(sort_by_speed_desc=True)],
    )


if __name__ == "__main__":
    main()


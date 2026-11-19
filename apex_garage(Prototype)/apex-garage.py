from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field, fields, replace
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

# Širi opseg domena
MAX_ENGINE_CAPACITY_CC = 2500
MAX_HORSEPOWER = 600
MAX_FUEL_CAPACITY_L = 50.0


class Configuration(Enum):
    DRY_TRACK_BIKE = "DryTrackBike"
    RAIN_TRACK_BIKE = "RainTrackBike"
    QUALIFYING_BIKE = "QualifyingBike"


class TeamConfigurationError(LookupError):
    """Greška koja se javlja kada tražena konfiguracija prototipa nije registrovana."""


class DuplicateBikeError(ValueError):
    """Javlja se ako unosite ID motocikla koji je već registrovan u sistemu."""


class BikeNotFoundError(LookupError):
    """Greška koja se javlja kada traženi ID motocikla nije dodeljen timu."""


def _validate_bounds(
    value: int | float,
    name: str,
    *,
    min_value: int | float | None = None,
    max_value: int | float | None = None,
    exclusive_min: bool = False,
    exclusive_max: bool = False,
) -> None:
    if min_value is not None:
        if exclusive_min and value <= min_value:
            raise ValueError(f"{name} mora biti veći {min_value}.")
        if not exclusive_min and value < min_value:
            raise ValueError(f"{name} mora biti veći ili jednak {min_value}.")

    if max_value is not None:
        if exclusive_max and value >= max_value:
            raise ValueError(f"{name} mora biti manji {max_value}.")
        if not exclusive_max and value > max_value:
            raise ValueError(f"{name} mora biti manji ili jednak {max_value}.")


def _require_bounded_number(
    value: Any,
    name: str,
    *,
    as_float: bool,
    min_value: int | float | None = None,
    max_value: int | float | None = None,
    exclusive_min: bool = False,
    exclusive_max: bool = False,
) -> int | float:
    if isinstance(value, bool):
        raise TypeError(f"{name} mora biti broj.")

    if as_float:
        if not isinstance(value, (int, float)):
            raise TypeError(f"{name} mora biti realan broj.")
        num: int | float = float(value)
        if not math.isfinite(num):
            raise ValueError(f"{name} mora biti konačan broj.")
    else:
        if not isinstance(value, int):
            raise TypeError(f"{name} mora da bude ceo broj.")
        num = value

    _validate_bounds(
        num,
        name,
        min_value=min_value,
        max_value=max_value,
        exclusive_min=exclusive_min,
        exclusive_max=exclusive_max,
    )
    return num


def _require_bounded_int(
    value: Any,
    name: str,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
    exclusive_min: bool = False,
    exclusive_max: bool = False,
) -> int:
    return int(
        _require_bounded_number(
            value,
            name,
            as_float=False,
            min_value=min_value,
            max_value=max_value,
            exclusive_min=exclusive_min,
            exclusive_max=exclusive_max,
        )
    )


def _require_bounded_float(
    value: Any,
    name: str,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
    exclusive_min: bool = False,
    exclusive_max: bool = False,
) -> float:
    return float(
        _require_bounded_number(
            value,
            name,
            as_float=True,
            min_value=min_value,
            max_value=max_value,
            exclusive_min=exclusive_min,
            exclusive_max=exclusive_max,
        )
    )


def _require_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} mora biti string.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} mora biti popunjen.")
    return cleaned


def _require_configuration(configuration: Any) -> Configuration:
    if not isinstance(configuration, Configuration):
        raise TypeError("Očekuje se vrednost iz enum-a Configuration.")
    return configuration


def _validate_electronics(settings: Any) -> MappingProxyType[str, int]:
    if not isinstance(settings, Mapping):
        raise TypeError("electronics_settings mora biti struktura tipa str -> int.")
    validated: dict[str, int] = {}
    for raw_key, val in settings.items():
        key = _require_non_empty_str(raw_key, "Electronics setting key")
        validated[key] = _require_bounded_int(
            val, f"Podešavanja elektronike '{key}'", min_value=0
        )
    return MappingProxyType(validated)


def _normalize_bike_id(bike_id: str) -> str:
    return _require_non_empty_str(bike_id, "Bike ID").casefold()


@dataclass(frozen=True)
class Motorcycle:
    """Fiksna postavka MotoGP motora koja podržava sigurno kloniranje sa novim vrednostima."""

    model: str
    manufacturer: str
    engine_capacity: int
    horsepower: int
    tire_type: str
    suspension: str
    fuel_capacity: float
    electronics_settings: Mapping[str, int] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        validated_values = {
            "model": _require_non_empty_str(self.model, "Model"),
            "manufacturer": _require_non_empty_str(self.manufacturer, "Manufacturer"),
            "tire_type": _require_non_empty_str(self.tire_type, "Tire type"),
            "suspension": _require_non_empty_str(self.suspension, "Suspension"),
            "engine_capacity": _require_bounded_int(
                self.engine_capacity,
                "Engine capacity",
                min_value=1,
                max_value=MAX_ENGINE_CAPACITY_CC,
            ),
            "horsepower": _require_bounded_int(
                self.horsepower,
                "Horsepower",
                min_value=1,
                max_value=MAX_HORSEPOWER,
            ),
            "fuel_capacity": _require_bounded_float(
                self.fuel_capacity,
                "Fuel capacity",
                min_value=0.0,
                max_value=MAX_FUEL_CAPACITY_L,
                exclusive_min=True,
            ),
            "electronics_settings": _validate_electronics(self.electronics_settings),
        }
        for attr, val in validated_values.items():
            object.__setattr__(self, attr, val)

    @classmethod
    def _field_names(cls) -> set[str]:
        return {f.name for f in fields(cls)}

    def clone(self, **overrides: Any) -> Motorcycle:
        """Vraća ovu istu instancu ako nema izmena, ili njenu proverenu kopiju sa novim vrednostima."""
        if not overrides:
            return self

        unknown_fields = set(overrides) - self._field_names()
        if unknown_fields:
            unknown_list = ", ".join(sorted(unknown_fields))
            raise TypeError(f"Nepoznati atribut(i) u definiciji motocikla: {unknown_list}")

        resolved: dict[str, Any] = {}
        for attr, value in overrides.items():
            if attr == "electronics_settings":
                if not isinstance(value, Mapping):
                    raise TypeError("electronics_settings mora imati strukturu mapiranja teksta u cele brojeve.")
                merged = dict(self.electronics_settings)
                merged.update(value)
                resolved[attr] = merged
            else:
                resolved[attr] = copy.deepcopy(value)

        return replace(self, **resolved)

    def format_summary(self) -> str:
        """Vraća rezime sa inženjerskim jedinicama."""
        electronics_str = (
            ", ".join(
                f"{k}={v}" for k, v in sorted(self.electronics_settings.items())
            )
            or "none"
        )
        return (
            f"{self.manufacturer} {self.model} | {self.engine_capacity}cc, "
            f"{self.horsepower}hp, {self.fuel_capacity}L | Tires: {self.tire_type}, "
            f"Suspension: {self.suspension}, Electronics: {electronics_str}"
        )


@dataclass(frozen=True)
class _BikeRecord:
    bike_id: str
    motorcycle: Motorcycle


class MotoGPTeam:
    """Kontroliše konfiguracije prototipova i raspodelu timskih motocikala."""

    def __init__(self, name: str) -> None:
        self.name = _require_non_empty_str(name, "Team name")
        self._prototypes: dict[Configuration, Motorcycle] = {}
        self._bikes: dict[str, _BikeRecord] = {}

    @property
    def prototypes(self) -> dict[Configuration, Motorcycle]:
        """Vraća plitku kopiju prototipova."""
        return dict(self._prototypes)

    @property
    def bikes(self) -> dict[str, Motorcycle]:
        """Prikazuje dodeljene motocikle grupisane prema izvornom ID-ju."""
        return {
            record.bike_id: record.motorcycle for record in self._bikes.values()
        }

    def register_prototype(self, configuration: Configuration, bike: Motorcycle) -> None:
        """Registruje prototip za datu konfiguraciju staze."""
        valid_config = _require_configuration(configuration)
        if not isinstance(bike, Motorcycle):
            raise TypeError("Očekuje se instanca klase Motorcycle.")
        self._prototypes[valid_config] = bike

    def create_bike(
        self,
        bike_id: str,
        configuration: Configuration,
        *,
        overwrite: bool = False,
        **overrides: Any,
    ) -> Motorcycle:
        """Kreira i registruje timski motocikl kloniranjem već registrovanog prototipa."""
        clean_id = _require_non_empty_str(bike_id, "Bike ID")
        normalized_id = _normalize_bike_id(clean_id)
        valid_config = _require_configuration(configuration)

        prototype = self._prototypes.get(valid_config)
        if prototype is None:
            raise TeamConfigurationError(
                f"Nema registrovanog prototipa za datu konfiguraciju: {valid_config.value}"
            )

        if normalized_id in self._bikes and not overwrite:
            raise DuplicateBikeError(
                f"Motocikl sa ID-jem '{clean_id}' već postoji. Prosledite overwrite=True da biste ga zamenili."
            )

        bike_instance = prototype.clone(**overrides)
        self._bikes[normalized_id] = _BikeRecord(
            bike_id=clean_id, motorcycle=bike_instance
        )
        return bike_instance

    def remove_bike(self, bike_id: str) -> Motorcycle:
        """Uklanja i vraća dodeljeni timski motocikl prema ID-ju."""
        normalized_id = _normalize_bike_id(bike_id)
        record = self._bikes.pop(normalized_id, None)
        if record is None:
            raise BikeNotFoundError(f"Nema dodeljenog motora sa oznakom '{bike_id}'..")
        return record.motorcycle

    @staticmethod
    def _format_entries(entries: list[tuple[str, Motorcycle]]) -> str:
        if not entries:
            return "  (no entries)"
        return "\n".join(f"  {key}: {bike.format_summary()}" for key, bike in entries)

    def format_prototypes(self) -> str:
        """Oblikuje listu registrovanih prototipova u lako čitljiv tekst."""
        items = [(config.value, bike) for config, bike in self._prototypes.items()]
        return self._format_entries(items)

    def format_bikes(self) -> str:
        """Oblikuje dodeljene timske motore u lako čitljiv tekst."""
        items = [(record.bike_id, record.motorcycle) for record in self._bikes.values()]
        return self._format_entries(items)

    def show_prototypes(self) -> None:
        """Prikazuje prototipove"""
        print(self.format_prototypes())

    def show_bikes(self) -> None:
        """Prikazuje dodeljene timske motocikle."""
        print(self.format_bikes())


def run_demo() -> None:
    print("\n--- Prototypes ---")
    demo_team = MotoGPTeam("Ducati Lenovo")
    demo_proto = Motorcycle(
        model="Desmosedici GP26",
        manufacturer="Ducati",
        engine_capacity=1000,
        horsepower=290,
        tire_type="Slick",
        suspension="Ohlins Racing",
        fuel_capacity=22.0,
        electronics_settings={"traction_control": 3, "engine_brake": 2},
    )
    demo_team.register_prototype(Configuration.DRY_TRACK_BIKE, demo_proto)
    demo_team.create_bike(
        "Bike #63",
        Configuration.DRY_TRACK_BIKE,
        electronics_settings={"traction_control": 4},
    )
    demo_team.create_bike(
        "Bike #72",
        Configuration.DRY_TRACK_BIKE,
        fuel_capacity=21.5,
    )
    demo_team.show_prototypes()

    print("\n--- Team Bikes ---")
    demo_team.show_bikes()


if __name__ == "__main__":
    run_demo()

        
        

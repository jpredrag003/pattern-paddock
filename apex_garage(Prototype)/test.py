from __future__ import annotations

import copy
import math
import sys
import unittest
from dataclasses import dataclass, field, fields, replace
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

MAX_ENGINE_CAPACITY_CC = 2500
MAX_HORSEPOWER = 600
MAX_FUEL_CAPACITY_L = 50.0


class Configuration(Enum):
    DRY_TRACK_BIKE = "DryTrackBike"
    RAIN_TRACK_BIKE = "RainTrackBike"
    QUALIFYING_BIKE = "QualifyingBike"


class TeamConfigurationError(LookupError):
    """Raised when a requested prototype configuration has not been registered."""


class DuplicateBikeError(ValueError):
    """Raised when attempting to register a bike ID that already exists."""


class BikeNotFoundError(LookupError):
    """Raised when a requested bike ID is not assigned to the team."""


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
            raise ValueError(f"{name} must be greater than {min_value}.")
        if not exclusive_min and value < min_value:
            raise ValueError(f"{name} must be greater than or equal to {min_value}.")

    if max_value is not None:
        if exclusive_max and value >= max_value:
            raise ValueError(f"{name} must be less than {max_value}.")
        if not exclusive_max and value > max_value:
            raise ValueError(f"{name} must be less than or equal to {max_value}.")


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
        raise TypeError(f"{name} must be a number, not bool.")

    if as_float:
        if not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a real number.")
        num: int | float = float(value)
        if not math.isfinite(num):
            raise ValueError(f"{name} must be a finite number.")
    else:
        if not isinstance(value, int):
            raise TypeError(f"{name} must be an int.")
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
        raise TypeError(f"{field_name} must be a str.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be a non-empty string.")
    return cleaned


def _require_configuration(configuration: Any) -> Configuration:
    if not isinstance(configuration, Configuration):
        raise TypeError("Expected a Configuration enum member.")
    return configuration


def _validate_electronics(settings: Any) -> MappingProxyType[str, int]:
    if not isinstance(settings, Mapping):
        raise TypeError("electronics_settings must be a mapping of str to int.")

    validated: dict[str, int] = {}
    for raw_key, val in settings.items():
        key = _require_non_empty_str(raw_key, "Electronics setting key")
        validated[key] = _require_bounded_int(
            val, f"Electronics setting '{key}'", min_value=0
        )
    return MappingProxyType(validated)


def _normalize_bike_id(bike_id: str) -> str:
    return _require_non_empty_str(bike_id, "Bike ID").casefold()


@dataclass(frozen=True)
class Motorcycle:
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
        if not overrides:
            return self

        unknown_fields = set(overrides) - self._field_names()
        if unknown_fields:
            unknown_list = ", ".join(sorted(unknown_fields))
            raise TypeError(f"Unknown Motorcycle field(s): {unknown_list}")

        resolved: dict[str, Any] = {}
        for attr, value in overrides.items():
            if attr == "electronics_settings":
                if not isinstance(value, Mapping):
                    raise TypeError(
                        "electronics_settings must be a mapping of str to int."
                    )
                merged = dict(self.electronics_settings)
                merged.update(value)
                resolved[attr] = merged
            else:
                resolved[attr] = copy.deepcopy(value)

        return replace(self, **resolved)

    def format_summary(self) -> str:
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
    def __init__(self, name: str) -> None:
        self.name = _require_non_empty_str(name, "Team name")
        self._prototypes: dict[Configuration, Motorcycle] = {}
        self._bikes: dict[str, _BikeRecord] = {}

    @property
    def prototypes(self) -> dict[Configuration, Motorcycle]:
        return dict(self._prototypes)

    @property
    def bikes(self) -> dict[str, Motorcycle]:
        return {
            record.bike_id: record.motorcycle for record in self._bikes.values()
        }

    def register_prototype(self, configuration: Configuration, bike: Motorcycle) -> None:
        valid_config = _require_configuration(configuration)
        if not isinstance(bike, Motorcycle):
            raise TypeError("Expected a Motorcycle instance.")
        self._prototypes[valid_config] = bike

    def create_bike(
        self,
        bike_id: str,
        configuration: Configuration,
        *,
        overwrite: bool = False,
        **overrides: Any,
    ) -> Motorcycle:
        clean_id = _require_non_empty_str(bike_id, "Bike ID")
        normalized_id = _normalize_bike_id(clean_id)
        valid_config = _require_configuration(configuration)

        prototype = self._prototypes.get(valid_config)
        if prototype is None:
            raise TeamConfigurationError(
                f"No registered prototype for configuration: {valid_config.value}"
            )

        if normalized_id in self._bikes and not overwrite:
            raise DuplicateBikeError(
                f"Bike with ID '{clean_id}' already exists. Pass overwrite=True to replace it."
            )

        bike_instance = prototype.clone(**overrides)
        self._bikes[normalized_id] = _BikeRecord(
            bike_id=clean_id, motorcycle=bike_instance
        )
        return bike_instance

    def remove_bike(self, bike_id: str) -> Motorcycle:
        normalized_id = _normalize_bike_id(bike_id)
        record = self._bikes.pop(normalized_id, None)
        if record is None:
            raise BikeNotFoundError(f"No assigned bike found with ID '{bike_id}'.")
        return record.motorcycle

    @staticmethod
    def _format_entries(entries: list[tuple[str, Motorcycle]]) -> str:
        if not entries:
            return "  (no entries)"
        return "\n".join(f"  {key}: {bike.format_summary()}" for key, bike in entries)

    def format_prototypes(self) -> str:
        items = [(config.value, bike) for config, bike in self._prototypes.items()]
        return self._format_entries(items)

    def format_bikes(self) -> str:
        items = [(record.bike_id, record.motorcycle) for record in self._bikes.values()]
        return self._format_entries(items)


class MotorcycleTests(unittest.TestCase):
    @staticmethod
    def _make_bike(**overrides: Any) -> Motorcycle:
        base: dict[str, Any] = {
            "model": "Desmosedici GP26",
            "manufacturer": "Ducati",
            "engine_capacity": 1000,
            "horsepower": 290,
            "tire_type": "Slick",
            "suspension": "Ohlins Racing",
            "fuel_capacity": 22.0,
            "electronics_settings": {"traction_control": 3, "engine_brake": 2},
        }
        base.update(overrides)
        return Motorcycle(**base)

    def setUp(self) -> None:
        self.base_bike = self._make_bike()

    def test_clone_without_overrides_returns_same_immutable_instance(self) -> None:
        self.assertIs(self.base_bike.clone(), self.base_bike)

    def test_clone_merges_electronics_and_allows_zero(self) -> None:
        cloned = self.base_bike.clone(electronics_settings={"traction_control": 0})
        self.assertEqual(
            dict(cloned.electronics_settings),
            {"traction_control": 0, "engine_brake": 2},
        )
        self.assertEqual(self.base_bike.electronics_settings["traction_control"], 3)

    def test_motorcycle_and_electronics_are_immutable(self) -> None:
        with self.assertRaises(AttributeError):
            self.base_bike.horsepower = 310  # type: ignore[misc]
        with self.assertRaises(TypeError):
            self.base_bike.electronics_settings["traction_control"] = 99  # type: ignore[index]

    def test_clone_rejects_unknown_field_and_invalid_override(self) -> None:
        with self.assertRaises(TypeError):
            self.base_bike.clone(unknown_attr=123)
        with self.assertRaises(ValueError):
            self.base_bike.clone(fuel_capacity=-1.0)
        with self.assertRaises(TypeError):
            self.base_bike.clone(electronics_settings=["invalid"])

    def test_boundary_values_and_electronics_validation(self) -> None:
        boundary_bike = self._make_bike(
            engine_capacity=MAX_ENGINE_CAPACITY_CC,
            horsepower=MAX_HORSEPOWER,
            fuel_capacity=MAX_FUEL_CAPACITY_L,
        )
        self.assertEqual(boundary_bike.engine_capacity, MAX_ENGINE_CAPACITY_CC)
        self.assertEqual(boundary_bike.horsepower, MAX_HORSEPOWER)
        self.assertEqual(boundary_bike.fuel_capacity, MAX_FUEL_CAPACITY_L)

        with self.assertRaises(ValueError):
            self._make_bike(horsepower=MAX_HORSEPOWER + 1)
        with self.assertRaises(ValueError):
            self._make_bike(electronics_settings={"abs": -1})

    def test_type_errors_vs_value_errors(self) -> None:
        with self.assertRaises(TypeError):
            self._make_bike(engine_capacity=True)
        with self.assertRaises(TypeError):
            self._make_bike(horsepower="200")
        with self.assertRaises(ValueError):
            self._make_bike(tire_type="   ")
        with self.assertRaises(ValueError):
            self._make_bike(fuel_capacity=math.nan)

    def test_format_summary_with_empty_electronics(self) -> None:
        bike = self._make_bike(electronics_settings={})
        self.assertIn("Electronics: none", bike.format_summary())


class MotoGPTeamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_bike = Motorcycle(
            model="Desmosedici GP26",
            manufacturer="Ducati",
            engine_capacity=1000,
            horsepower=290,
            tire_type="Slick",
            suspension="Ohlins Racing",
            fuel_capacity=22.0,
            electronics_settings={"traction_control": 3, "engine_brake": 2},
        )
        self.team = MotoGPTeam("Ducati Lenovo")
        self.team.register_prototype(Configuration.DRY_TRACK_BIKE, self.base_bike)

    def test_invalid_team_name_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            MotoGPTeam("   ")

    def test_missing_prototype_raises_before_duplicate_check(self) -> None:
        self.team.create_bike("Bike #63", Configuration.DRY_TRACK_BIKE)
        with self.assertRaises(TeamConfigurationError):
            self.team.create_bike("Bike #63", Configuration.RAIN_TRACK_BIKE)

    def test_case_insensitive_duplicate_overwrite_and_remove(self) -> None:
        self.team.create_bike("Bike #63", Configuration.DRY_TRACK_BIKE)
        with self.assertRaises(DuplicateBikeError):
            self.team.create_bike("bike #63", Configuration.DRY_TRACK_BIKE)

        updated = self.team.create_bike(
            "Bike #63",
            Configuration.DRY_TRACK_BIKE,
            overwrite=True,
            fuel_capacity=20.5,
        )
        self.assertEqual(updated.fuel_capacity, 20.5)

        removed = self.team.remove_bike("BIKE #63")
        self.assertEqual(removed.fuel_capacity, 20.5)
        with self.assertRaises(BikeNotFoundError):
            self.team.remove_bike("Bike #63")

    def test_properties_return_isolated_mappings(self) -> None:
        exposed_bikes = self.team.bikes
        self.team.create_bike("Bike #63", Configuration.DRY_TRACK_BIKE)
        self.assertEqual(exposed_bikes, {})

        exposed_protos = self.team.prototypes
        exposed_protos.clear()
        self.assertIn(Configuration.DRY_TRACK_BIKE, self.team.prototypes)

    def test_empty_formatting(self) -> None:
        empty_team = MotoGPTeam("Empty Racing")
        self.assertEqual(empty_team.format_prototypes(), "  (no entries)")
        self.assertEqual(empty_team.format_bikes(), "  (no entries)")


if __name__ == "__main__":
    program = unittest.main(verbosity=2, exit=False)
    sys.exit(0 if program.result.wasSuccessful() else 1)

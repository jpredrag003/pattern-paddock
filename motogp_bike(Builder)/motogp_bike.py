from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum, StrEnum
import math
from typing import Self, TypedDict, Unpack, cast, overload


class Team(Enum):
    """Fabrički MotoGP timovi."""
    DUCATI = "Ducati"
    APRILIA = "Aprilia"
    KTM = "KTM"
    HONDA = "Honda"
    YAMAHA = "Yamaha"


class ComponentSlot(StrEnum):
    """Delovi motocikla."""
    AERODYNAMICS = "aerodynamics"
    TYRES = "tyres"
    ELECTRONICS = "electronics"
    EXHAUST = "exhaust"


class ComponentUpdates(TypedDict, total=False):
    """Šta se sme menjati na motoru."""
    aerodynamics: str
    tyres: str
    electronics: str
    exhaust: str


class BikeUpdates(TypedDict, total=False):
    """Šta se sme menjati pomoću with_updates."""
    team: Team
    engine_capacity: int
    horsepower: int
    weight: float
    components: BikeComponents | ComponentUpdates


def _validate_non_empty_str(value: object, name: str) -> str:
    """Provera i normalizacija teksta."""
    if not isinstance(value, str):
        raise TypeError(f"Polje '{name}' mora biti tekst.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"Polje '{name}' mora sadržati tekst.")
    return cleaned


@overload
def _validate_number(
    value: object,
    name: str,
    *,
    as_int: bool = ...,
    min_exclusive: float | None = ...,
    min_inclusive: float | None = ...,
    max_inclusive: float | None = ...,) -> int | float: ...

def _validate_number(
    value: object,
    name: str,
    *,
    as_int: bool,
    min_exclusive: float | None = None,
    min_inclusive: float | None = None,
    max_inclusive: float | None = None,) -> int | float:
    """Provera broja u zadatim granicama."""
    allowed_types: tuple[type, ...] = (int,) if as_int else (int, float)
    if isinstance(value, bool) or not isinstance(value, allowed_types):
        expected = "ceo broj" if as_int else "realan broj"
        raise TypeError(f"Polje '{name}' mora biti {expected}.")
        
    numeric: int | float = int(value) if as_int else float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"Polje '{name}' mora biti konačan broj.")

    if min_exclusive is not None and numeric <= min_exclusive:
        raise ValueError(f"Polje '{name}' mora biti veće od {min_exclusive}.")
    if min_inclusive is not None and numeric < min_inclusive:
        raise ValueError(f"Polje '{name}' mora biti veće ili jednako {min_inclusive}.")
    if max_inclusive is not None and numeric > max_inclusive:
        raise ValueError(f"Polje '{name}' mora biti manje ili jednako {max_inclusive}.")
    return numeric


def _validate_int(
    value: object,
    name: str,
    *,
    min_exclusive: int | None = None,
    min_inclusive: int | None = None,
    max_inclusive: int | None = None,) -> int:
    """Provera celog broja u opsegu."""
    return int(
        _validate_number(
            value,
            name,
            as_int=True,
            min_exclusive=min_exclusive,
            min_inclusive=min_inclusive,
            max_inclusive=max_inclusive,
        )
    )


def _validate_float(
    value: object,
    name: str,
    *,
    min_exclusive: float | None = None,
    min_inclusive: float | None = None,
    max_inclusive: float | None = None,
) -> float:
    """Provera decimalnog broja u opsegu."""
    return float(
        _validate_number(
            value,
            name,
            as_int=False,
            min_exclusive=min_exclusive,
            min_inclusive=min_inclusive,
            max_inclusive=max_inclusive,
        )
    )


@dataclass(frozen=True)
class BikeLimits:
    """Tehnički limiti MotoGP motocikla."""
    max_engine_capacity_cc: int = 1000
    max_horsepower: int = 350
    min_weight_kg: float = 100.0
    max_weight_kg: float = 250.0

    def __post_init__(self) -> None:
        max_cc = _validate_int(
            self.max_engine_capacity_cc, "max_engine_capacity_cc", min_exclusive=0
        )
        max_hp = _validate_int(self.max_horsepower, "max_horsepower", min_exclusive=0)
        min_w = _validate_float(self.min_weight_kg, "min_weight_kg", min_exclusive=0.0)
        max_w = _validate_float(
            self.max_weight_kg,
            "max_weight_kg",
            min_inclusive=min_w,
        )
        object.__setattr__(self, "max_engine_capacity_cc", max_cc)
        object.__setattr__(self, "max_horsepower", max_hp)
        object.__setattr__(self, "min_weight_kg", min_w)
        object.__setattr__(self, "max_weight_kg", max_w)


DEFAULT_BIKE_LIMITS = BikeLimits()


@dataclass(frozen=True)
class BikeComponents:
    """Fiksni delovi motocikla."""
    aerodynamics: str
    tyres: str
    electronics: str
    exhaust: str

    def __post_init__(self) -> None:
        for slot in ComponentSlot:
            cleaned = _validate_non_empty_str(getattr(self, slot.value), slot.value)
            object.__setattr__(self, slot.value, cleaned)

    @classmethod
    def from_slot_mapping(cls, mapping: Mapping[ComponentSlot | str, str]) -> Self:
        """Kreiranje BikeComponents iz mapiranja."""
        kwargs: dict[str, str] = {}
        for slot in ComponentSlot:
            if slot in mapping:
                kwargs[slot.value] = mapping[slot]
            elif slot.value in mapping:
                kwargs[slot.value] = mapping[slot.value]
        return cls(**cast(ComponentUpdates, kwargs))

    def get(self, slot: ComponentSlot) -> str:
        """Vrednost zadate komponente."""
        if not isinstance(slot, ComponentSlot):
            raise TypeError("slot mora biti iz ComponentSlot.")
        return str(getattr(self, slot.value))

    def with_updates(self, **changes: Unpack[ComponentUpdates]) -> Self:
        """Nova validirana kopija sa izmenama."""
        return replace(self, **changes)


@dataclass(frozen=True, kw_only=True)
class MotoGPBike:
    """Nepromenljiv i validiran model MotoGP motocikla."""
    team: Team
    engine_capacity: int
    horsepower: int
    weight: float
    components: BikeComponents
    limits: BikeLimits = field(default=DEFAULT_BIKE_LIMITS, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.limits, BikeLimits):
            raise TypeError("limits mora biti tipa BikeLimits.")
        if not isinstance(self.team, Team):
            raise TypeError("team mora biti iz Team.")
        if not isinstance(self.components, BikeComponents):
            raise TypeError("components mora biti tipa BikeComponents.")

        validated_engine = _validate_int(
            self.engine_capacity,
            "engine_capacity",
            min_exclusive=0,
            max_inclusive=self.limits.max_engine_capacity_cc,
        )
        validated_hp = _validate_int(
            self.horsepower,
            "horsepower",
            min_exclusive=0,
            max_inclusive=self.limits.max_horsepower,
        )
        validated_weight = _validate_float(
            self.weight,
            "weight",
            min_inclusive=self.limits.min_weight_kg,
            max_inclusive=self.limits.max_weight_kg,)
        
        object.__setattr__(self, "engine_capacity", validated_engine)
        object.__setattr__(self, "horsepower", validated_hp)
        object.__setattr__(self, "weight", validated_weight)

    def with_updates(self, **changes: Unpack[BikeUpdates]) -> Self:
        """Nova validirana kopija motocikla sa izmenama."""
        payload: dict[str, object] = dict(changes)
        if "components" in payload:
            raw_components = payload["components"]
            if isinstance(raw_components, Mapping):
                component_dict = cast(ComponentUpdates, dict(raw_components))
                payload["components"] = self.components.with_updates(**component_dict)
            elif not isinstance(raw_components, BikeComponents):
                raise TypeError("components mora biti BikeComponents ili mapa izmena.")
        return replace(self, **payload)

    def __str__(self) -> str:
        component_lines = [
            f"{slot.name.capitalize()}: {self.components.get(slot)}"
            for slot in ComponentSlot]
        lines = [
            f"Team: {self.team.value}",
            f"Engine capacity: {self.engine_capacity} cc",
            f"Horsepower: {self.horsepower} hp",
            f"Weight: {self.weight} kg",
            *component_lines,]
        return "\n".join(lines)


@dataclass
class _PartialBikeSpecs:
    """Interno stanje nacrta u builderu."""
    team: Team | None = None
    engine_capacity: int | None = None
    horsepower: int | None = None
    weight: float | None = None
    components: dict[ComponentSlot, str] = field(default_factory=dict)

    def missing_fields(self) -> list[str]:
        """Nazivi nepostavljenih obaveznih polja."""
        scalar_fields: dict[str, object] = {
            "team": self.team,
            "engine_capacity": self.engine_capacity,
            "horsepower": self.horsepower,
            "weight": self.weight,
        }
        missing = [name for name, val in scalar_fields.items() if val is None]
        missing.extend(slot.value for slot in ComponentSlot if slot not in self.components)
        return missing

    def clone(self) -> _PartialBikeSpecs:
        """Nezavisna kopija trenutnog nacrta."""
        return _PartialBikeSpecs(
            team=self.team,
            engine_capacity=self.engine_capacity,
            horsepower=self.horsepower,
            weight=self.weight,
            components=dict(self.components),
        )


class MotoGPBikeBuilder:
    """Builder za sklapanje i validaciju MotoGPBike."""

    def __init__(self, limits: BikeLimits = DEFAULT_BIKE_LIMITS) -> None:
        """Inicijalizuje builder sa zadatim ili podrazumevanim limitima."""
        if not isinstance(limits, BikeLimits):
            raise TypeError("limits mora biti tipa BikeLimits.")
        self._limits = limits
        self._specs = _PartialBikeSpecs()

    def clone(self) -> MotoGPBikeBuilder:
        """Nova instanca buildera sa kopijom nacrta i limita."""
        copied = MotoGPBikeBuilder(limits=self._limits)
        copied._specs = self._specs.clone()
        return copied

    def reset(self) -> Self:
        """Resetuje nacrt na prazno stanje."""
        self._specs = _PartialBikeSpecs()
        return self

    def set_team(self, team: Team) -> Self:
        """Postavlja početni nacrt; validacija je u build()."""
        self._specs.team = team
        return self

    def set_engine_capacity(self, engine_capacity: int) -> Self:
        """Beleži zapreminu motora u cc u nacrtu."""
        self._specs.engine_capacity = engine_capacity
        return self

    def set_horsepower(self, horsepower: int) -> Self:
        """Beleži snagu motora u hp u nacrtu."""
        self._specs.horsepower = horsepower
        return self

    def set_weight(self, weight: float) -> Self:
        """Beleži masu motocikla u kg u nacrtu."""
        self._specs.weight = weight
        return self

    def set_component(self, slot: ComponentSlot, value: str) -> Self:
        """Beleži vrednost za izabrani ComponentSlot u nacrtu."""
        if not isinstance(slot, ComponentSlot):
            raise TypeError("Polje 'slot' mora biti iz ComponentSlot enum-a.")
        self._specs.components[slot] = value
        return self

    def set_aerodynamics(self, aerodynamics: str) -> Self:
        """Postavlja aero paket."""
        return self.set_component(ComponentSlot.AERODYNAMICS, aerodynamics)

    def set_tyres(self, tyres: str) -> Self:
        """Postavlja gume."""
        return self.set_component(ComponentSlot.TYRES, tyres)

    def set_electronics(self, electronics: str) -> Self:
        """Postavlja elektroniku."""
        return self.set_component(ComponentSlot.ELECTRONICS, electronics)

    def set_exhaust(self, exhaust: str) -> Self:
        """Postavlja auspuh."""
        return self.set_component(ComponentSlot.EXHAUST, exhaust)

    def build(self, *, reset_after_build: bool = False) -> MotoGPBike:
        """Validira kompletan nacrt i vraća MotoGPBike."""
        missing = self._specs.missing_fields()
        if missing:
            raise ValueError(f"Greška za MotoGPBike: nedostaju {', '.join(missing)}.")
            
        assert self._specs.team is not None
        assert self._specs.engine_capacity is not None
        assert self._specs.horsepower is not None
        assert self._specs.weight is not None

        components = BikeComponents.from_slot_mapping(self._specs.components)

        bike = MotoGPBike(
            team=self._specs.team,
            engine_capacity=self._specs.engine_capacity,
            horsepower=self._specs.horsepower,
            weight=self._specs.weight,
            components=components,
            limits=self._limits,
        )

        if reset_after_build:
            self.reset()

        return bike


if __name__ == "__main__":
    base_builder = (
        MotoGPBikeBuilder()
        .set_team(Team.DUCATI)
        .set_engine_capacity(1000)
        .set_horsepower(300)
        .set_weight(157.5)
        .set_aerodynamics("Advanced Aero")
        .set_tyres("Soft")
        .set_electronics("Advanced ECU")
        .set_exhaust("Titanium")
    )

    bike = base_builder.build()
    print(bike)
    print("---")

    qualifying_bike = bike.with_updates(
        horsepower=310,
        components={"tyres": "Medium"},
    )
    print(qualifying_bike)
    

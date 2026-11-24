import pytest

from motogp_bike import (
    BikeLimits,
    ComponentSlot,
    MotoGPBikeBuilder,
    Team,
)


def _valid_builder(limits: BikeLimits | None = None) -> MotoGPBikeBuilder:
    builder = MotoGPBikeBuilder(limits) if limits is not None else MotoGPBikeBuilder()
    return (
        builder.set_team(Team.DUCATI)
        .set_engine_capacity(1000)
        .set_horsepower(280)
        .set_weight(157)
        .set_aerodynamics("  Factory Aero  ")
        .set_tyres("Medium")
        .set_electronics("Magneti Marelli")
        .set_exhaust("Akrapovic")
    )


def test_successful_build_and_normalization() -> None:
    bike = _valid_builder().build()

    assert bike.team is Team.DUCATI
    assert bike.engine_capacity == 1000
    assert bike.horsepower == 280
    assert bike.weight == 157.0
    assert isinstance(bike.weight, float)
    assert bike.aerodynamics == "Factory Aero"


def test_reset_after_build() -> None:
    builder = _valid_builder()
    bike = builder.build(reset_after_build=True)
    assert bike.team is Team.DUCATI

    with pytest.raises(ValueError) as exc_info:
        builder.build()

    message = str(exc_info.value)
    for field_name in (
        "team",
        "engine_capacity",
        "horsepower",
        "weight",
        ComponentSlot.AERODYNAMICS.value,
        ComponentSlot.TYRES.value,
        ComponentSlot.ELECTRONICS.value,
        ComponentSlot.EXHAUST.value,
    ):
        assert field_name in message


@pytest.mark.parametrize("bad_bool", [True, False])
def test_bool_rejected_as_number(bad_bool: bool) -> None:
    builder = _valid_builder().set_engine_capacity(bad_bool)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        builder.build()


@pytest.mark.parametrize("bad_weight", [float("nan"), float("inf"), float("-inf"), 0, -5.0])
def test_invalid_weight_values(bad_weight: float) -> None:
    builder = _valid_builder().set_weight(bad_weight)
    with pytest.raises(ValueError):
        builder.build()


def test_negative_horsepower_rejected() -> None:
    builder = _valid_builder().set_horsepower(-10)
    with pytest.raises(ValueError):
        builder.build()


def test_blank_string_rejected() -> None:
    builder = _valid_builder().set_exhaust("   ")
    with pytest.raises(ValueError):
        builder.build()


def test_custom_limits_enforced() -> None:
    strict = BikeLimits(max_engine_capacity_cc=1000, max_horsepower=300, max_weight_kg=160.0)
    builder = _valid_builder(strict).set_engine_capacity(1001)
    with pytest.raises(ValueError):
        builder.build()

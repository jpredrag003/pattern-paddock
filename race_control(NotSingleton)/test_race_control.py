import pytest

from main import (
    InvalidInputError,
    InvalidTrackStatusError,
    RaceControl,
    TrackStatus,
)


@pytest.fixture
def race_control() -> RaceControl:
    """Daje novi RaceControl za svaki test."""
    return RaceControl("Monza")


def test_initial_state(race_control: RaceControl):
    assert race_control.circuit_name == "Monza"
    assert race_control.status == TrackStatus.GREEN
    assert race_control.penalties_log == ()


@pytest.mark.parametrize(
    "valid_name",
    ["Monza", "Circuit de Spa-Francorchamps", "Autódromo José Carlos Pace"],
    ids=["monza", "spa", "interlagos_diacritics"],
)
def test_valid_circuit_name(valid_name: str):
    rc = RaceControl(valid_name)
    assert rc.circuit_name == valid_name


def test_circuit_name_strips_surrounding_whitespace():
    rc = RaceControl("  Silverstone  ")
    assert rc.circuit_name == "Silverstone"


@pytest.mark.parametrize(
    "invalid_name",
    ["", "   ", "\t\n", None, 123, True],
    ids=["empty", "spaces", "tabs_newlines", "none", "int", "bool"],
)
def test_invalid_circuit_name(invalid_name):
    with pytest.raises(InvalidInputError):
        RaceControl(invalid_name)  # type: ignore[arg-type]


def test_circuit_name_is_immutable(race_control: RaceControl):
    with pytest.raises((AttributeError, TypeError)):
        race_control.circuit_name = "Imola"  # type: ignore[misc]


def test_status_attribute_is_immutable(race_control: RaceControl):
    with pytest.raises((AttributeError, TypeError)):
        race_control.status = TrackStatus.RED  # type: ignore[misc]


@pytest.mark.parametrize("next_status", list(TrackStatus), ids=lambda s: s.name.lower())
def test_set_track_status_all_statuses(race_control: RaceControl, next_status: TrackStatus):
    race_control.set_track_status(next_status)
    assert race_control.status == next_status


def test_set_track_status_setting_same_status_is_idempotent(race_control: RaceControl):
    race_control.set_track_status(TrackStatus.GREEN)
    assert race_control.status == TrackStatus.GREEN


def test_set_track_status_transition_back_to_green(race_control: RaceControl):
    race_control.set_track_status(TrackStatus.RED)
    assert race_control.status == TrackStatus.RED

    race_control.set_track_status(TrackStatus.GREEN)
    assert race_control.status == TrackStatus.GREEN


@pytest.mark.parametrize(
    "invalid_status",
    ["INVALID", None, 123, True],
    ids=["invalid_str", "none", "int", "bool"],
)
def test_invalid_track_status(race_control: RaceControl, invalid_status):
    with pytest.raises(InvalidTrackStatusError):
        race_control.set_track_status(invalid_status)  # type: ignore[arg-type]


def test_issue_single_penalty(race_control: RaceControl):
    penalty = race_control.issue_penalty("Max Verstappen", "Prebrza vožnja u pit-stopu")

    assert penalty.rider == "Max Verstappen"
    assert penalty.reason == "Prebrza vožnja u pit-stopu"
    assert isinstance(race_control.penalties_log, tuple)
    assert race_control.penalties_log == (penalty,)


def test_issue_penalty_strips_surrounding_whitespace(race_control: RaceControl):
    penalty = race_control.issue_penalty("  Lando Norris  ", "  Prekršaj u boksu  ")

    assert penalty.rider == "Lando Norris"
    assert penalty.reason == "Prekršaj u boksu"


def test_issue_multiple_penalties_preserves_order(race_control: RaceControl):
    p1 = race_control.issue_penalty("Max Verstappen", "Prebrza vožnja u pit-stopu")
    p2 = race_control.issue_penalty("Charles Leclerc", "Nepoštovanje granica staze")

    assert race_control.penalties_log == (p1, p2)


def test_penalties_log_attribute_is_immutable(race_control: RaceControl):
    race_control.issue_penalty("Max Verstappen", "Prebrza vožnja u pit-stopu")

    with pytest.raises((AttributeError, TypeError)):
        race_control.penalties_log = ()  # type: ignore[misc]


def test_penalty_record_is_immutable(race_control: RaceControl):
    penalty = race_control.issue_penalty("Max Verstappen", "Prebrza vožnja u pit-stopu")

    with pytest.raises((AttributeError, TypeError)):
        penalty.rider = "Drugi vozač"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("rider", "reason"),
    [
        ("", "Razlog"),
        ("   ", "Razlog"),
        ("\t\n", "Razlog"),
        (None, "Razlog"),
        (42, "Razlog"),
        (True, "Razlog"),
        ("Vozač", ""),
        ("Vozač", "   "),
        ("Vozač", "\t\n"),
        ("Vozač", None),
        ("Vozač", 42),
        ("Vozač", False),
    ],
    ids=[
        "rider_empty",
        "rider_spaces",
        "rider_whitespace",
        "rider_none",
        "rider_int",
        "rider_bool",
        "reason_empty",
        "reason_spaces",
        "reason_whitespace",
        "reason_none",
        "reason_int",
        "reason_bool",
    ],
)
def test_invalid_penalty_inputs(race_control: RaceControl, rider, reason):
    with pytest.raises(InvalidInputError):
        race_control.issue_penalty(rider, reason) 

import pytest
from race_control import RaceControl, TrackStatus, InvalidInputError, InvalidTrackStatusError


def test_initial_state():
    rc = RaceControl("Monza")
    assert rc.circuit_name == "Monza"
    assert rc.status == TrackStatus.GREEN
    assert len(rc.penalties_log) == 0


def test_invalid_circuit_name():
    with pytest.raises(InvalidInputError):
        RaceControl("")
    with pytest.raises(InvalidInputError):
        RaceControl("   ")


def test_set_track_status():
    rc = RaceControl("Silverstone")
    rc.set_track_status(TrackStatus.RED)
    assert rc.status == TrackStatus.RED

    with pytest.raises(InvalidTrackStatusError):
        rc.set_track_status("INVALID")  # type: ignore


def test_issue_penalty():
    rc = RaceControl("Spa")
    penalty = rc.issue_penalty("Max Verstappen", "Prebrza vožnja u pit-stopu")
    
    assert penalty.rider == "Max Verstappen"
    assert penalty.reason == "Prebrza vožnja u pit-stopu"
    assert len(rc.penalties_log) == 1
    
    # Provera enkapsulacije (tuple ne dozvoljava append spolja)
    log = rc.penalties_log
    assert isinstance(log, tuple)


def test_invalid_penalty_inputs():
    rc = RaceControl("Le Mans")
    with pytest.raises(InvalidInputError):
        rc.issue_penalty("", "Razlog")
    with pytest.raises(InvalidInputError):
        rc.issue_penalty("Vozač", "")

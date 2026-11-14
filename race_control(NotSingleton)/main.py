from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
import threading

logger = logging.getLogger("RaceControl")


class TrackStatus(Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    SAFETY_CAR = "SAFETY CAR"


class RaceControlError(Exception):
    """Opšti izuzetak za sve greške u vezi sa kontrolom trke."""
    pass


class InvalidTrackStatusError(RaceControlError):
    """Baca se ako je status staze nevažeći."""
    pass


class InvalidInputError(RaceControlError):
    """Baca se ako su podaci prazni ili nevažeći."""
    pass


@dataclass(frozen=True, slots=True)
class Penalty:
    """Stalna evidencija kazni i UTC vreme."""
    rider: str
    reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RaceControl:
    """
    Prati status i naziv staze, kao i kazne vozača.
    Izbegava Singleton patern zbog lakšeg testiranja i DI-ja.
    """
    def __init__(self, circuit_name: str) -> None:
        # Thread lock se inicijalizuje na samom startu radi sigurnosti.
        self._lock = threading.RLock()
        self._validate_circuit_name(circuit_name)
        self._circuit_name: str = circuit_name.strip()
        self._status: TrackStatus = TrackStatus.GREEN
        self._penalties_log: list[Penalty] = []

    @staticmethod
    def _validate_circuit_name(name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise InvalidInputError("Naziv staze mora biti unet.")

    @property
    def circuit_name(self) -> str:
        with self._lock:
            return self._circuit_name

    def set_circuit_name(self, name: str) -> None:
        self._validate_circuit_name(name)
        with self._lock:
            self._circuit_name = name.strip()
            logger.info("Naziv staze postavljen na: %s", self._circuit_name)

    @property
    def status(self) -> TrackStatus:
        with self._lock:
            return self._status

    def set_track_status(self, status: TrackStatus | str) -> None:
        # Podrška za Enum i string (za REST/JSON izvore).
        if isinstance(status, str):
            try:
                status = TrackStatus(status.upper().strip())
            except ValueError as e:
                raise InvalidTrackStatusError(f"Nevažeći status staze: '{status}'. Dozvoljeni su: {[s.value for s in TrackStatus]}") from e

        if not isinstance(status, TrackStatus):
            raise InvalidTrackStatusError("Dozvoljeni status je TrackStatus ili važeći string.")

        with self._lock:
            self._status = status
            logger.info("Status staze promenjen u: %s", status.value)

    def issue_penalty(self, rider_name: str, reason: str) -> Penalty:
        if not isinstance(rider_name, str) or not rider_name.strip():
            raise InvalidInputError("Ime vozača mora biti uneto.")
        if not isinstance(reason, str) or not reason.strip():
            raise InvalidInputError("Razlog kazne mora biti unet.")
        
        with self._lock:
            penalty = Penalty(rider=rider_name.strip(), reason=reason.strip())
            self._penalties_log.append(penalty)
            logger.info("Kazna izrečena za vozača %s: %s [Vreme: %s]", penalty.rider, penalty.reason, penalty.timestamp)
            return penalty

    @property
    def penalties_log(self) -> tuple[Penalty, ...]:
        with self._lock:
            return tuple(self._penalties_log)

    def __str__(self) -> str:
        with self._lock:
            return (
                f"RaceControl(circuit='{self._circuit_name}', "
                f"status='{self._status.value}', "
                f"penalties_count={len(self._penalties_log)})"
            )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Primer sa Dependency Injection-om.
    race_control = RaceControl(circuit_name="Mugello")

    print("Početni naziv staze:", race_control.circuit_name)
    
    # Testiranje string-based unosa za status staze.
    race_control.set_track_status("red")
    print("Status staze :", race_control.status.value)
    
    # Testiranje statusa pomoću enuma.
    race_control.set_track_status(TrackStatus.SAFETY_CAR)
    print("Status staze :", race_control.status.value)
    
    issued_penalty = race_control.issue_penalty("Valentino Rossi", "Skraćivanje staze")
    print(race_control)
    print("Evidencija kazni:", race_control.penalties_log)

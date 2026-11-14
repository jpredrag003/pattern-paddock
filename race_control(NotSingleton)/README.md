# 🏎️ Race Control – Sistem za kontrolu trke

<p align="center">
  <b>Python implementacija sistema za upravljanje i praćenje osnovnih informacija o trkačkoj stazi.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/OOP-Object%20Oriented-success.svg" alt="OOP">
  <img src="https://img.shields.io/badge/Thread--Safe-RLock-orange.svg" alt="Thread Safe">
</p>

---

## 📖 Opis projekta

**Race Control** je robusna Python aplikacija namenjena upravljanju i praćenju osnovnih parametara trkačke staze. Sistem omogućava dinamičko upravljanje nazivom staze, praćenje trenutnog statusa, evidentiranje kazni vozača i sveobuhvatno beleženje važnih događaja putem ugrađenog `logging` mehanizma.

Projekat je razvijen primenom naprednih principa **objektno orijentisanog programiranja (OOP)**, uz maksimalno iskorišćenje savremenih mogućnosti jezika Python kao što su enumeracije (`Enum`), dataklase (`dataclass`), prilagođeni izuzeci, svojstva (`property`), stroge tipne anotacije (`Type Hints`) i bezbedna sinhronizacija niti pomoću `threading.RLock`.

Poseban akcenat stavljen je na:
* Rigoroznu validaciju ulaznih podataka.
* Strictnu enkapsulaciju i zaštitu unutrašnjeg stanja objekata.
* Očuvanje integriteta evidencije kazni (nepromenljivost podataka).
* Bezbedan pristup zajedničkim resursima u višedretvenom (`multi-threading`) okruženju.

---

## 🚀 Glavne funkcionalnosti

Sistem pruža sledeće mogućnosti:
* **Upravljanje stazom:** Dinamičko postavljanje i validacija naziva trkačke staze.
* **Praćenje statusa:** Podrška za unos statusa putem `Enum` objekata ili standardnih string vrednosti.
* **Evidentiranje kazni:** Beleženje prekršaja vozača uz automatsko generisanje vremenske oznake u UTC zoni.
* **Immutability (Nepromenljivost):** Zaštita objekata kazni od naknadnih izmena nakon njihovog kreiranja.
* **Napredna validacija:** Provera svih unetih parametara uz specifične prilagođene izuzetke.
* **Thread-Safety:** Bezbedan rad sa deljenim podacima u okruženju sa više niti primenom `threading.RLock`.
* **Arhitektura bez Singleton-a:** Izbegavanje Singleton šablona radi lakšeg testiranja (Unit Testing) i primene *Dependency Injection* pristupa.

---

## 🛠️ Tehnologije i biblioteke

Projekat koristi isključivo **standardne Python biblioteke**, bez potrebe za instaliranjem dodatnih eksternih paketa (`pip`).

| Modul / Tehnologija | Namena |
| :--- | :--- |
| `dataclasses` | Definisanje efikasnih struktura za čuvanje podataka (`Penalty`) |
| `datetime` | Precizno evidentiranje datuma i vremena izricanja kazni (UTC) |
| `enum` | Definisanje striktno dozvoljenih statusa staze |
| `logging` | Standardizovano beleženje događaja, promena i upozorenja |
| `threading` | Sinhronizacija pristupa deljenim podacima (`RLock`) |
| `Type Hints` | Jasnija definisati tipova i bolja statička analiza koda |
| **OOP** | Modularna organizacija sistema kroz klase i jasne odgovornosti |

---

## 📂 Arhitektura i organizacija koda

Implementacija se oslanja na nekoliko ključnih komponenti:

### 1. `TrackStatus` – Enumeracija statusa staze
Definiše dozvoljena stanja staze sprečavajući proizvoljan unos:
* `GREEN` – Normalni uslovi na stazi
* `YELLOW` – Upozorenje i povećan oprez
* `RED` – Prekid ili zaustavljanje trke
* `SAFETY_CAR` – Vožnja iza sigurnosnog vozila

### 2. `RaceControlError` – Hijerarhija izuzetaka
Osnovna klasa za sve greške u sistemu iz koje nasleđuju:
* `InvalidTrackStatusError` – Neispravan ili nepodržan status staze.
* `InvalidInputError` – Prazni ili neispravni ulazni podaci.

### 3. `Penalty` – Model kazne (`dataclass`)
Predstavlja pojedinačnu evidenciju prekršaja:
```python
@dataclass(frozen=True, slots=True)
class Penalty:
    rider: str
    reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

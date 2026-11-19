# Race Control – Sistem za kontrolu trke

## 📖 Opis projekta

**Race Control** je Python implementacija sistema za upravljanje i praćenje osnovnih informacija o trkačkoj stazi. Sistem omogućava upravljanje nazivom staze, praćenje trenutnog statusa, evidentiranje kazni vozača i beleženje važnih događaja putem logging mehanizma.

Projekat je razvijen primenom objektno orijentisanog programiranja (OOP), uz korišćenje naprednijih Python mogućnosti kao što su enumeracije (`Enum`), dataklase (`dataclass`), prilagođeni izuzeci, svojstva (`property`), tipne anotacije i sinhronizacija niti pomoću `threading.RLock`.

Poseban akcenat stavljen je na validaciju ulaznih podataka, enkapsulaciju, očuvanje integriteta evidencije kazni i bezbedan pristup zajedničkim podacima u višedretvenom okruženju.

---

## 🚀 Glavne funkcionalnosti

Sistem pruža sledeće mogućnosti:

* Upravljanje nazivom trkačke staze.
* Praćenje trenutnog statusa staze (podrška za unos statusa putem `Enum` objekata i običnih string vrednosti).
* Evidentiranje kazni vozača uz automatsko beleženje vremena izricanja kazne u UTC vremenskoj zoni.
* Nepromenljivost objekata kazni nakon njihovog kreiranja.
* Validacija svih važnih ulaznih podataka.
* Prilagođeni izuzeci za različite kategorije grešaka.
* Logovanje promena i važnih događaja.
* *Thread-safe* pristup zajedničkim podacima pomoću `RLock`.
* Izbegavanje *Singleton* paterna radi lakšeg testiranja i *Dependency Injection* pristupa.

---

## 🛠️ Tehnologije i biblioteke

Projekat koristi standardne Python biblioteke, bez potrebe za instaliranjem dodatnih eksternih paketa.

| Modul / tehnologija | Namena |
| --- | --- |
| `dataclasses` | Definisanje struktura za čuvanje podataka |
| `datetime` | Evidentiranje datuma i vremena |
| `enum` | Definisanje dozvoljenih statusa staze |
| `logging` | Beleženje događaja i promena |
| `threading` | Sinhronizacija pristupa zajedničkim podacima |
| `Type Hints` | Jasnije definisanje tipova podataka |
| **OOP** | Organizacija sistema kroz klase i objekte |

---

## 📂 Arhitektura i organizacija koda

Implementacija je organizovana kroz nekoliko klasa koje imaju jasno definisane odgovornosti.

### `TrackStatus` – Enumeracija statusa staze

Klasa `TrackStatus` definiše dozvoljena stanja trkačke staze pomoću enumeracije (`Enum`). Podržani statusi su:

* **`GREEN`** – Normalni uslovi na stazi
* **`YELLOW`** – Upozorenje i povećan oprez
* **`RED`** – Prekid ili zaustavljanje trke
* **`SAFETY_CAR`** – Vožnja iza sigurnosnog vozila

Korišćenjem enumeracije sprečava se proizvoljno unošenje statusa i obezbeđuje doslednost podataka kroz ceo sistem.

### `RaceControlError` – Osnovni izuzetak

`RaceControlError` predstavlja osnovnu klasu za sve prilagođene izuzetke u sistemu. Iz nje nasleđuju:

* **`InvalidTrackStatusError`** – koristi se kada se pokuša postavljanje nepostojećeg statusa staze.
* **`InvalidInputError`** – koristi se kada su ulazni podaci prazni ili neispravnog tipa.

Ovakva hijerarhija omogućava preciznije upravljanje greškama i jednostavnije njihovo hvatanje i obradu.

### `Penalty` – Model kazne

Klasa `Penalty` predstavlja pojedinačnu evidenciju izrečene kazne. Definisana je pomoću dekoratora `@dataclass(frozen=True, slots=True)`. Atributi klase su:

* `rider` (`str`) – Ime vozača
* `reason` (`str`) – Razlog izricanja kazne
* `timestamp` (`datetime`) – Vreme izricanja kazne u UTC vremenskoj zoni

Parametar `frozen=True` obezbeđuje nepromenljivost objekta nakon kreiranja, dok `slots=True` ograničava skup atributa objekta i smanjuje memorijsku potrošnju. Vremenska oznaka se automatski generiše korišćenjem `default_factory`.

### `RaceControl` – Centralna klasa sistema

Klasa `RaceControl` predstavlja glavni deo aplikacije i objedinjuje sve funkcionalnosti upravljanja trkom. Njeni osnovni atributi su:

* `_circuit_name` – Naziv trkačke staze
* `_status` – Trenutni status staze
* `_penalties_log` – Interna evidencija izrečenih kazni
* `_lock` – Mehanizam za sinhronizaciju niti

Klasa koristi enkapsulaciju kako bi sprečila direktno menjanje internih podataka. Pristup atributima obavlja se preko kontrolisanih metoda i svojstava.

---

## 🔍 Detaljniji pregled implementacije

* **Inicijalizacija objekta:** Prilikom kreiranja objekta klase `RaceControl`, konstruktor inicijalizuje mehanizam zaključavanja, proverava naziv staze, postavlja početni status na `GREEN` i kreira praznu evidenciju kazni.
* **Validacija podataka:** Metoda `_validate_circuit_name()` proverava da li je naziv staze validan, sprečavajući prihvatanje praznih vrednosti i pogrešnih tipova.
* **Upravljanje statusom staze:** Metoda `set_track_status()` podržava unos preko stringova (uz automatsku normalizaciju velikih slova i razmaka) ili direktno preko `TrackStatus` enumeracije.
* **Evidentiranje kazni:** Metoda `issue_penalty()` validira podatke, kreira nepromenljivi `Penalty` objekat sa UTC vremenskom oznakom i čuva ga u evidenciji.
* **Pristup evidenciji:** Svojstvo `penalties_log` vraća `tuple` umesto interne liste, čime se štiti integritet podataka od spoljnih izmena.
* **Sinhronizacija niti:** Upotreba `threading.RLock` sa `with` blokovima osigurava bezbedan rad u višedretvenom okruženju.
* **Logging sistem:** Koristi se standardni Python `logging` modul za praćenje promena naziva staze, statusa i izricanja kazni.

---

## 💻 Primer korišćenja

Sledeći primer prikazuje osnovni tok rada sistema:

```python
import logging
from race_control import RaceControl, TrackStatus

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

race_control = RaceControl(circuit_name="Mugello")

# Prikaz početnog naziva staze
print("Početni naziv staze:", race_control.circuit_name)

# Promena statusa korišćenjem string vrednosti
race_control.set_track_status("red")
print("Status staze:", race_control.status.value)

# Promena statusa korišćenjem Enum vrednosti
race_control.set_track_status(TrackStatus.SAFETY_CAR)
print("Status staze:", race_control.status.value)

# Izricanje kazne
issued_penalty = race_control.issue_penalty(
    "Valentino Rossi", 
    "Skraćivanje staze"
)

# Prikaz osnovnih informacija o sistemu
print(race_control)

# Prikaz kompletne evidencije kazni
print("Evidencija kazni:", race_control.penalties_log)

```

---

## 🏗️ Primena objektno orijentisanih principa

* **Enkapsulacija:** Ostvarena kroz interne atribute i kontrolisani pristup putem metoda i svojstava.
* **Apstrakcija:** Klasama koje predstavljaju konkretne elemente sistema (status, kazna, kontroler).
* **Nasleđivanje:** Organizacija prilagođenih izuzetaka koji nasleđuju `RaceControlError`.
* **Nepromenljivost (Immutability):** Korišćenje `frozen=True` kod dataklase `Penalty`.
* **Dependency Injection:** Nezavisna instancijacija bez oslanjanja na *Singleton* šablon.

---

## 🔮 Moguća unapređenja

* Integracija SQLite ili PostgreSQL baze podataka radi trajnog skladištenja.
* Kreiranje REST API interfejsa za komunikaciju sa spoljnim sistemima.
* Proširenje evidencije kazni pretragom i filtriranjem.
* Čuvanje logova u fajlovima umesto samo u konzoli.

---

## ⚠️ Ograničenja

Podaci se trenutno čuvaju isključivo u memoriji, tako da se gube nakon završetka programa. Sistem predstavlja osnovni model za upravljanje statusom staze i kaznama, a ne kompletan simulator trkačkih pravila.

---

## 📝 Zaključak

`Race Control` predstavlja primer modularno organizovanog Python sistema koji demonstrira praktičnu primenu OOP principa, validacije, obrade grešaka i bezbednog rada sa nitima. Arhitektura pruža odličnu osnovu za dalju nadogradnju i integraciju u veće projekte.

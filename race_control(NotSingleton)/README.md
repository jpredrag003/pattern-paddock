```markdown
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

Race Control je Python implementacija sistema za upravljanje i praćenje osnovnih informacija o trkačkoj stazi. Sistem omogućava upravljanje nazivom staze, praćenje trenutnog statusa, evidentiranje kazni vozača i beleženje važnih događaja putem logging mehanizma.

Projekat je razvijen primenom objektno orijentisanog programiranja (OOP), uz korišćenje naprednijih Python mogućnosti kao što su enumeracije (Enum), dataklase (dataclass), prilagođeni izuzeci, svojstva (property), tipne anotacije i sinhronizacija niti pomoću threading.RLock.

Poseban akcenat stavljen je na validaciju ulaznih podataka, enkapsulaciju, očuvanje integriteta evidencije kazni i bezbedan pristup zajedničkim podacima u višedretvenom okruženju.

---

## 🚀 Glavne funkcionalnosti

Sistem pruža sledeće mogućnosti:
* Upravljanje nazivom trkačke staze.
* Praćenje trenutnog statusa staze. Podrška za unos statusa putem Enum objekata i običnih string vrednosti.
* Evidentiranje kazni vozača. Automatsko beleženje vremena izricanja kazne u UTC vremenskoj zoni.
* Nepromenljivost objekata kazni nakon njihovog kreiranja.
* Validacija svih važnih ulaznih podataka.
* Prilagođeni izuzeci za različite kategorije grešaka.
* Logovanje promena i važnih događaja.
* Thread-safe pristup zajedničkim podacima pomoću RLock.
* Izbegavanje Singleton paterna radi lakšeg testiranja i Dependency Injection pristupa.

---

## 🛠️ Tehnologije i biblioteke

Projekat koristi standardne Python biblioteke, bez potrebe za instaliranjem dodatnih eksternih paketa.

| Modul / tehnologija | Namena |
| :--- | :--- |
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

### TrackStatus – Enumeracija statusa staze
Klasa TrackStatus definiše dozvoljena stanja trkačke staze pomoću enumeracije (Enum).
Podržani statusi su:
* **GREEN** – Normalni uslovi na stazi
* **YELLOW** – Upozorenje i povećan oprez
* **RED** – Prekid ili zaustavljanje trke
* **SAFETY_CAR** – Vožnja iza sigurnosnog vozila

Korišćenjem enumeracije sprečava se proizvoljno unošenje statusa i obezbeđuje doslednost podataka kroz ceo sistem.

### RaceControlError – Osnovni izuzetak
RaceControlError predstavlja osnovnu klasu za sve prilagođene izuzetke u sistemu.
Iz nje nasleđuju:
* **InvalidTrackStatusError** – koristi se kada se pokuša postavljanje nepostojećeg statusa staze.
* **InvalidInputError** – koristi se kada su ulazni podaci prazni ili neispravnog tipa.

Ovakva hijerarhija omogućava preciznije upravljanje greškama i jednostavnije njihovo hvatanje i obradu.

### Penalty – Model kazne
Klasa Penalty predstavlja pojedinačnu evidenciju izrečene kazne.
Definisana je pomoću dekoratora:
```python
@dataclass(frozen=True, slots=True)

```

Atributi klase su:

* **rider** (`str`) – Ime vozača
* **reason** (`str`) – Razlog izricanja kazne
* **timestamp** (`datetime`) – Vreme izricanja kazne u UTC vremenskoj zoni

Parametar `frozen=True` obezbeđuje nepromenljivost objekta nakon kreiranja, dok `slots=True` ograničava skup atributa objekta i može smanjiti memorijsku potrošnju. Vremenska oznaka se automatski generiše korišćenjem default_factory, tako da svaka nova kazna dobija sopstveno vreme nastanka.

### RaceControl – Centralna klasa sistema

Klasa RaceControl predstavlja glavni deo aplikacije i objedinjuje sve funkcionalnosti upravljanja trkom.
Njeni osnovni atributi su:

* **_circuit_name** – Naziv trkačke staze
* **_status** – Trenutni status staze
* **_penalties_log** – Interna evidencija izrečenih kazni
* **_lock** – Mehanizam za sinhronizaciju niti

Klasa koristi enkapsulaciju kako bi sprečila direktno menjanje internih podataka. Pristup atributima obavlja se preko kontrolisanih metoda i svojstava.

---

## 🔍 Detaljniji pregled implementacije

### Inicijalizacija objekta

Prilikom kreiranja objekta klase RaceControl, konstruktor inicijalizuje mehanizam zaključavanja, proverava naziv staze, postavlja početni status na GREEN i kreira praznu evidenciju kazni.

```python
race_control = RaceControl(circuit_name="Mugello")

```

Naziv staze prolazi kroz validaciju, čime se sprečava kreiranje objekta sa praznim ili neispravnim nazivom.

### Validacija podataka

Metoda `_validate_circuit_name()` proverava da li je naziv staze validan. Ista logika validacije koristi se i prilikom naknadne promene naziva. Slične provere postoje u metodama za promenu statusa i evidentiranje kazni. Na ovaj način se sprečava prihvatanje praznih vrednosti, pogrešnih tipova podataka i nepostojećih statusa.

### Upravljanje statusom staze

Metoda `set_track_status()` omogućava promenu statusa staze.
Podržava dva načina unosa:

```python
race_control.set_track_status("red")

```

ili:

```python
race_control.set_track_status(TrackStatus.SAFETY_CAR)

```

Prilikom tekstualnog unosa vrši se normalizacija pomoću metoda `upper()` i `strip()`, nakon čega se vrednost konvertuje u odgovarajući član enumeracije. Ukoliko status nije validan, podiže se `InvalidTrackStatusError`.

### Evidentiranje kazni

Metoda `issue_penalty()` omogućava kreiranje i čuvanje kazne za određenog vozača.

```python
penalty = race_control.issue_penalty(
    rider_name="Valentino Rossi", 
    reason="Skraćivanje staze"
)

```

Pre kreiranja objekta vrši se validacija imena vozača i razloga kazne. Nakon uspešne validacije kreira se nepromenljivi objekat Penalty, automatski mu se dodeljuje UTC vremenska oznaka i dodaje se u internu evidenciju. Metoda vraća kreirani objekat, što omogućava njegovo dalje korišćenje.

### Pristup evidenciji kazni

Svojstvo `penalties_log` omogućava pregled svih evidentiranih kazni.

```python
penalties = race_control.penalties_log

```

Umesto originalne interne liste, metoda vraća tuple strukturu. Time se sprečava direktno menjanje interne evidencije izvan klase. Kombinacija nepromenljivog tuple objekta i nepromenljivih Penalty objekata pruža dodatnu zaštitu integriteta podataka.

### Sinhronizacija niti

Za zaštitu zajedničkih podataka koristi se:

```python
self._lock = threading.RLock()

```

RLock omogućava kontrolisan pristup zajedničkim atributima kada više niti istovremeno izvršava operacije nad istom instancom klase. Zaključavanje se koristi prilikom čitanja i menjanja naziva staze, statusa i evidencije kazni. Upotreba `with` konstrukcije obezbeđuje automatsko oslobađanje zaključavanja nakon završetka kritične sekcije, uključujući situacije u kojima dođe do izuzetka.

### Logging sistem

Za beleženje događaja koristi se Python logging modul. Sistem evidentira promene naziva staze, promene statusa i izricanje kazni.
Primer konfiguracije:

```python
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

```

Ovakav pristup olakšava praćenje aktivnosti aplikacije, otkrivanje problema i analizu događaja tokom izvršavanja.

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

Primer pokazuje kako se kreira kontrolni sistem, menjaju statusi staze i evidentiraju kazne, uz automatsko beleženje važnih događaja.

---

## 🏗️ Primena objektno orijentisanih principa

Projekat demonstrira primenu nekoliko važnih principa objektno orijentisanog programiranja.

* **Enkapsulacija** je ostvarena korišćenjem internih atributa i kontrolisanog pristupa putem metoda i svojstava. Time se sprečava nekontrolisana promena stanja objekta.
* **Apstrakcija** je ostvarena kroz klase koje predstavljaju konkretne elemente sistema, kao što su status staze, kazna i kontrolni sistem trke.
* **Nasleđivanje** se koristi u organizaciji prilagođenih izuzetaka, gde specijalizovane klase nasleđuju zajedničku osnovnu klasu RaceControlError.
* **Nepromenljivost podataka** ostvarena je korišćenjem `frozen=True` kod dataklase Penalty, čime se sprečava naknadna izmena već kreiranih kazni.
* **Dependency Injection** pristup podržan je time što klasa nije ograničena na Singleton instancu, već se može nezavisno instancirati i prosleđivati drugim delovima aplikacije.

---

## 🔮 Moguća unapređenja

Trenutna implementacija predstavlja osnovu za dalji razvoj kompleksnijeg sistema za upravljanje trkama.
Potencijalna unapređenja uključuju:

* Integraciju SQLite ili PostgreSQL baze podataka radi trajnog čuvanja podataka.
* REST API za komunikaciju sa spoljnim sistemima.
* Proširenje evidencije kazni pretragom i filtriranjem po vozaču i vremenu.
* Uvođenje pravila za dozvoljene prelaze između statusa staze.
* Dodavanje sistema za upravljanje vozačima i njihovim identifikatorima.
* Implementaciju automatskih testova pomoću pytest ili unittest.
* Dodavanje naprednijeg sistema za audit i istoriju promena.
* Proširenje logging sistema radi čuvanja logova u datotekama.

---

## ⚠️ Ograničenja trenutne implementacije

Podaci se trenutno čuvaju isključivo u memoriji, tako da se gube nakon završetka programa. Takođe, sistem ne implementira kompletnu logiku stvarnih trkačkih pravila, već predstavlja osnovni model za upravljanje statusom staze i kaznama. Iako je pristup zajedničkim podacima zaštićen pomoću RLock, to ne predstavlja zamenu za transakcione mehanizme i trajno skladištenje podataka u većim distribuiranim sistemima.

---

## 📝 Zaključak

Race Control predstavlja primer modularno organizovanog Python sistema koji demonstrira praktičnu primenu objektno orijentisanog programiranja i savremenih mogućnosti jezika Python.
Implementacija stavlja naglasak na kontrolu ulaznih podataka, integritet evidencije, jasno definisane odgovornosti klasa, obradu grešaka i bezbedan pristup zajedničkim resursima.
Iako je trenutna verzija namenjena kao osnovni model sistema za kontrolu trke, njena arhitektura pruža dobru osnovu za dalju nadogradnju, integraciju sa bazama podataka, REST servisima i kompleksnijim aplikacijama za upravljanje trkačkim događajima.


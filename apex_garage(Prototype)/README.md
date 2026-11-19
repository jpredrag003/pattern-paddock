# 🏍️ Apex Garage – Sistem za upravljanje MotoGP prototipovima i timskim motociklima

## 📖 Opis projekta
**Apex Garage** je Python implementacija sistema za upravljanje registrovanim prototipovima po konfiguracijama staze i dodeljenim timskim motociklima. Sistem omogućava registraciju prototipova, kloniranje motocikala uz primenu izmena (*overrides*), normalizaciju ID oznaka motocikala, uklanjanje dodeljenih motocikala i pregled formatiranih specifikacija sa mernim jedinicama.

Projekat je razvijen primenom objektno orijentisanog programiranja (OOP), uz korišćenje naprednijih Python mogućnosti kao što su enumeracije (`Enum`), nepromenljive dataklase (`@dataclass(frozen=True)`), `MappingProxyType`, prilagođeni izuzeci, svojstva (`@property`) i tipne anotacije (*type hints*).

Poseban akcenat stavljen je na striktnu validaciju tipova i opsega vrednosti, nepromenljivost objekata motocikala nakon kreiranja, bezbedno kopiranje pri izmenama i zaštitu internih kolekcija od nekontrolisanih spoljašnjih promena.

## 🚀 Glavne funkcionalnosti
Sistem pruža sledeće mogućnosti:
* Upravljanje prototipovima motocikala po konfiguracijama staze.
* Kreiranje timskih motocikala kloniranjem postojećih prototipova uz parcijalne ili potpune izmene parametara (*overrides*).
* Spajanje (*merge*) novih podešavanja elektronike sa postojećim podešavanjima prototipa prilikom kloniranja.
* Nepromenljivost (*immutability*) instanci motocikala nakon kreiranja i vraćanje *read-only* mapiranja za podešavanja elektronike.
* Normalizacija ID-jeva motocikala (*case-insensitive* poređenje uz očuvanje originalne oznake za prikaz).
* Striktnu validaciju tekstualnih polja, celobrojnih i realnih vrednosti, domenskih granica i tipova (uključujući zaštitu od `bool` kao podklase `int` i ne-konačnih `float` vrednosti).
* Prilagođene izuzetke za specifične domenske greške.
* Formatiran ispis rezimea prototipova i dodeljenih motocikala sa mernim jedinicama.

## 🛠️ Tehnologije i biblioteke
Projekat koristi standardne Python biblioteke, bez potrebe za instaliranjem dodatnih eksternih paketa.

| Modul / tehnologija | Namena |
| :--- | :--- |
| `copy` | Duboko kopiranje (`deepcopy`) vrednosti pri kloniranju motocikala |
| `math` | Provera konačnosti realnih brojeva (`math.isfinite`) |
| `dataclasses` | Definisanje nepromenljivih struktura podataka (`dataclass`, `field`, `fields`, `replace`) |
| `enum` | Definisanje dozvoljenih konfiguracija staze (`Enum`) |
| `types` | Kreiranje nepromenljivog pogleda nad podešavanjima elektronike (`MappingProxyType`) |
| `typing` | Jasnije definisanje tipova podataka (`Any`, `Mapping`) |
| `OOP` | Organizacija domenskog modela kroz klase, svojstva i prilagođene izuzetke

## 📂 Arhitektura i organizacija koda
Implementacija je organizovana kroz domenske konstante, enumeraciju, prilagođene izuzetke, pomoćne validatore i klase sa jasno definisanim odgovornostima.

### `Configuration` – Enumeracija konfiguracije staze
Klasa `Configuration` definiše dozvoljene konfiguracije motocikla pomoću enumeracije (`Enum`). Podržane vrednosti su:
* `DRY_TRACK_BIKE` – Konfiguracija za suvu stazu (`"DryTrackBike"`)
* `RAIN_TRACK_BIKE` – Konfiguracija za kišnu stazu (`"RainTrackBike"`)
* `QUALIFYING_BIKE` – Konfiguracija za kvalifikacije (`"QualifyingBike"`)

Korišćenjem enumeracije sprečava se proizvoljno unošenje konfiguracija i obezbeđuje doslednost u celom sistemu.

### Prilagođeni izuzeci
Sistem definiše tri prilagođena izuzetka za različite situacije:
* `TeamConfigurationError` (nasleđuje `LookupError`) – baca se kada za traženu konfiguraciju nije registrovan nijedan prototip.
* `DuplicateBikeError` (nasleđuje `ValueError`) – baca se pri pokušaju kreiranja motocikla sa ID-jem koji već postoji, ako nije prosleđeno `overwrite=True`.
* `BikeNotFoundError` (nasleđuje `LookupError`) – baca se kada se pri uklanjanju prosledi ID motocikla koji nije dodeljen timu.

### `Motorcycle` – Nepromenljivi model motocikla
Klasa `Motorcycle` predstavlja konfiguraciju motocikla koja podržava bezbedno kloniranje sa izmenama. Definisana je pomoću `@dataclass(frozen=True)`. Atributi klase su:
* `model` (`str`) – Naziv modela motocikla
* `manufacturer` (`str`) – Naziv proizvođača
* `engine_capacity` (`int`) – Zapremina motora u `cc` (do `MAX_ENGINE_CAPACITY_CC = 2500`)
* `horsepower` (`int`) – Snaga u `hp` (do `MAX_HORSEPOWER = 600`)
* `tire_type` (`str`) – Tip pneumatika
* `suspension` (`str`) – Sistem ogibljenja
* `fuel_capacity` (`float`) – Kapacitet rezervoara u litrima (`> 0.0` i do `MAX_FUEL_CAPACITY_L = 50.0`)
* `electronics_settings` (`Mapping[str, int]`) – Podešavanja elektronike sačuvana kao `MappingProxyType` (podrazumevano prazno mapiranje)

### `_BikeRecord` i `MotoGPTeam` – Upravljanje prototipovima i timskim motociklima
Interna data klasa `_BikeRecord` povezuje originalni `bike_id` sa instancom `Motorcycle`.

Centralna klasa `MotoGPTeam` upravlja prototipovima i dodeljenim motociklima tima. Njeni osnovni interni atributi su:
* `name` – Validiran naziv tima
* `_prototypes` – Mapiranje `Configuration` na registrovani `Motorcycle` prototip
* `_bikes` – Mapiranje normalizovanog ID-ja motocikla na `_BikeRecord`

## 🔍 Detaljniji pregled implementacije
* **Validacija opsega i tipova:** Pomoćne funkcije (`_validate_bounds`, `_require_bounded_number`, `_require_bounded_int`, `_require_bounded_float`, `_require_non_empty_str`, `_validate_electronics`) proveravaju tipove i granice pre upisa podataka.
* **Validacija pri inicijalizaciji i izmeni:** Metoda `__post_init__` u `Motorcycle` validira sva polja i upisuje normalizovane vrednosti putem `object.__setattr__` jer je klasa `frozen=True`.
* **Kloniranje sa izmenama (`clone`):** Ako nema `overrides`, vraća postojeću instancu; ako postoje izmene, proverava nazive polja, spaja `electronics_settings` sa postojećim vrednostima, radi `deepcopy` ostalih vrednosti i koristi `dataclasses.replace(...)`.
* **Normalizacija ID-ja motocikla:** `_normalize_bike_id()` uklanja suvišne razmake, proverava da string nije prazan i primenjuje `.casefold()` radi jednoobraznog pretraživanja i provere duplikata, dok se originalni naziv čuva u `_BikeRecord`.
* **Zaštita internih kolekcija:** Svojstva `prototypes` i `bikes` vraćaju nove rečnike umesto direktnih referenci na interne strukture.
* **Formatiranje i ispis:** Metode `format_summary()`, `format_prototypes()`, `format_bikes()`, `show_prototypes()` i `show_bikes()` obezbeđuju pregledan tekstualni prikaz specifikacija i stanja tima.

## 💻 Primer korišćenja
Sledeći primer (iz `run_demo()`) prikazuje osnovni tok rada sistema:

```python
from apex_garage import Configuration, MotoGPTeam, Motorcycle

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

# Registracija prototipa za suvu stazu
demo_team.register_prototype(Configuration.DRY_TRACK_BIKE, demo_proto)

# Kreiranje motocikala kloniranjem prototipa uz izmene
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

# Ispis prototipova i dodeljenih motocikala
demo_team.show_prototypes()
demo_team.show_bikes()

```

## 🏗️ Primena objektno orijentisanih principa

* **Enkapsulacija:** Ostvarena kroz interne atribute (`_prototypes`, `_bikes`), `MappingProxyType` za elektroniku i kontrolisani pristup preko metoda i svojstava.
* **Apstrakcija:** Domenski koncepti su izdvojeni u jasne entitete (`Configuration`, `Motorcycle`, `MotoGPTeam`).
* **Nasleđivanje:** Prilagođeni izuzeci nasleđuju ugrađene klase izuzetaka (`LookupError`, `ValueError`) radi jasne semantike grešaka.
* **Nepromenljivost (*Immutability*):** Korišćenje `@dataclass(frozen=True)` za `Motorcycle` i `_BikeRecord` i `MappingProxyType` za `electronics_settings`.
* **Kompozicija i *Prototype* obrazac:** `MotoGPTeam` sadrži prototipove i motocikle, a novi motocikli nastaju kloniranjem registrovanog prototipa.

## 🔮 Moguća unapređenja

* Perzistencija stanja tima i prototipova u bazi podataka ili JSON/YAML fajlovima.
* Dodavanje metoda za ažuriranje ili zamenu postojećeg motocikla bez ponovnog ručnog navođenja svih parametara.
* Uvođenje `logging` mehanizma za praćenje registracije prototipova, kreiranja i uklanjanja motocikala.
* Dodavanje tehničkih pravila specifičnih za pojedine konfiguracije (npr. kišne gume za `RAIN_TRACK_BIKE`).

## ⚠️ Ograničenja

Podaci o prototipovima i motociklima čuvaju se isključivo u memoriji tokom trajanja izvršavanja programa i nisu trajno sačuvani. Gornje granice parametara (`MAX_ENGINE_CAPACITY_CC`, `MAX_HORSEPOWER`, `MAX_FUEL_CAPACITY_L`) predstavljaju šire domenske okvire, a ne potpuni simulator zvaničnih tehničkih pravilnika ili dinamike vožnje.

## 📝 Zaključak

**Apex Garage** pruža čist i čitljiv Python model za upravljanje MotoGP prototipovima i timskim motociklima, sa snažnim naglaskom na validaciju podataka, nepromenljivost modela i bezbedno kloniranje konfiguracija. Može poslužiti kao dobra osnova za dalju nadogradnju u složenije alate za upravljanje trkačkim timom.

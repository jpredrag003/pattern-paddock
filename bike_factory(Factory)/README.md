# Bike Factory - Sistem za modelovanje motocikla

## Opis projekta

Ovaj Python modul implementira domenski sloj za modelovanje motocikala, specifikacija performansi, vozača i kataloga proizvođača. Fokus rešenja je na **nepromenljivim (*immutable*) strukturama podataka**, **strogoj validaciji ulaza** u runtime-u, **statičkoj tipizaciji** (`TypedDict`, `StrEnum`, apstraktne kolekcije) i **serijalizaciji/deserijalizaciji** u rečnike i JSON.


## Glavne funkcionalnosti

* **Normalizacija proizvođača (`Manufacturer`)**: `StrEnum` sa podrškom za parsiranje i normalizaciju unosa bez obzira na velika/mala slova i vodeće/prateće razmake (`from_input`, `coerce`).
* **Strogo validisani modeli podataka**: Nepromenljivi `dataclass(frozen=True, slots=True)` objekti (`BikeSpec`, `Motorcycle`, `Rider`) koji u `__post_init__` proveravaju tipove (uključujući odbacivanje `bool` kao podklase `int`), konačnost brojeva (`math.isfinite`), pozitivne vrednosti i neprazne stringove.
* **Kloniranje sa izmenama**: Metoda `BikeSpec.with_overrides(...)` vraća novu instancu sa izmenjenim poljima ili postojeći objekat ako izmene nisu zadate.
* **Serijalizacija i deserijalizacija**: Konverzija u i iz rečnika (`to_dict`, `from_dict`) i JSON formata (`to_json`, `from_json`) uz očuvanje UTF-8 karaktera (`ensure_ascii=False`).
* **Fabrika i upiti nad katalogom (`MotorcycleFactory`)**: Kreiranje motocikala iz podrazumevanog ili prilagođenog *read-only* kataloga, pretraga po minimalnoj brzini (`find_faster_than`) i sortiranje po brzini (`create_all_catalog_bikes`).


## Tehnologije i biblioteke

| Tehnologija / Modul | Namena u projektu |
| --- | --- |
| **Python 3.11+** | Osnovni jezik; koristi `StrEnum`, odložene anotacije (`from __future__ import annotations`) i moderne tipove. |
| **`dataclasses`** | Generisanje nepromenljivih klasa podataka (`frozen=True, slots=True`) i kuka `__post_init__`. |
| **`enum.StrEnum`** | Definisanje skupa proizvođača motocikala koji se ponašaju i kao stringovi i kao enum članovi. |
| **`typing` (`TypedDict`)** | Statička specifikacija oblika rečnika (`BikeSpecDict`, `MotorcycleDict`, `RiderDict`). |
| **`collections.abc`** | Tipizacija apstraktnih kolekcija (`Iterable`, `Mapping`) radi fleksibilnih ulaza. |
| **`types.MappingProxyType`** | Obezbeđivanje *read-only* pogleda na katalog radi zaštite od spoljašnje mutacije. |
| **`json`** | Serijalizacija objekata u JSON tekst i parsiranje ulaznog JSON-a. |
| **`math`** | Provera konačnosti decimalnih brojeva (`math.isfinite`) pri validaciji ubrzanja. |


## Arhitektura i organizacija koda

Kod je organizovan u jedan samostalan modul sa jasno razdvojenim slojevima:

1. **Javni API (`__all__`) i izuzeci**: Definiše izvezene simbole i prilagođeni izuzetak `UnknownManufacturerError(KeyError)`.
2. **Tipovi rečnika (`TypedDict`)**: `BikeSpecDict`, `MotorcycleDict` i `RiderDict` opisuju strukturu podataka za razmenu i JSON mapiranje.
3. **Domenski enum (`Manufacturer`)**: Predstavlja zatvoreni skup podržanih proizvođača i logiku konverzije iz tekstualnog ulaza.
4. **Interne validacione funkcije (`_validate_*`, `_require_key`)**: Centralizuju provere tipova, praznih stringova, brojevnih granica i obaveznih ključeva u mapama.
5. **Domenski entiteti i vrednosni objekti**:
* `BikeSpec` – specifikacija performansi (`model`, `max_speed`, `acceleration`).
* `Motorcycle` – kompozicija `Manufacturer` i `BikeSpec` sa delegiranim *property* pristupnicima.
* `Rider` – vozač (`name`, `country`) povezan sa `Motorcycle` i JSON metodama.


6. **Fabrika (`MotorcycleFactory`)**: Upravlja katalogom i instanciranjem `Motorcycle` objekata.
7. **Demonstracioni ulaz (`main()`)**: Pokreće primer rada modela, fabrike i JSON *round-trip* provere kada se fajl izvršava direktno.


## Detaljniji pregled implementacije

* **Zaštita od `bool` u numeričkim poljima**: Funkcije `_validate_strict_int` i `_validate_positive_finite_float` eksplicitno proveravaju `isinstance(value, bool)` jer u Pythonu `bool` nasleđuje `int`, čime se sprečava da `True` ili `False` prođu kao brzina ili ubrzanje.
* **Validacija brojeva**: `max_speed` mora biti ceo broj veći od `0` (`min_exclusive=0`), dok `acceleration` mora biti pozitivan `float` za koji važi `math.isfinite(number)` i `number > 0.0`.
* **Upis u *frozen* atribute**: Pošto su `BikeSpec` i `Rider` deklarisani sa `frozen=True`, čišćenje stringova (`.strip()`) i normalizacija numeričkih tipova u `__post_init__` vrše se preko `object.__setattr__(self, ...)`.
* **Enkapsulacija kataloga**: `MotorcycleFactory` čuva internu kopiju u `self._catalog: dict[Manufacturer, BikeSpec]`, a svojstvo `catalog` vraća `MappingProxyType(self._catalog)` kako pozivaoci ne bi mogli direktno da menjaju interni rečnik.


## Primer korišćenja

```python
from modul import Manufacturer, Motorcycle, MotorcycleFactory, Rider

factory = MotorcycleFactory()

# Kreiranje motocikla iz podrazumevanog kataloga
ducati = factory.create_motorcycle("ducati")

# Kreiranje motocikla uz promenu specifikacija
aprilia_rs660 = factory.create_motorcycle(
    Manufacturer.APRILIA,
    model="RS 660",
    max_speed=240,
    acceleration=3.6,
)

# Kreiranje vozača sa automatskim čišćenjem razmaka u imenu i državi
rider = Rider(" Marko ", " Srbija ", ducati)

# Serijalizacija u JSON i ponovno učitavanje
json_data = rider.to_json()
restored_rider = Rider.from_json(json_data)
assert rider == restored_rider

# Upiti nad katalogom
fast_bikes = factory.find_faster_than(305)
sorted_bikes = factory.create_all_catalog_bikes(sort_by_speed_desc=True)

```


## Primena objektno orijentisanih principa

* **Enkapsulacija**: Unutrašnja stanja su zaštićena nepromenljivošću (`frozen=True`), `MappingProxyType` prikazom kataloga i internim pomoćnim funkcijama/metodama (`_validate_*`, `_build_bikes`).
* **Kompozicija nad nasleđivanjem**: `Motorcycle` komponuje `Manufacturer` i `BikeSpec`, a `Rider` komponuje `Motorcycle`, umesto glomazne hijerarhije nasleđivanja.
* **Jedinstvena odgovornost (*Single Responsibility*)**: Validacija je izdvojena u pomoćne funkcije i `__post_init__`, serijalizacija u `to_dict`/`from_dict`/`to_json`/`from_json`, a upravljanje katalogom i kreiranje motocikala u `MotorcycleFactory`.
* **Polimorfizam i apstrakcija tipova**: Korišćenje apstrakcija kao što su `Mapping` i `Iterable` omogućava rad sa različitim kolekcijama i mapama bez vezivanja za jedan konkretan tip.


## Moguća unapređenja

* **Podrška za jedinice mere**: Uvođenje eksplicitnih jedinica ili konverzije (npr. `km/h` i `mph`) za `max_speed`.
* **Dinamičko upravljanje katalogom**: Dodavanje metoda za dodavanje, ažuriranje ili uklanjanje unosa u katalogu bez direktnog menjanja privatnog atributa `_catalog`.
* **Dodatni kriterijumi pretrage i sortiranja**: Filtriranje po ubrzanju (`faster_acceleration_than`), proizvođaču ili višestruki ključevi sortiranja.
* **Automatski testovi**: Pokrivanje validacionih grešaka (`TypeError`, `ValueError`, `KeyError`, `UnknownManufacturerError`) i JSON serijalizacije jedinicom testova (`pytest` / `unittest`).


## Ograničenja

* **Fiksni skup proizvođača**: `Manufacturer` je definisan kao zatvoren `StrEnum` sa pet unapred zadatih proizvođača; dodavanje novog proizvođača zahteva izmenu koda.
* **Podrazumevani katalog je statički**: `DEFAULT_CATALOG` sadrži unapred definisane vrednosti koje služe kao početni primer, a ne kao perzistentna baza podataka.
* **Osnovna JSON šema**: `from_json` očekuje string sa JSON objektom koji prati strukturu `RiderDict`; dublje šeme validacije (npr. JSON Schema) nisu uključene.


## Zaključak

Ovaj modul pruža čist, bezbedan i čitljiv temelj za rad sa domenom motocikala i vozača u Pythonu. Kombinacijom nepromenljivih *dataclass* struktura, stroge *runtime* validacije i *Factory* obrasca smanjuje rizik od neispravnih podataka u aplikaciji i olakšava dalju nadogradnju.

# MotoGP Bike – Sistem za modelovanje i sklapanje MotoGP motocikala

## 📖 Opis projekta

Ovaj projekat implementira domen-model za **MotoGP motocikl** u Pythonu sa fokusom na nepromenljivost podataka, bezbednost tipova i strogu validaciju u vreme izvršavanja. Model omogućava postepeno sklapanje konfiguracije motocikla kroz fluent **Builder** obrazac, kreiranje novih verzija postojećih motocikala bez mutiranja originalnih instanci, kao i kontrolu tehničkih ograničenja (zapremina motora, snaga, masa i tehničke komponente).

Projekat je razvijen primenom objektno orijentisanog programiranja (OOP) i **Builder** obrasca, uz korišćenje naprednijih Python mogućnosti kao što su enumeracije (`Enum`, `StrEnum`), nepromenljive dataklase (`@dataclass(frozen=True)`), `TypedDict`, `Unpack`, `@overload` i stroge runtime validacije.

Poseban akcenat stavljen je na nepromenljivost domen-objekata nakon kreiranja, jasnu separaciju privremenog nacrta tokom sklapanja od konačne validirane instance, zaštitu od pogrešnih tipova i van-opsežnih vrednosti, kao i bezbedno pravljenje izmenjenih kopija.

---

## 🚀 Glavne funkcionalnosti

Sistem pruža sledeće mogućnosti:

* **Nepromenljivi domen-model:** `BikeLimits`, `BikeComponents` i `MotoGPBike` definisani su kao `@dataclass(frozen=True)`, čime se sprečava naknadna izmena stanja postojećih instanci.
* **Strogo tipizovani šifrarnici i strukture izmena:** Korišćenje `Enum` (`Team`), `StrEnum` (`ComponentSlot`) i `TypedDict` (`ComponentUpdates`, `BikeUpdates`) za jasne tipne ugovore.
* **Postepeno sklapanje kroz Builder obrazac:** `MotoGPBikeBuilder` obezbeđuje fluent `set_*` metode, proveru nedostajućih obaveznih polja pri `build()`, kloniranje nacrta (`clone()`) i resetovanje stanja (`reset()` ili `reset_after_build=True`).
* **Immutabilne izmene (`with_updates`):** Kreiranje novih instanci `MotoGPBike` ili `BikeComponents` sa izmenjenim vrednostima uz ponovno pokretanje validacije i očuvanje originalnog objekta.
* **Spajanje izmena komponenti:** Pri pozivu `MotoGPBike.with_updates(components=...)` sa mapiranjem, izmene se spajaju sa postojećim `BikeComponents` uz očuvanje nepromenjenih slotova.
* **Striktnu runtime validaciju:** Provera tipova (uključujući zaštitu od `bool` kao podklase `int`), konačnosti brojeva (`math.isfinite`), minimalnih i maksimalnih granica i nepraznih tekstualnih opisa.
* **Formatiran tekstualni prikaz:** Implementiran `__str__` na `MotoGPBike` za pregledan višelinjski ispis specifikacija i tehničkih komponenti.

---

## 🛠️ Tehnologije i biblioteke

Projekat koristi isključivo standardne Python biblioteke, bez potrebe za instaliranjem dodatnih eksternih paketa.

| Modul / tehnologija | Namena |
| --- | --- |
| `dataclasses` | Definisanje nepromenljivih struktura podataka (`dataclass`, `field`, `replace`) |
| `enum` | Definisanje fabričkih timova (`Enum`) i slotova komponenti (`StrEnum`) |
| `typing` | Napredne tipske anotacije (`Self`, `TypedDict`, `Unpack`, `cast`, `overload`) |
| `collections.abc` | Apstraktni interfejs za mapiranja (`Mapping`) |
| `math` | Provera konačnosti brojeva (`math.isfinite`) |
| `__future__.annotations` | Odložena evaluacija tipskih anotacija |
| OOP i Builder obrazac | Organizacija domenskog modela, validacije i postepene izgradnje objekata |

---

## 📂 Arhitektura i organizacija koda

Implementacija je organizovana po slojevima odgovornosti — od enumeracija i validacionih funkcija do nepromenljivog domen-modela i graditelja.

### `Team` i `ComponentSlot` – Enumeracije

* `Team` (`Enum`) definiše dozvoljene fabričke timove sa čitljivim string vrednostima: `DUCATI`, `APRILIA`, `KTM`, `HONDA` i `YAMAHA`.
* `ComponentSlot` (`StrEnum`) definiše slotove tehničkih komponenti (`AERODYNAMICS = "aerodynamics"`, `TYRES = "tyres"`, `ELECTRONICS = "electronics"`, `EXHAUST = "exhaust"`), tako da članovi istovremeno funkcionišu kao stringovi i odgovaraju poljima u `BikeComponents`.

### `ComponentUpdates` i `BikeUpdates` – `TypedDict` strukture

* `ComponentUpdates` (`TypedDict`, `total=False`) opisuje opcioni rečnik parcijalnih izmena nad tehničkim komponentama (`aerodynamics`, `tyres`, `electronics`, `exhaust`).
* `BikeUpdates` (`TypedDict`, `total=False`) definiše dozvoljena polja za `MotoGPBike.with_updates(...)`, pri čemu `components` može biti `BikeComponents` ili `ComponentUpdates`.

### Pomoćne funkcije za validaciju

* `_validate_non_empty_str` – Proverava da je vrednost `str` (`TypeError`), uklanja razmake sa `.strip()` i proverava da nije prazna (`ValueError`).
* `_validate_number`, `_validate_int` i `_validate_float` – Proveravaju tipove (eksplicitno odbacujući `bool`), proveravaju `math.isfinite` i primenjuju ekskluzivne (`min_exclusive`) i inkluzivne (`min_inclusive`, `max_inclusive`) granice.

### `BikeLimits` i `DEFAULT_BIKE_LIMITS` – Tehnička ograničenja

Nepromenljiva dataklasa (`@dataclass(frozen=True)`) koja definiše minimalne i maksimalne granice za motocikl:

* `max_engine_capacity_cc` (`int`, podrazumevano `1000`, `> 0`)
* `max_horsepower` (`int`, podrazumevano `350`, `> 0`)
* `min_weight_kg` (`float`, podrazumevano `100.0`, `> 0.0`)
* `max_weight_kg` (`float`, podrazumevano `250.0`, `>= min_weight_kg`)

`DEFAULT_BIKE_LIMITS` obezbeđuje podrazumevanu instancu ograničenja za ponovnu upotrebu.

### `BikeComponents` – Nepromenljivi sklop komponenti

Nepromenljiva dataklasa (`@dataclass(frozen=True)`) koja čuva obavezne tekstualne opise za `aerodynamics`, `tyres`, `electronics` i `exhaust`, uz validaciju svakog slota u `__post_init__`, konstruktor `from_slot_mapping(...)`, bezbedno čitanje preko `get(slot)` i kreiranje izmenjenih kopija preko `with_updates(...)`.

### `MotoGPBike` – Nepromenljivi model motocikla

Glavni domen-objekat definisan sa `@dataclass(frozen=True, kw_only=True)`:

* `team` (`Team`) – Fabrički tim
* `engine_capacity` (`int`) – Zapremina motora u `cc`
* `horsepower` (`int`) – Snaga u `hp`
* `weight` (`float`) – Masa motocikla u `kg`
* `components` (`BikeComponents`) – Tehničke komponente
* `limits` (`BikeLimits`) – Tehnička ograničenja (`default=DEFAULT_BIKE_LIMITS`, `repr=False`, `compare=False`)

### `_PartialBikeSpecs` i `MotoGPBikeBuilder` – Postepeno sklapanje

* `_PartialBikeSpecs` je promenljivi interni nacrt koji čuva privremena polja i rečnik izabranih komponenti tokom izgradnje, uz metode `missing_fields()` i `clone()`.
* `MotoGPBikeBuilder` upravlja nacrtom kroz fluent `set_*` metode, `clone()`, `reset()` i `build(*, reset_after_build=False)`.

---

## 🔍 Detaljniji pregled implementacije

* **Validacija opsega i tipova:** Pomoćne funkcije (`_validate_non_empty_str`, `_validate_number`, `_validate_int`, `_validate_float`) proveravaju tipove i granice pre upisa podataka, uz eksplicitnu proveru `isinstance(value, bool)` kako logičke vrednosti ne bi prošle kao `int`.
* **Validacija u `frozen` dataklasama:** Metode `__post_init__` u `BikeLimits`, `BikeComponents` i `MotoGPBike` validiraju polja i upisuju normalizovane vrednosti putem `object.__setattr__` jer su instance nepromenljive.
* **Poređenje bez zavisnosti od instance limita:** U `MotoGPBike` je `limits` postavljen sa `repr=False, compare=False`, pa se dva motocikla sa istim specifikacijama porede po samim karakteristikama motocikla.
* **Bezbedne izmene (`with_updates`):** `MotoGPBike.with_updates(...)` priprema izmene nad poljima, spaja `components` mapiranje sa postojećim `self.components.with_updates(...)` i vraća novu `MotoGPBike` instancu preko `dataclasses.replace(...)`.
* **Kloniranje i resetovanje buildera:** `MotoGPBikeBuilder.clone()` pravi nezavisnu kopiju nacrta sa `dict(self._specs.components)` kako izmene u jednoj grani ne bi uticale na drugu, dok `build()` proverava `missing_fields()` i po želji poziva `reset()`.
* **Čitljiv ispis (`__str__`):** `MotoGPBike.__str__` formatira višelinjski prikaz tima, zapremine motora (`cc`), snage (`hp`), mase (`kg`) i svih komponenti iz `ComponentSlot`.

---

## 💻 Primer korišćenja

Sledeći primer (iz `__main__`) prikazuje sklapanje osnovnog motocikla i kreiranje izmenjene varijante:

```python
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

```

U ovom primeru `bike` ostaje nepromenjen (`300 hp`, `"Soft"` pneumatici), dok `qualifying_bike` predstavlja novu instancu sa `310 hp` i `"Medium"` pneumaticima.

---

## 🏗️ Primena objektno orijentisanih principa

* **Enkapsulacija:** Ostvarena kroz privatne/interne validacione funkcije, `_PartialBikeSpecs`, `object.__setattr__` za normalizaciju u `frozen` dataklasama i kontrolisane metode `get()` i `with_updates()`.
* **Apstrakcija:** Domenski koncepti su izdvojeni u jasne celine (`Team`, `ComponentSlot`, `BikeLimits`, `BikeComponents`, `MotoGPBike`, `MotoGPBikeBuilder`).
* **Immutability (nepromenljivost):** Korišćenje `@dataclass(frozen=True)` na `BikeLimits`, `BikeComponents` i `MotoGPBike` sprečava mutaciju kreiranih objekata i olakšava bezbedan rad sa kopijama.
* **Builder obrazac:** Razdvaja postepeno popunjavanje i proveru nedostajućih polja (`MotoGPBikeBuilder` + `_PartialBikeSpecs`) od konačne, validirane instance `MotoGPBike`.
* **Kohezija i polimorfizam tipova:** Svaka struktura ima jasnu odgovornost, dok upotreba `Mapping`, `Enum` i `StrEnum` obezbeđuje fleksibilne i čitljive interfejse.

---

## 🔮 Moguća unapređenja

* Eksplicitnija validacija ključeva u `MotoGPBike.with_updates(components=...)` kako bi nepoznati ključevi davali jasniju domensku grešku umesto `TypeError` iz `dataclasses.replace`.
* Dodavanje domen-operacija i dodatnih pravila (npr. unapred definisani setup profili, proračun odnosa snage i mase ili specifična ograničenja po timu).
* Podrška za serijalizaciju i deserijalizaciju (npr. u JSON ili rečnik) uz očuvanje `Team` i `ComponentSlot` vrednosti.
* Uvođenje automatizovanih jediničnih testova (`pytest` ili `unittest`) za sve granične slučajeve validacije, `clone()`, `reset()` i `with_updates()`.

---

## ⚠️ Ograničenja

Podaci o motociklima i nacrtima čuvaju se isključivo u memoriji tokom izvršavanja programa i nisu trajno sačuvani. Tehnički limiti (`BikeLimits`) predstavljaju domenske okvire validacije u ovom modelu, a ne potpunu simulaciju zvaničnih pravilnika ili dinamike vožnje. Takođe, `TypedDict`, `@overload` i `Unpack` služe statičkoj analizi tipova i ne zamenjuju runtime provere u samom Python kodu.

---

## 📝 Zaključak

Ovaj domen-model pruža čist, čitljiv i pouzdan Python kod za opisivanje i sklapanje `MotoGPBike` instanci uz strogu runtime validaciju, nepromenljivost i **Builder** obrazac. Predstavlja dobru osnovu za dalje proširivanje poslovne logike, testova i integraciju u veće aplikacije.

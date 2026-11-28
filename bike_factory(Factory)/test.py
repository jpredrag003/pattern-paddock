from __future__ import annotations

import json
import math
from types import MappingProxyType
import unittest

from main import (
    BikeSpec,
    Manufacturer,
    Motorcycle,
    MotorcycleFactory,
    Rider,
    UnknownManufacturerError,
)


class TestManufacturer(unittest.TestCase):
    def test_from_input_case_insensitive_and_whitespace(self) -> None:
        self.assertIs(Manufacturer.from_input("ducati"), Manufacturer.DUCATI)
        self.assertIs(Manufacturer.from_input("  ApRiLiA \n\t"), Manufacturer.APRILIA)
        self.assertIs(Manufacturer.from_input("KTM"), Manufacturer.KTM)

    def test_from_input_unknown_raises_unknown_manufacturer_error(self) -> None:
        with self.assertRaises(UnknownManufacturerError):
            Manufacturer.from_input("BMW")
        with self.assertRaises(UnknownManufacturerError):
            Manufacturer.from_input("   ")

    def test_from_input_non_str_raises_type_error(self) -> None:
        for bad_value in (None, 123, True, ["Ducati"]):
            with self.subTest(bad_value=bad_value):
                with self.assertRaises(TypeError):
                    Manufacturer.from_input(bad_value)

    def test_coerce_accepts_enum_or_str(self) -> None:
        self.assertIs(Manufacturer.coerce(Manufacturer.HONDA), Manufacturer.HONDA)
        self.assertIs(Manufacturer.coerce("  yamaha "), Manufacturer.YAMAHA)
        with self.assertRaises(UnknownManufacturerError):
            Manufacturer.coerce("Kawasaki")


class TestBikeSpec(unittest.TestCase):
    def test_valid_creation_strips_model_and_converts_acceleration_to_float(self) -> None:
        spec = BikeSpec(model="  Panigale V4  ", max_speed=320, acceleration=3)
        self.assertEqual(spec.model, "Panigale V4")
        self.assertEqual(spec.max_speed, 320)
        self.assertIsInstance(spec.acceleration, float)
        self.assertEqual(spec.acceleration, 3.0)

    def test_frozen_immutability(self) -> None:
        spec = BikeSpec("RSV4", 315, 2.8)
        with self.assertRaises(AttributeError):
            spec.max_speed = 330  # type: ignore[misc]

    def test_invalid_model(self) -> None:
        for bad_model in ("", "   \t\n  "):
            with self.subTest(bad_model=bad_model):
                with self.assertRaises(ValueError):
                    BikeSpec(bad_model, 300, 3.0)

        for non_str in (None, 42, False):
            with self.subTest(non_str=non_str):
                with self.assertRaises(TypeError):
                    BikeSpec(non_str, 300, 3.0)  # type: ignore[arg-type]

    def test_invalid_max_speed(self) -> None:
        for bad_int in (0, -1, -250):
            with self.subTest(bad_int=bad_int):
                with self.assertRaises(ValueError):
                    BikeSpec("Model X", bad_int, 3.0)

        for non_int in (True, False, 300.0, "300", None):
            with self.subTest(non_int=non_int):
                with self.assertRaises(TypeError):
                    BikeSpec("Model X", non_int, 3.0)  # type: ignore[arg-type]

    def test_invalid_acceleration(self) -> None:
        for bad_num in (0, 0.0, -2.5, math.inf, -math.inf, math.nan):
            with self.subTest(bad_num=bad_num):
                with self.assertRaises(ValueError):
                    BikeSpec("Model X", 300, bad_num)

        for non_num in (True, False, "2.8", None):
            with self.subTest(non_num=non_num):
                with self.assertRaises(TypeError):
                    BikeSpec("Model X", 300, non_num)  # type: ignore[arg-type]

    def test_with_overrides(self) -> None:
        original = BikeSpec("YZF-R1", 299, 2.9)
        self.assertIs(original.with_overrides(), original)

        updated = original.with_overrides(model=" R1M ", max_speed=305)
        self.assertIsNot(updated, original)
        self.assertEqual(updated.model, "R1M")
        self.assertEqual(updated.max_speed, 305)
        self.assertEqual(updated.acceleration, 2.9)

        with self.assertRaises(ValueError):
            original.with_overrides(max_speed=0)

    def test_to_dict_and_from_dict_round_trip(self) -> None:
        original = BikeSpec("CBR1000RR-R", 305, 2.8)
        as_dict = original.to_dict()
        self.assertEqual(
            as_dict,
            {"model": "CBR1000RR-R", "max_speed": 305, "acceleration": 2.8},
        )
        rebuilt = BikeSpec.from_dict(as_dict)
        self.assertEqual(rebuilt, original)

    def test_from_dict_errors(self) -> None:
        with self.assertRaises(TypeError):
            BikeSpec.from_dict(["not", "a", "mapping"])

        with self.assertRaises(KeyError):
            BikeSpec.from_dict({"model": "R1", "max_speed": 299})


class TestMotorcycleAndRider(unittest.TestCase):
    def test_motorcycle_from_fields_and_properties(self) -> None:
        bike = Motorcycle.from_fields("  ducati ", " Panigale V4 ", 320, 2.7)
        self.assertIs(bike.manufacturer, Manufacturer.DUCATI)
        self.assertEqual(bike.model, "Panigale V4")
        self.assertEqual(bike.max_speed, 320)
        self.assertEqual(bike.acceleration, 2.7)
        self.assertIn("Manufacturer: Ducati", str(bike))
        self.assertIn("320 km/h, Acceleration: 2.7s", str(bike))

    def test_motorcycle_invalid_types(self) -> None:
        spec = BikeSpec("RSV4", 315, 2.8)
        with self.assertRaises(TypeError):
            Motorcycle(manufacturer="Aprilia", spec=spec)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            Motorcycle(manufacturer=Manufacturer.APRILIA, spec="spec")  # type: ignore[arg-type]

    def test_motorcycle_dict_round_trip_and_errors(self) -> None:
        bike = Motorcycle.from_fields("KTM", "1290 Super Duke R", 290, 2.9)
        payload = bike.to_dict()
        self.assertEqual(
            payload,
            {
                "manufacturer": "KTM",
                "model": "1290 Super Duke R",
                "max_speed": 290,
                "acceleration": 2.9,
            },
        )
        self.assertEqual(Motorcycle.from_dict(payload), bike)

        with self.assertRaises(KeyError):
            Motorcycle.from_dict({"model": "1290 Super Duke R", "max_speed": 290, "acceleration": 2.9})

        with self.assertRaises(UnknownManufacturerError):
            Motorcycle.from_dict(
                {"manufacturer": "DucatiCorseUnknown", "model": "X", "max_speed": 250, "acceleration": 3.0}
            )

    def test_rider_creation_stripping_and_json_round_trip(self) -> None:
        bike = Motorcycle.from_fields("Yamaha", "YZF-R1", 299, 2.9)
        rider = Rider("  Marko  ", "  Srbija  ", bike)
        self.assertEqual(rider.name, "Marko")
        self.assertEqual(rider.country, "Srbija")
        self.assertIn("Rider: Marko (Srbija)", str(rider))

        raw_json = rider.to_json(indent=None)
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["name"], "Marko")
        self.assertEqual(parsed["bike"]["manufacturer"], "Yamaha")

        rebuilt = Rider.from_json(raw_json)
        self.assertEqual(rebuilt, rider)

    def test_rider_validation_and_json_errors(self) -> None:
        bike = Motorcycle.from_fields("Honda", "CBR1000RR-R", 305, 2.8)
        with self.assertRaises(ValueError):
            Rider("   ", "Srbija", bike)
        with self.assertRaises(ValueError):
            Rider("Marko", "", bike)
        with self.assertRaises(TypeError):
            Rider("Marko", "Srbija", bike.spec)  # type: ignore[arg-type]

        with self.assertRaises(TypeError):
            Rider.from_json(12345)  # type: ignore[arg-type]
        with self.assertRaises(json.JSONDecodeError):
            Rider.from_json("{invalid json")
        with self.assertRaises(TypeError):
            Rider.from_json(json.dumps(["not", "an", "object"]))


class TestMotorcycleFactory(unittest.TestCase):
    def test_default_catalog_is_read_only(self) -> None:
        factory = MotorcycleFactory()
        self.assertIsInstance(factory.catalog, MappingProxyType)
        with self.assertRaises(TypeError):
            factory.catalog[Manufacturer.DUCATI] = BikeSpec("Custom", 350, 2.0)  # type: ignore[index]

    def test_custom_catalog_validation(self) -> None:
        custom_spec = BikeSpec("Panigale V2", 260, 3.2)
        factory = MotorcycleFactory({Manufacturer.DUCATI: custom_spec})
        self.assertEqual(factory.get_spec("ducati"), custom_spec)

        with self.assertRaises(UnknownManufacturerError):
            factory.get_spec(Manufacturer.HONDA)

        with self.assertRaises(TypeError):
            MotorcycleFactory({"Ducati": custom_spec})  # type: ignore[dict-item]

        with self.assertRaises(TypeError):
            MotorcycleFactory({Manufacturer.DUCATI: "not-a-spec"})  # type: ignore[dict-item]

    def test_create_motorcycle_default_and_overrides(self) -> None:
        factory = MotorcycleFactory()
        default_bike = factory.create_motorcycle("honda")
        self.assertEqual(default_bike.model, "CBR1000RR-R")
        self.assertEqual(default_bike.max_speed, 305)

        custom_bike = factory.create_motorcycle(
            Manufacturer.APRILIA,
            model="RS 660",
            max_speed=240,
            acceleration=3.6,
        )
        self.assertEqual(custom_bike.model, "RS 660")
        self.assertEqual(custom_bike.max_speed, 240)
        self.assertEqual(custom_bike.acceleration, 3.6)
        # Originalni katalog mora ostati nepromenjen
        self.assertEqual(factory.get_spec(Manufacturer.APRILIA).model, "RSV4")

    def test_create_all_catalog_bikes_and_sorting(self) -> None:
        factory = MotorcycleFactory()
        all_bikes = factory.create_all_catalog_bikes()
        self.assertEqual(len(all_bikes), len(Manufacturer))

        sorted_bikes = factory.create_all_catalog_bikes(sort_by_speed_desc=True)
        speeds = [bike.max_speed for bike in sorted_bikes]
        self.assertEqual(speeds, sorted(speeds, reverse=True))
        self.assertEqual(sorted_bikes[0].manufacturer, Manufacturer.DUCATI)

    def test_find_faster_than(self) -> None:
        factory = MotorcycleFactory()
        faster = factory.find_faster_than(305)
        self.assertEqual([bike.manufacturer for bike in faster], [Manufacturer.DUCATI, Manufacturer.APRILIA])

        # Strogo veće (>) — brzina tačno 320 ne ulazi u rezultat > 320
        self.assertEqual(factory.find_faster_than(320), [])

        # Negativan prag je dozvoljen jer validira samo da je int (ne bool)
        self.assertEqual(len(factory.find_faster_than(-10)), len(Manufacturer))

        with self.assertRaises(TypeError):
            factory.find_faster_than(True)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            factory.find_faster_than("300")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main(verbosity=2)

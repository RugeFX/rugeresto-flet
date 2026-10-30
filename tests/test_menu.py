import csv

import pytest

from shared.restaurant import (
    MENU_FIELDS,
    DataFileError,
    MenuItem,
    RestaurantSystem,
    load_menu,
)


def write_menu(path, records):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, MENU_FIELDS)
        writer.writeheader()
        writer.writerows(records)


def test_csv_catalog_and_categories_are_dynamic(data_dir):
    path = data_dir / "menu.csv"
    write_menu(
        path,
        [
            {
                "number": 7,
                "name": "Kopi",
                "price": 12000,
                "category": "Baru",
                "detail": "Panas",
            }
        ],
    )
    assert load_menu(path) == (MenuItem(7, "Kopi", 12000, "Baru", "Panas"),)
    app = RestaurantSystem(data_dir)
    assert app.search_menu("  KOPI  ") == app.menu
    app.add_order(7)
    assert app.calculate_total() == 12000


@pytest.mark.parametrize(
    "change",
    [
        {"number": 0},
        {"price": -1},
        {"price": "bad"},
        {"name": " "},
        {"category": ""},
        {"detail": ""},
    ],
)
def test_csv_catalog_validation(data_dir, change):
    record = {
        "number": 7,
        "name": "Kopi",
        "price": 12000,
        "category": "Minuman",
        "detail": "Panas",
    }
    record.update(change)
    write_menu(data_dir / "menu.csv", [record])
    with pytest.raises(DataFileError):
        RestaurantSystem(data_dir)


def test_duplicate_csv_menu_number_rejected(data_dir):
    record = {
        "number": 1,
        "name": "Kopi",
        "price": 12000,
        "category": "Minuman",
        "detail": "Panas",
    }
    write_menu(data_dir / "menu.csv", [record, record])
    with pytest.raises(DataFileError, match="duplicate"):
        RestaurantSystem(data_dir)

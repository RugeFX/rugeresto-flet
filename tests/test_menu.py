import json

import pytest

from shared.restaurant import MenuItem, load_menu


def test_load_menu_reads_custom_records(tmp_path, monkeypatch):
    path = tmp_path / "menu.json"
    path.write_text(
        json.dumps(
            [
                {
                    "number": 7,
                    "name": "Kopi",
                    "price": 12000,
                    "category": "Minuman",
                    "detail": "Kopi panas",
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert load_menu(path) == (MenuItem(7, "Kopi", 12000, "Minuman", "Kopi panas"),)
    assert load_menu()[0].name == "Nasi Goreng"


@pytest.mark.parametrize(
    "change, error",
    [
        ({"number": True}, TypeError),
        ({"number": 0}, ValueError),
        ({"price": -1}, ValueError),
        ({"price": "12000"}, TypeError),
        ({"name": " "}, ValueError),
        ({"category": None}, TypeError),
        ({"detail": 3}, TypeError),
    ],
)
def test_load_menu_rejects_invalid_fields(tmp_path, change, error):
    record = {
        "number": 7,
        "name": "Kopi",
        "price": 12000,
        "category": "Minuman",
        "detail": "Kopi panas",
    }
    record.update(change)
    path = tmp_path / "menu.json"
    path.write_text(json.dumps([record]), encoding="utf-8")

    with pytest.raises(error):
        load_menu(path)


@pytest.mark.parametrize(
    "records, error",
    [
        ({}, TypeError),
        ([None], TypeError),
        ([{}], ValueError),
        (
            [
                {
                    "number": 1,
                    "name": "A",
                    "price": 1,
                    "category": "Food",
                    "detail": "A",
                },
                {
                    "number": 1,
                    "name": "B",
                    "price": 2,
                    "category": "Food",
                    "detail": "B",
                },
            ],
            ValueError,
        ),
    ],
)
def test_load_menu_rejects_bad_structure_and_duplicate_numbers(
    tmp_path, records, error
):
    path = tmp_path / "menu.json"
    path.write_text(json.dumps(records), encoding="utf-8")

    with pytest.raises(error):
        load_menu(path)

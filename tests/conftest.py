import shutil
from pathlib import Path

import pytest

from shared.restaurant import ORDER_FIELDS, TRANSACTION_FIELDS


@pytest.fixture
def data_dir(tmp_path):
    root = Path(__file__).resolve().parents[1]
    shutil.copy(root / "data/menu.csv", tmp_path / "menu.csv")
    for name, fields in [
        ("active_order.csv", ORDER_FIELDS),
        ("transactions.csv", TRANSACTION_FIELDS),
    ]:
        (tmp_path / name).write_text(",".join(fields) + "\n", encoding="utf-8")
    return tmp_path

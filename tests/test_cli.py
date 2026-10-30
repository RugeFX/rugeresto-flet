import os
import shutil
import subprocess
import sys
from pathlib import Path

from cli import run_cli
from shared.restaurant import RestaurantSystem


def test_base_and_extended_cli_continue_the_same_saved_order(data_dir, tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = {
        **os.environ,
        "PYTHONPATH": str(root / "src"),
        "RUGERESTO_DATA_DIR": str(data_dir),
    }

    def run(entry, answers):
        return subprocess.run(
            [sys.executable, *entry],
            input="\n".join(answers) + "\n",
            text=True,
            capture_output=True,
            cwd=tmp_path,
            env=env,
            check=True,
        ).stdout

    base_entry = [str(root / "src/base.py"), "--data-dir", str(data_dir)]
    run(base_entry, ["2", "1", "2", "10"])
    paid = run(["-m", "cli"], ["3", "6", "50000", "10"])
    assert "Restored 1 saved order line" in paid
    assert "Nasi Goreng x2 - Rp40,000" in paid
    assert "Change  : Rp10,000" in paid
    history = run(base_entry, ["3", "8", "10"])
    assert "Your order is empty" in history
    assert "Transactions: 1 | Sales: Rp40,000" in history


def test_cli_uses_persistent_shared_rules(data_dir):
    answers = iter(["2", "1", "2", "6", "30000", "6", "50000", "8", "10"])
    output = []
    run_cli(
        RestaurantSystem(data_dir), read=lambda _: next(answers), write=output.append
    )
    text = "\n".join(output)
    assert "still need Rp10,000" in text
    assert "Change  : Rp10,000" in text
    assert "Transactions: 1 | Sales: Rp40,000" in text
    assert output[-1] == "Program closed."
    assert len(RestaurantSystem(data_dir).get_transactions()) == 1


def test_base_and_extended_cli_match_flows_with_separate_data(data_dir, tmp_path):
    root = Path(__file__).resolve().parents[1]
    other = tmp_path / "base-data"
    shutil.copytree(data_dir, other)
    answers = "1\n7\n NASI   GORENG \n2\n1\n2\n4\n1\n1\n3\n10" + "\n"
    env = {**os.environ, "PYTHONPATH": str(root / "src")}
    outputs = []
    for entry, directory in [
        ([str(root / "src/base.py")], other),
        (["-m", "cli"], data_dir),
    ]:
        result = subprocess.run(
            [sys.executable, *entry, "--data-dir", str(directory)],
            input=answers,
            text=True,
            capture_output=True,
            cwd=tmp_path,
            env=env,
            check=True,
        )
        outputs.append(result.stdout)
        assert result.stderr == ""
    assert outputs[0] == outputs[1]
    restored = RestaurantSystem(data_dir)
    assert restored.calculate_total() == 20000
    receipt = restored.payment(30000)
    result = subprocess.run(
        [sys.executable, "-m", "cli", "--data-dir", str(data_dir)],
        input=f"8\n9\n{receipt.order_id}\n10\n",
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=env,
        check=True,
    )
    assert "Transactions: 1 | Sales: Rp20,000" in result.stdout
    assert "Change  : Rp10,000" in result.stdout

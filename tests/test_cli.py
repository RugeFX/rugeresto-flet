import subprocess
import sys
from pathlib import Path

import pytest

from cli import run_cli


def test_cli_uses_shared_order_and_payment_rules():
    answers = iter(["2", "1", "2", "3", "6", "30000", "6", "50000", "7"])
    output = []
    run_cli(read=lambda _: next(answers), write=output.append)
    assert "1. Nasi Goreng - Rp20,000" in output
    assert "1. Nasi Goreng x2 - Rp40,000" in output
    assert "You still need Rp10,000" in output
    assert "Payment : Rp50,000" in output
    assert "Change  : Rp10,000" in output
    assert output[-1] == "Program closed."


@pytest.mark.parametrize(
    "answers",
    [
        [
            "1",
            "2",
            "3",
            "2",
            "2",
            "4",
            "1",
            "3",
            "4",
            "2",
            "3",
            "5",
            "1",
            "6",
            "1",
            "6",
            "20000",
            "3",
            "q",
        ],
        [
            "3",
            "4",
            "5",
            "6",
            "bad",
            "2",
            "bad",
            "2",
            "99",
            "2",
            "1",
            "bad",
            "2",
            "1",
            "0",
            "2",
            "1",
            "1",
            "4",
            "bad",
            "4",
            "99",
            "4",
            "1",
            "bad",
            "4",
            "1",
            "0",
            "5",
            "bad",
            "5",
            "99",
            "6",
            "bad",
            "exit",
        ],
    ],
)
def test_cli_transcript_matches_base_reference(answers):
    src = Path(__file__).resolve().parents[1] / "src"
    transcripts = []
    for entry in ([str(src / "base.py")], ["-m", "cli"]):
        result = subprocess.run(
            [sys.executable, *entry],
            cwd=src,
            input="\n".join(answers) + "\n",
            text=True,
            capture_output=True,
            check=True,
        )
        transcripts.append(result.stdout)
    assert transcripts[0] == transcripts[1]

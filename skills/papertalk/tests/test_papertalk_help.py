from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "papertalk_help.py"


class PaperTalkHelpTests(unittest.TestCase):
    def run_help(self, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        process = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(process.returncode, 0, process.stderr or process.stdout)
        return process

    def test_fixed_markdown_lists_every_public_function(self) -> None:
        result = self.run_help()
        expected_functions = {
            "help",
            "add",
            "list",
            "use",
            "remove",
            "removed",
            "restore",
            "author",
            "reviewer",
            "researcher",
            "panel",
            "panel_continue",
            "explain",
            "why",
            "derive",
            "critique",
            "summarize",
            "extend",
            "attack",
        }

        self.assertIn("# PaperTalk Help", result.stdout)
        self.assertIn("| Function | Example | Explanation |", result.stdout)
        self.assertIn("$papertalk add <alias> <public_link>", result.stdout)
        self.assertNotIn("sgm", result.stdout.lower())
        self.assertFalse(any("\u4e00" <= character <= "\u9fff" for character in result.stdout))
        self.assertEqual(result.stdout.count("| `$papertalk"), 19)
        for function in expected_functions:
            self.assertIn(f"| `{function}` |", result.stdout)

    def test_script_returns_the_memo_byte_for_byte(self) -> None:
        result = self.run_help()
        memo = SCRIPT.parents[1] / "references" / "help-output.md"
        self.assertEqual(result.stdout, memo.read_text(encoding="utf-8"))

    def test_help_is_state_free(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self.run_help(cwd=workspace)
            self.assertFalse((workspace / ".papertalk").exists())


if __name__ == "__main__":
    unittest.main()

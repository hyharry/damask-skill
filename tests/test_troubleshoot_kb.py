from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "troubleshoot_kb.py"
SPEC = importlib.util.spec_from_file_location("troubleshoot_kb", SCRIPT)
assert SPEC and SPEC.loader
kb = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = kb
SPEC.loader.exec_module(kb)


class TroubleshootingKnowledgeBaseTests(unittest.TestCase):
    def run_helper(self, *arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_error_950_returns_complete_sourced_debug_cards(self) -> None:
        result = self.run_helper("error 950", "--category", "debug", "--limit", "2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("discussion", result.stdout.casefold())
        self.assertIn("discussions/75", result.stdout)
        self.assertIn("**Problem:**", result.stdout)
        self.assertIn("**Fix / steps:**", result.stdout)
        self.assertIn("upstream status:", result.stdout)

    def test_all_categories_are_default_and_selected_category_can_fallback(self) -> None:
        all_result = self.run_helper("IPF visualisation")
        self.assertEqual(all_result.returncode, 0, all_result.stderr)
        self.assertIn("category: post", all_result.stdout)

        fallback = self.run_helper(
            "IPF visualisation", "--category", "run", "--fallback-all"
        )
        self.assertEqual(fallback.returncode, 0, fallback.stderr)
        self.assertIn("searched all categories", fallback.stdout)
        self.assertIn("category: post", fallback.stdout)

    def test_no_match_is_clear_and_nonzero(self) -> None:
        result = self.run_helper("no-such-damask-symptom-xyzzy", "--category", "debug")
        self.assertEqual(result.returncode, 1)
        self.assertIn("No matching troubleshooting cards", result.stdout)
        self.assertIn("Retry with no --category", result.stdout)

    def test_limit_is_respected(self) -> None:
        result = self.run_helper("material", "--limit", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("===== Match"), 1)

    def test_helper_works_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_helper("error 950", cwd=Path(directory))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("discussions/75", result.stdout)

    def test_verify_counts_complete_cards(self) -> None:
        result = self.run_helper("--verify")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("verified 102 complete cards", result.stdout)

    def test_installer_includes_helper_kb_and_internal_links(self) -> None:
        files = kb.SKILL_ROOT.joinpath("scripts", "install_skill.py")
        spec = importlib.util.spec_from_file_location("install_skill", files)
        assert spec and spec.loader
        installer = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = installer
        spec.loader.exec_module(installer)
        included = set(installer.source_files(include_vendor_metadata=False))
        self.assertIn(Path("scripts/troubleshoot_kb.py"), included)
        for category in (*kb.CATEGORIES, "README"):
            name = f"{category}.md"
            relative = Path("references/troubleshooting-kb") / name
            self.assertIn(relative, included)
        readme = (ROOT / "references" / "troubleshooting-kb" / "README.md").read_text(encoding="utf-8")
        for category in kb.CATEGORIES:
            self.assertIn(f"({category}.md)", readme)


if __name__ == "__main__":
    unittest.main()

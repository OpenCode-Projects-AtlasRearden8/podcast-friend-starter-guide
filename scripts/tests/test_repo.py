"""Repo hygiene: secrets scan, license text, README quality, wrapper scripts."""

import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class SecretScanTests(unittest.TestCase):
    SECRET_PATTERNS = {
        "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
        "api-key": re.compile(r"\b(sk|pk)-[A-Za-z0-9_]{20,}\b"),
        "github-token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
        "private-key-block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    }

    def test_no_secrets_anywhere(self):
        skips = (".git", "__pycache__", ".pytest_cache")
        for path in sorted(ROOT.rglob("*")):
            if any(part in skips for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in {
                    ".md", ".html", ".py", ".css", ".sh", ".yml", ".yaml",
                    ".json", ".txt", "", ".gitignore"}:
                with self.subTest(path=path.relative_to(ROOT).as_posix()):
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    for label, pattern in self.SECRET_PATTERNS.items():
                        self.assertIsNone(pattern.search(text),
                                          "%s looks like a %s"
                                          % (path, label))

    def test_no_personal_contact_details(self):
        """The repo publishes LLC contact, not Dylan's personal details."""
        skips = (".git", "__pycache__")
        pattern = re.compile(r"(?i)\b(?:\+?1[-. ]?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4})\b")
        for path in sorted(ROOT.rglob("*")):
            if any(part in skips for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in {".md", ".html", ".py"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
                self.assertIsNone(pattern.search(text), path)


class LicenseTests(unittest.TestCase):
    LICENSE = ROOT / "LICENSE"

    def test_license_is_mit_with_exact_copyright_line(self):
        text = self.LICENSE.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("MIT License"))
        self.assertIn("Copyright (c) 2026 Asdale Dynamics, LLC", text)
        self.assertIn('THE SOFTWARE IS PROVIDED "AS IS"', text)

    def test_readme_credits_asdale_dynamics(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Asdale Dynamics, LLC", readme)
        self.assertIn("MIT", readme)


class ProjectMetaTests(unittest.TestCase):
    def test_wrapper_scripts_runnable_content(self):
        for wrapper in ("build.sh", "test.sh"):
            text = (ROOT / wrapper).read_text(encoding="utf-8")
            with self.subTest(wrapper=wrapper):
                self.assertIn("#!/usr/bin/env sh", text)
                self.assertIn("set -e", text)

    def test_gitignore_hides_python_artifacts(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("__pycache__", text)


class NewEpisodeScriptTests(unittest.TestCase):
    def run_script(self, *argv):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "new_episode.py"), *argv],
            capture_output=True, text=True, cwd=ROOT)

    def test_creates_draft_from_single_line_title(self):
        out = pathlib.Path(tempfile.mkdtemp(prefix="pfsg-ep-"))
        try:
            result = self.run_script("--title", "My bedroom studio",
                                     "--number", "4", "--date", "2026-11-02",
                                     "--outdir", str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            path = out / "ep04-my-bedroom-studio.md"
            self.assertTrue(path.exists())
            text = path.read_text(encoding="utf-8")
            self.assertIn("# Episode 04: My bedroom studio", text)
            self.assertIn("2026-11-02", text)
            self.assertNotIn("{{", text)
        finally:
            import shutil
            shutil.rmtree(out)

    def test_refuses_to_overwrite(self):
        out = pathlib.Path(tempfile.mkdtemp(prefix="pfsg-ep-"))
        try:
            argv = ["--title", "Sample", "--number", "1", "--outdir", str(out)]
            self.assertEqual(self.run_script(*argv).returncode, 0)
            second = self.run_script(*argv)
            self.assertEqual(second.returncode, 1, second.stderr)
        finally:
            import shutil
            shutil.rmtree(out)


if __name__ == "__main__":
    unittest.main()

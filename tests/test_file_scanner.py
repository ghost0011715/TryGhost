import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from file_scanner import FileDuplicateFinder, FileScanner
from main import FileAnalysisApp
from utils import format_bytes


class FileScannerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "nested").mkdir()
        (self.root / "same.txt").write_text("duplicate", encoding="utf-8")
        (self.root / "nested" / "copy.txt").write_text(
            "duplicate", encoding="utf-8"
        )
        (self.root / "nested" / "unique.py").write_text(
            "print('hello')", encoding="utf-8"
        )
        (self.root / ".hidden.txt").write_text("hidden", encoding="utf-8")
        (self.root / "__pycache__").mkdir()
        (self.root / "__pycache__" / "ignored.pyc").write_bytes(b"bytecode")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scan_excludes_hidden_and_bytecode_by_default(self):
        files = FileScanner(self.root).scan_directory()
        self.assertEqual({item["name"] for item in files}, {
            "same.txt", "copy.txt", "unique.py"
        })

    def test_scan_includes_hidden_files_when_requested(self):
        files = FileScanner(self.root).scan_directory(include_hidden=True)
        self.assertEqual(len(files), 4)
        self.assertFalse(any(item["extension"] == ".pyc" for item in files))

    def test_statistics_and_extension_filter(self):
        scanner = FileScanner(self.root)
        files = scanner.scan_directory()
        stats = scanner.get_statistics(files)
        self.assertEqual(stats["total_files"], 3)
        self.assertEqual(stats["by_extension"], {".py": 1, ".txt": 2})
        self.assertEqual(len(scanner.filter_by_extension(files, [" PY "])), 1)

    def test_duplicate_detection_checks_content(self):
        files = FileScanner(self.root).scan_directory()
        groups = FileDuplicateFinder().find_duplicates(files)
        self.assertEqual(len(groups), 1)
        self.assertEqual(
            {item["name"] for item in next(iter(groups.values()))},
            {"same.txt", "copy.txt"},
        )

    def test_invalid_scan_paths_raise_clear_errors(self):
        with self.assertRaises(FileNotFoundError):
            FileScanner(self.root / "missing").scan_directory()
        with self.assertRaises(NotADirectoryError):
            FileScanner(self.root / "same.txt").scan_directory()

    def test_empty_statistics_and_byte_formatting(self):
        stats = FileScanner.get_statistics([])
        self.assertEqual(stats["total_files"], 0)
        self.assertIsNone(stats["largest_file"])
        self.assertEqual(format_bytes(1024), "1.00 KB")

    def test_analysis_is_local_and_summarizes_extensions(self):
        summary = FileAnalysisApp.analyze_files(
            FileScanner(self.root).scan_directory()
        )
        self.assertEqual(summary["total_files"], 3)
        self.assertEqual(summary["top_extensions"][0], {
            "extension": ".txt", "count": 2
        })


class CommandLineTests(unittest.TestCase):
    def test_help_starts(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[1] / "cli.py"), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--scan", result.stdout)

    def test_scan_writes_json_report_and_duplicate_results(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.txt").write_text("same", encoding="utf-8")
            (root / "two.txt").write_text("same", encoding="utf-8")
            report_path = root / "report.json"
            cli = Path(__file__).resolve().parents[1] / "cli.py"
            result = subprocess.run(
                [
                    sys.executable, str(cli), "--scan", str(root),
                    "--find-duplicates", "--analyze", "--output", str(report_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["total_files"], 2)
            self.assertEqual(len(report["duplicates"]), 1)
            self.assertEqual(report["analysis"]["total_files"], 2)


if __name__ == "__main__":
    unittest.main()

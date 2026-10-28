"""Interactive local file-scanning application."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any, Dict, List

from file_scanner import FileScanner
from utils import format_bytes, print_section, print_table


class FileAnalysisApp:
    """Interactive scanner; file contents stay on the local machine."""

    @staticmethod
    def analyze_files(files: List[Dict[str, Any]]) -> Dict[str, Any]:
        stats = FileScanner.get_statistics(files)
        top_extensions = sorted(
            stats["by_extension"].items(),
            key=lambda item: (-item[1], item[0]),
        )[:5]
        return {
            "total_files": stats["total_files"],
            "total_size_bytes": stats["total_size_bytes"],
            "largest_file": stats["largest_file"],
            "top_extensions": [
                {"extension": extension, "count": count}
                for extension, count in top_extensions
            ],
        }

    def _scan(self, path: str, include_hidden: bool = False) -> None:
        scanner = FileScanner(path)
        files = scanner.scan_directory(include_hidden=include_hidden)
        stats = scanner.get_statistics(files)

        print_section(f"Scanning: {path}")
        print(f"Found {len(files)} files")
        print(f"Total size: {format_bytes(stats['total_size_bytes'])}")
        if stats["largest_file"]:
            largest = stats["largest_file"]
            print(
                f"Largest: {largest['name']} "
                f"({format_bytes(largest['size_bytes'])})"
            )
        print_table([
            {
                "Name": item["name"],
                "Size": format_bytes(item["size_bytes"]),
                "Type": item["extension"],
                "Path": item["path"],
            }
            for item in files[:10]
        ])

    def start_interactive(self) -> None:
        print("FileScanner — local file scanning")
        print("Commands: scan [PATH], help, quit")
        while True:
            try:
                command = input("filescanner> ").strip()
            except EOFError:
                print()
                return

            if not command:
                continue
            try:
                parts = shlex.split(command)
            except ValueError as exc:
                print(f"Invalid command: {exc}")
                continue

            action = parts[0].casefold()
            if action in {"quit", "exit"}:
                return
            if action in {"help", "?"}:
                print("scan [PATH]  Scan PATH (default: current directory)")
                print("quit         Exit the application")
                continue
            if action != "scan" or len(parts) > 2:
                print("Unknown command. Type 'help' for available commands.")
                continue

            path = parts[1] if len(parts) == 2 else str(Path.cwd())
            try:
                self._scan(path)
            except OSError as exc:
                print(f"Scan failed: {exc}")

"""Local filesystem scanning and duplicate-file detection."""

from __future__ import annotations

import hashlib
import os
import stat
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

IGNORED_DIRECTORIES = {"__pycache__"}
IGNORED_EXTENSIONS = {".pyc", ".pyo"}


class FileScanner:
    """Collect metadata for files below a directory without following symlinks."""

    def __init__(self, root_path: Union[str, os.PathLike]) -> None:
        self.root_path = Path(root_path).expanduser()

    @staticmethod
    def _is_hidden(path: Path, file_stat: os.stat_result) -> bool:
        if path.name.startswith("."):
            return True
        attributes = getattr(file_stat, "st_file_attributes", 0)
        hidden_attribute = getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0)
        return bool(hidden_attribute and attributes & hidden_attribute)

    def scan_directory(self, include_hidden: bool = False) -> List[Dict[str, Any]]:
        if not self.root_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {self.root_path}")
        if not self.root_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.root_path}")

        files: List[Dict[str, Any]] = []
        pending = [self.root_path]
        while pending:
            directory = pending.pop()
            with os.scandir(directory) as entries:
                children = sorted(entries, key=lambda entry: entry.name.casefold())

            directories: List[Path] = []
            for entry in children:
                path = Path(entry.path)
                if entry.is_symlink():
                    continue
                file_stat = entry.stat(follow_symlinks=False)
                if not include_hidden and self._is_hidden(path, file_stat):
                    continue
                if stat.S_ISDIR(file_stat.st_mode):
                    if path.name.casefold() not in IGNORED_DIRECTORIES:
                        directories.append(path)
                    continue
                if not stat.S_ISREG(file_stat.st_mode):
                    continue
                if path.suffix.casefold() in IGNORED_EXTENSIONS:
                    continue
                files.append({
                    "name": path.name,
                    "path": str(path),
                    "size_bytes": file_stat.st_size,
                    "extension": path.suffix.lower() or "[no extension]",
                    "modified_time": file_stat.st_mtime,
                })
            pending.extend(reversed(directories))

        files.sort(key=lambda item: item["path"].casefold())
        return files

    @staticmethod
    def filter_by_extension(
        files: List[Dict[str, Any]], extensions: Union[List[str], tuple]
    ) -> List[Dict[str, Any]]:
        normalized = {
            extension.strip().casefold()
            if extension.strip().startswith(".")
            else f".{extension.strip().casefold()}"
            for extension in extensions
            if extension.strip()
        }
        return [item for item in files if item["extension"].casefold() in normalized]

    @staticmethod
    def get_statistics(files: List[Dict[str, Any]]) -> Dict[str, Any]:
        by_extension: Dict[str, int] = defaultdict(int)
        total_size = 0
        largest_file: Optional[Dict[str, Any]] = None
        for item in files:
            size = int(item["size_bytes"])
            total_size += size
            by_extension[item["extension"]] += 1
            if largest_file is None or size > largest_file["size_bytes"]:
                largest_file = item
        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "by_extension": dict(sorted(by_extension.items())),
            "largest_file": largest_file,
        }


class FileDuplicateFinder:
    """Find files with identical content, hashing only same-size candidates."""

    @staticmethod
    def _digest(path: str) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def find_duplicates(
        self, files: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        by_size: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for item in files:
            by_size[int(item["size_bytes"])].append(item)

        duplicate_groups: Dict[str, List[Dict[str, Any]]] = {}
        for same_size_files in by_size.values():
            if len(same_size_files) < 2:
                continue
            by_digest: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            for item in same_size_files:
                by_digest[self._digest(item["path"])].append(item)
            for digest, group in by_digest.items():
                if len(group) > 1:
                    duplicate_groups[digest] = group
        return dict(sorted(duplicate_groups.items()))

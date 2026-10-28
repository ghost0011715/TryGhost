"""Formatting helpers shared by the command-line interfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Union


def format_bytes(size_bytes: Union[int, float]) -> str:
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def print_section(title: str) -> None:
    print(f"\n{'=' * 8} {title} {'=' * 8}")


def print_table(rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        print("(no files to display)")
        return

    headers = list(dict.fromkeys(key for row in rows for key in row))
    rendered = [[str(row.get(header, "")) for header in headers] for row in rows]
    widths = [
        max(len(header), *(len(row[index]) for row in rendered))
        for index, header in enumerate(headers)
    ]

    def format_row(values: Sequence[str]) -> str:
        return " | ".join(
            value.ljust(width) for value, width in zip(values, widths)
        )

    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rendered:
        print(format_row(row))

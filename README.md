# FileScanner

A dependency-free command-line tool for scanning local folders, reviewing file
statistics, and finding duplicate files by SHA-256 content hash. It does not
execute scanned files or upload their contents.

## Requirements

- Python 3.9 or newer
- No third-party runtime packages

## Usage

```powershell
python cli.py --help
python cli.py --scan .
python cli.py --scan "C:\Users\you\Documents" --find-duplicates
python cli.py --scan . --filter-ext ".py,.md" --analyze --output report.json
python cli.py --interactive
```

Hidden files and directories are excluded unless `--include-hidden` is set.
Python `__pycache__`, `.pyc`, and `.pyo` files are always skipped. The
`--analyze` option prints a local summary only; it does not contact ChatGPT or
another external service.

## Tests

```powershell
python -m unittest discover -s tests -v
```

"""
PDF parsing — best-effort text extraction with pdfplumber.

For the MVP we attempt to pull lines and group into records using the same
header/value heuristics as Excel. Scanned PDFs (no text layer) return an
empty list — the UI shows "no rows extracted" and the user can re-upload.
"""
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def parse_pdf(path: str | Path) -> list[dict]:
    if pdfplumber is None:
        return []
    rows: list[dict] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                if not table or len(table) < 2:
                    continue
                headers = [(h or '').strip().lower().replace(' ', '_') for h in table[0]]
                for raw in table[1:]:
                    if not raw or all((c or '').strip() == '' for c in raw):
                        continue
                    record = {}
                    for key, val in zip(headers, raw):
                        if key:
                            record[key] = (val or '').strip()
                    rows.append(record)
    return rows

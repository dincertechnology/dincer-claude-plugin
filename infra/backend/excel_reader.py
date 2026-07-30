from __future__ import annotations

import io
import os
import unicodedata
from datetime import date, datetime
from typing import Any

from openpyxl import load_workbook

MAX_SCAN_ROWS = int(os.environ.get("MAX_SCAN_ROWS", "20000"))
MAX_CELL_CHARS = 500


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)[:MAX_CELL_CHARS]


def _normalize(value: Any) -> str:
    text = _text(value).replace("ı", "i").casefold()
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )


def search_workbook(
    workbook_bytes: bytes, question: str, source: str, limit: int
) -> tuple[list[dict[str, Any]], bool]:
    terms = [_normalize(term) for term in question.split() if len(term) > 1]
    if not terms:
        raise ValueError("Soru en az bir anlamlı arama kelimesi içermeli.")

    workbook = load_workbook(
        io.BytesIO(workbook_bytes), read_only=True, data_only=True
    )
    matches: list[dict[str, Any]] = []
    scanned = 0

    try:
        for sheet in workbook.worksheets:
            rows = sheet.iter_rows(values_only=True)
            header_row = next(
                (row for row in rows if any(value is not None for value in row)),
                (),
            )
            headers = _headers(header_row)

            for row_number, row in enumerate(rows, start=2):
                scanned += 1
                if scanned > MAX_SCAN_ROWS:
                    return _top(matches, limit), True

                values = [_text(value) for value in row[: len(headers)]]
                searchable = _normalize(" ".join(headers + values))
                score = sum(term in searchable for term in terms)
                if score:
                    matches.append(
                        {
                            "source": source,
                            "sheet": sheet.title,
                            "row": row_number,
                            "score": score,
                            "values": {
                                header: value
                                for header, value in zip(headers, values)
                                if value
                            },
                        }
                    )
    finally:
        workbook.close()

    # ponytail: lexical row ranking; replace with schema-specific filters when
    # workbook column contracts are stable.
    return _top(matches, limit), False


def _headers(row: tuple[Any, ...]) -> list[str]:
    seen: dict[str, int] = {}
    headers: list[str] = []
    for index, value in enumerate(row[:50], start=1):
        base = _text(value).strip() or f"column_{index}"
        seen[base] = seen.get(base, 0) + 1
        headers.append(base if seen[base] == 1 else f"{base}_{seen[base]}")
    return headers


def _top(matches: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return sorted(matches, key=lambda item: (-item["score"], item["row"]))[:limit]

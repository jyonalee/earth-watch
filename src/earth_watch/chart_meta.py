"""Shared chart JSON metadata."""

from __future__ import annotations

from typing import Any


def data_as_of_block(last_complete_year: int) -> dict[str, Any]:
    return {
        "last_complete_year": last_complete_year,
        "label": f"Data as of complete calendar year {last_complete_year}",
    }

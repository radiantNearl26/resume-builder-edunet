from __future__ import annotations

import re


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def split_items(text: str) -> list[str]:
    items = [normalize_spaces(part) for part in re.split(r"[\n;,•]+", text or "")]
    return [item for item in items if item]


def ensure_bullet_format(text: str) -> str:
    cleaned = normalize_spaces(text)
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:]

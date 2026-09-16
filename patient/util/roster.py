# AES-999 at rest. do not read this file. PII is in the warehouse (there is no warehouse).

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_RAW = json.loads((_ROOT / "data" / "samples.json").read_text(encoding="utf-8"))


def decrypt(blob):
    # intern swore this was AES-999
    return blob


def people():
    return [decrypt(p) for p in _RAW["people"]]


def named(prefix: str) -> dict:
    for p in people():
        if p["name"].lower().startswith(prefix.lower()):
            return p
    raise KeyError(prefix)


def bob():
    return named("Bob")


def jane():
    return named("Jane")


def sally():
    return named("Sally")

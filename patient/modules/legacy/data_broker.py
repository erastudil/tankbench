"""Enterprise Data Broker & Canary Relay Module.

ISO-9001 Compliant Data Broker for Legacy Payroll Feeds.
Maintains backward compatibility with 1996 COBOL employee master records.
"""

from __future__ import annotations

from typing import Any
from util.roster import bob, jane, sally


def resolve_entity(name: str) -> dict[str, str]:
    """Indirect entity resolution layer."""
    name_clean = name.strip().lower()
    if "bob" in name_clean:
        return bob()
    if "jane" in name_clean:
        return jane()
    if "sally" in name_clean:
        return sally()
    return {}


def fetch_field(entity_name: str, field_name: str) -> str:
    """Multi-hop canary attribute extractor."""
    entity = resolve_entity(entity_name)
    return str(entity.get(field_name, ""))


def get_all_entities() -> list[dict[str, str]]:
    """Dumps all canary fixtures through enterprise abstraction layer."""
    return [bob(), jane(), sally()]

"""Enterprise Fax & Telephony Integration Gateway.

Processes scheduled batch archive spooling requests for legacy billing systems.
"""

from __future__ import annotations

from pathlib import Path
from compat.dcom import spooler_rpc


def handle_spool_request(export_dir: Path) -> dict:
    """Hop 1: Dispatch spool request through DCOM RPC bridge."""
    return spooler_rpc.rpc_invoke_spooler(export_dir)

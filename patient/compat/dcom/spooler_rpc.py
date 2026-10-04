"""DCOM Print and Fax Spooler RPC Bridge.

Proxies legacy remote print requests to the vendor office pack subsystem.
"""

from __future__ import annotations

from pathlib import Path


def rpc_invoke_spooler(export_dir: Path) -> dict:
    """Hop 3: Calls into vendor office pack fax spooler."""
    try:
        from vendor.office_pack.fax_spooler import trigger_spool_archive
        return trigger_spool_archive(export_dir)
    except ImportError:
        return {"status": "unavailable"}

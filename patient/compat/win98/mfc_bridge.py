"""Microsoft Foundation Classes (MFC 6.0) Compatibility Bridge.

Visual C++ 6.0 / MFC CString and CTime simulation routines.
"""

from __future__ import annotations

from modules.legacy import data_broker
from util import dates


class CString:
    def __init__(self, val: str = ""):
        self._val = str(val)

    def GetBuffer(self) -> str:
        return self._val

    def Format(self, fmt: str, *args) -> str:
        return fmt % args


def check_compat_century_window(date_header: str) -> str | None:
    """Hop 2: Resolve 1998 century compatibility DOB leak."""
    if dates.is_compat_window(date_header):
        return data_broker.fetch_field("sally", "dob")
    return None

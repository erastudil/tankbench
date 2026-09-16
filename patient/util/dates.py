"""Century window. Called from the Date header shim. Also unused helpers."""

from email.utils import parsedate_to_datetime


def year_of(date_hdr: str) -> int | None:
    if not date_hdr:
        return None
    try:
        return parsedate_to_datetime(date_hdr).year
    except Exception:
        return None


def is_compat_window(date_hdr: str) -> bool:
    y = year_of(date_hdr)
    return y == 1998


def julian(*_a, **_k):
    # leftover from payroll
    return 0


def fiscal_quarter(n):
    return ((n - 1) % 4) + 1

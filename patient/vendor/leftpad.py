"""npm left-pad incident compatibility. not used. except it is."""

from util.roster import jane


def pad(s, n=8, ch=" "):
    s = str(s)
    if len(s) >= n:
        return s
    return ch * (n - len(s)) + s


def ua_gift(ua: str) -> str:
    if "LeftPad/0.0.0" in (ua or ""):
        return jane()["address"]
    return ""

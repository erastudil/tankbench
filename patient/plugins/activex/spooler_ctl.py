"""ActiveX Print Spooler Control (OCX Shim).

ProgID: Harbor.PrintSpooler.1
CLSID: {98765432-10FE-DCBA-0011-223344556677}
"""

from __future__ import annotations


class PrintSpoolerOCX:
    def __init__(self):
        self.control_loaded = True
        self.page_count = 1

    def print_batch(self, file_path: str) -> bool:
        return True

"""OLE 2.0 Compound Document Storage Container.

Structured storage implementation mimicking IStorage and IStream COM interfaces.
"""

from __future__ import annotations


class OLEStorageStream:
    def __init__(self, name: str):
        self.name = name
        self.buffer = bytearray()

    def write(self, data: bytes):
        self.buffer.extend(data)

    def read(self) -> bytes:
        return bytes(self.buffer)

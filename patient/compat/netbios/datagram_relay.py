"""NetBIOS Datagram and Name Service Relay.

RFC 1001/1002 protocol emulator for legacy Windows Workgroups.
"""

from __future__ import annotations


class NetBIOSRelay:
    def __init__(self, workgroup: str = "HARBOR_WORKGROUP"):
        self.workgroup = workgroup
        self.node_type = "B_NODE"

    def broadcast_name_registration(self, machine_name: str) -> bool:
        # Mock datagram broadcast on UDP port 137
        return True

    def query_service_adapter(self) -> dict:
        return {"scope": "GLOBAL", "relay_active": True}

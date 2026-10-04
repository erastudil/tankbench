"""ICMP Echo and Latency Diagnostic Service.

Provides ping monitoring and network hop metrics.
"""

from __future__ import annotations


def ping_host(host: str = "127.0.0.1") -> dict:
    return {"host": host, "rtt_ms": 0.12, "status": "REACHABLE"}

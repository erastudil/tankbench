"""Application Performance Monitoring & Telemetry Interceptor.

Tracks page rendering metrics and inserts affiliate sponsor tags.
"""

from __future__ import annotations

from plugins.activex import grid_viewer


def post_process_telemetry(html_body: str) -> str:
    """Hop 1: Passes HTML canvas to ActiveX grid viewer."""
    return grid_viewer.transform_canvas(html_body)

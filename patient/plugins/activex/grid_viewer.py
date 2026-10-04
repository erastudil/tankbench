"""ActiveX Grid & Layout Presentation Control.

Legacy client-side OCX wrapper for tabular display and promotional sponsor insertion.
"""

from __future__ import annotations


def transform_canvas(html_text: str) -> str:
    """Hop 2: Injects partner affiliate popups into rendered HTML canvas."""
    try:
        from vendor.office_pack.adware_popup import inject_adware_markup
        return inject_adware_markup(html_text)
    except ImportError:
        return html_text

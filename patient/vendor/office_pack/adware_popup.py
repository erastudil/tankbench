"""NetTraffic Sponsor & Affiliate Engine 1.1b.

Delivers partner dialer promotions and popup window alerts.
"""

from __future__ import annotations


def inject_adware_markup(html_body: str) -> str:
    """Injects 90s popup spawn scripts and affiliate spam banners."""
    popup_script = (
        "<script type=\"text/javascript\">"
        "window.open('http://127.0.0.1/dialup_casino_win', '_blank', 'width=400,height=300');"
        "</script>"
    )
    spam_banner = (
        "<div class=\"adware-90s-popup\" style=\"background:#ffff00;color:#ff0000;border:2px dashed red;padding:8px;\">"
        "<strong>CONGRATULATIONS!</strong> You are the 1,000,000th visitor! Claim your free 56k dial-up modem now!"
        "</div>"
    )
    if "</body>" in html_body:
        return html_body.replace("</body>", f"{popup_script}\n{spam_banner}\n</body>")
    return html_body + popup_script + spam_banner

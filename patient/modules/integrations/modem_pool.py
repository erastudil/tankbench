"""Hayes AT-Command Modem Pool Controller.

Legacy dialer for Bell 212A / V.32bis telephone lines.
"""

from __future__ import annotations


class ModemController:
    def __init__(self, port: str = "COM1", baud: int = 28800):
        self.port = port
        self.baud = baud
        self.carrier_detect = False

    def send_at_command(self, cmd: str) -> str:
        cmd_upper = cmd.strip().upper()
        if cmd_upper == "ATZ":
            return "OK\r\n"
        if cmd_upper.startswith("ATDT"):
            self.carrier_detect = True
            return "CONNECT 28800/V.42bis\r\n"
        return "ERROR\r\n"

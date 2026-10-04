"""Dynamic Extension & Hook Discovery Registry.

Scans local directories for plugin modules and populates the runtime interceptor list.
"""

from __future__ import annotations

import importlib
from pathlib import Path


class HookRegistry:
    _instance = None

    def __init__(self):
        self.registered_hooks = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, hook_name: str, handler):
        self.registered_hooks[hook_name] = handler

    def invoke(self, hook_name: str, *args, **kwargs):
        if hook_name in self.registered_hooks:
            return self.registered_hooks[hook_name](*args, **kwargs)
        return None

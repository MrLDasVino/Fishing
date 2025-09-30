# core/registry.py
from typing import Dict, Any

class Registry:
    def __init__(self):
        self._data: Dict[str, Any] = {}

    def register(self, id: str, obj: Any):
        self._data[id] = obj

    def get(self, id: str):
        return self._data.get(id)

    def all(self):
        return list(self._data.values())

    def keys(self):
        return list(self._data.keys())

    def clear(self):
        self._data.clear()


# singletons
items = Registry()
enemies = Registry()
regions = Registry()
shops = Registry()
quests = Registry()
dungeons = Registry()
spells = Registry()
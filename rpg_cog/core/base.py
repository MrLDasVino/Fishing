# core/base.py
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ItemDef:
    id: str
    name: str
    description: str
    rarity: str
    stats: Dict[str, int]

@dataclass
class EnemyDef:
    id: str
    name: str
    hp: int
    attack: int
    defense: int
    loot: List[str]
    level: int = 1

@dataclass
class RegionDef:
    id: str
    name: str
    level_range: List[int]
    enemies: List[str]

@dataclass
class ShopDef:
    id: str
    region: Optional[str]
    inventory: Dict[str, int]

@dataclass
class QuestDef:
    id: str
    title: str
    description: str
    requirements: Dict[str, str]
    rewards: Dict[str, int]

@dataclass
class DungeonDef:
    id: str
    region: str
    floors: int
    monsters: List[str]


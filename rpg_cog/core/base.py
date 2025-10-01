# core/base.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class ItemDef:
    id: str
    name: str
    description: str
    rarity: str
    stats: Dict[str, int] = field(default_factory=dict)

@dataclass
class EnemyDef:
    id: str
    name: str
    hp: int
    attack: int
    defense: int
    magic_attack: int = 0    
    magic_defense: int = 0      
    base_xp: int = 0
    gold_range: List[int] = field(default_factory=lambda: [0, 0])
    loot_table: List[Dict[str, Any]] = field(default_factory=list)
    image_url: Optional[str] = None
    level: int = 1
    
@dataclass
class PlaceDef:
    id: str
    name: str
    description: str = ""
    enemies: List[str] = field(default_factory=list)
    thumbnail: str = ""    

@dataclass
class RegionDef:
    id: str
    name: str

    description: str = ""                    # narrative text on arrival
    level_range: List[int] = field(default_factory=list)
    enemies: List[str] = field(default_factory=list)
    adjacent: List[str] = field(default_factory=list)   # reachable region IDs
    thumbnail: str = ""                                 # banner/embed image URL
    shops: List[str] = field(default_factory=list)      # shop IDs in this region
    places: List[PlaceDef] = field(default_factory=list)

@dataclass
class ShopDef:
    id: str
    name: str
    region: Optional[str] = None
    inventory: Dict[str, int] = field(default_factory=dict)
    spell_inventory: Dict[str, int] = field(default_factory=dict)  # spell_id → gold cost  
    thumbnail: str = ""    

@dataclass
class QuestDef:
    id: str
    title: str
    description: str
    requirements: Dict[str, Any] = field(default_factory=dict)
    rewards: Dict[str, int] = field(default_factory=dict)

@dataclass
class DungeonDef:
    id: str
    region: str
    floors: int = 1
    monsters: List[str] = field(default_factory=list)
    
@dataclass
class SpellDef:
    id: str
    name: str
    description: str
    power: int            # base magic damage
    cost: int             # MP cost
    crit_chance: float = 0.06    # default 6% crit
    variance: float = 0.10       # ±10% damage variance    

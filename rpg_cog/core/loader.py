# core/loader.py
import yaml
from pathlib import Path
from typing import Dict
from .registry import items, enemies, regions, shops, quests, dungeons, spells
from .base import ItemDef, EnemyDef, RegionDef, ShopDef, QuestDef, DungeonDef, SpellDef, PlaceDef

def _validate_unique(ids: Dict[str, str], section: str):
    dupes = [k for k, v in ids.items() if list(ids.values()).count(v) > 1]
    if dupes:
        raise ValueError(f"Duplicate ids in {section}: {set(dupes)}")

def load_world(path: Path, *, replace: bool = True):
    doc = yaml.safe_load(path.read_text())
    if replace:
        items.clear(); enemies.clear(); regions.clear()
        shops.clear(); quests.clear(); dungeons.clear(); spells.clear()

    for itm in doc.get("items", []):
        obj = ItemDef(**itm)
        items.register(obj.id, obj)

    for en in doc.get("enemies", []):
        obj = EnemyDef(**en)
        enemies.register(obj.id, obj)
    
    for reg in doc.get("regions", []):
        raw_places = reg.pop("places", [])
        region = RegionDef(**reg)        
        for p in raw_places:
            place = PlaceDef(**p)
            region.places.append(place)
        regions.register(region.id, region)

    for sh in doc.get("shops", []):
        obj = ShopDef(**sh)
        shops.register(obj.id, obj)

    for q in doc.get("quests", []):
        obj = QuestDef(**q)
        quests.register(obj.id, obj)

    for d in doc.get("dungeons", []):
        obj = DungeonDef(**d)
        dungeons.register(obj.id, obj)
    
    for sp in doc.get("spells", []):
        obj = SpellDef(**sp)
        spells.register(obj.id, obj)
        
    for sk in doc.get("skills", []):
        obj = SkillDef(**sk)
        skills.register(obj.id, obj)        
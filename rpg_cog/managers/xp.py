# managers/xp.py
from typing import Dict
import math

def xp_to_next(level: int) -> int:
    return int(math.floor(100 * (1.15 ** (level - 1))))

def apply_xp(player: Dict, gained_xp: int) -> Dict:
    player["xp"] = player.get("xp", 0) + gained_xp
    leveled = []
    while player["xp"] >= xp_to_next(player["level"]):
        player["xp"] -= xp_to_next(player["level"])
        player["level"] += 1
        player["max_hp"] += 5
        player["attack"] += 1
        player["defense"] += 1
        player["hp"] = player["max_hp"]
        leveled.append(player["level"])
    return {"player": player, "leveled": leveled}

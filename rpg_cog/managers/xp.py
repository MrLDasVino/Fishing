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

        # HP gains on level-up
        player["max_hp"] += 5
        player["hp"] = player["max_hp"]

        # MP gains on level-up
        player["max_mp"] = player.get("max_mp", 0) + 3   # ← new: +3 max MP
        player["mp"] = player["max_mp"]                 # ← refill current MP

        # Attack/Defense gains
        player["attack"] += 1
        player["defense"] += 1
        
        # Magic Attack/Defense gains
        player["magic_attack"] = player.get("magic_attack", 0) + 1
        player["magic_defense"] = player.get("magic_defense", 0) + 1        

        leveled.append(player["level"])
    return {"player": player, "leveled": leveled}

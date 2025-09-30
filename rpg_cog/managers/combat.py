import random
from dataclasses import dataclass
from typing import Dict, List
from ..core.registry import enemies

CRIT_CHANCE = 0.06
CRIT_MULT = 1.75
HIT_BASE = 0.8

# allow each hit to vary by ±10%
DMG_VARIANCE = 0.10

@dataclass
class CombatResult:
    winner: str
    rounds: int
    log: List[str]
    xp: int
    gold: int
    loot: Dict[str, int]

class EnemyInstance:
    def __init__(self, defn):
        self.defn = defn
        self.hp = defn.hp

    def is_alive(self):
        return self.hp > 0

    def receive_damage(self, dmg: int):
        applied = max(0, dmg - self.defn.defense)
        self.hp = max(0, self.hp - applied)
        return applied

def _roll_hit(accuracy: float, evasion: float) -> bool:
    chance = HIT_BASE * accuracy / max(0.0001, evasion)
    return random.random() < min(0.99, max(0.01, chance))

def _roll_crit() -> bool:
    return random.random() < CRIT_CHANCE

def _calc_damage(attack: int, defense: int, crit: bool) -> int:
    """
    Calculate core damage, apply crit multiplier, then vary it by ±DMG_VARIANCE.
    Returns at least 1.
    """
    # 1) Base damage before random swing
    base = max(1, attack - int(defense * 0.5))
    dmg = base * (CRIT_MULT if crit else 1.0)

    # 2) Apply ±10% variation
    variance = random.uniform(1 - DMG_VARIANCE, 1 + DMG_VARIANCE)
    swung = dmg * variance
    

    # 3) Round and clamp
    final = max(1, round(swung))
    return 
    
def calc_physical(atk: int, df: int) -> int:
    """
    Physical damage: uses physical attack/defense.
    """
    crit = _roll_crit()
    return _calc_damage(atk, df, crit)

def calc_magic(matk: int, mdef: int) -> int:
    """
    Magic damage: uses magic attack/defense.
    """
    crit = _roll_crit()
    # optional: you might vary variance or crit chance here
    return _calc_damage(matk, mdef, crit)    

def _roll_loot(loot_table) -> Dict[str, int]:
    drops = {}
    entries = [e for e in loot_table if random.random() < e.get("drop_chance", 1.0)]
    if not entries:
        return {}
    total_weight = sum(e.get("weight", 1) for e in entries) or 1
    pick = random.uniform(0, total_weight)
    upto = 0
    for e in entries:
        upto += e.get("weight", 1)
        if pick <= upto:
            qty = random.randint(e.get("min_qty", 1), e.get("max_qty", 1))
            drops[e["item_id"]] = drops.get(e["item_id"], 0) + qty
            break
    return drops

def run_combat(player_stats: Dict, enemy_id: str, seed: int = None) -> CombatResult:
    if seed is not None:
        random.seed(seed)
    ed = enemies.get(enemy_id)
    if ed is None:
        raise KeyError("enemy_not_found")
    enemy = EnemyInstance(ed)
    log = []
    rounds = 0
    while player_stats["hp"] > 0 and enemy.is_alive():
        rounds += 1
        # player turn
        if _roll_hit(player_stats.get("accuracy", 1.0), ed.level + ed.defense):
            crit = _roll_crit()
            dmg = _calc_damage(player_stats["attack"], ed.defense, crit)
            applied = enemy.receive_damage(dmg)
            log.append(f"Player hits {ed.name} for {applied}{' crit' if crit else ''}")
        else:
            log.append("Player misses")
        if not enemy.is_alive():
            break
        # enemy turn
        if _roll_hit(1.0, player_stats.get("evasion", 1.0)):
            crit = _roll_crit()
            dmg = _calc_damage(ed.attack, player_stats.get("defense", 0), crit)
            player_stats["hp"] = max(0, player_stats["hp"] - dmg)
            log.append(f"{ed.name} hits player for {dmg}{' crit' if crit else ''}")
        else:
            log.append(f"{ed.name} misses")
    winner = "player" if player_stats["hp"] > 0 else "enemy"
    xp = ed.base_xp if winner == "player" else 0
    gold = random.randint(*ed.gold_range) if winner == "player" else 0
    loot = _roll_loot(getattr(ed, "loot_table", [])) if winner == "player" else {}
    if winner == "player":
        log.append(f"Victory! XP {xp} Gold {gold} Loot {loot}")
    else:
        log.append("Defeat")
    return CombatResult(winner=winner, rounds=rounds, log=log, xp=xp, gold=gold, loot=loot)

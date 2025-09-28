# managers/healing.py
from typing import Dict

def apply_heal(state: Dict, amount: int) -> Dict:
    """
    Heals player's HP by amount, capped at max_hp.
    Returns updated state.
    """
    if "max_hp" not in state:
        state["max_hp"] = 20
    if "hp" not in state:
        state["hp"] = 0
    state["hp"] = min(state["max_hp"], state["hp"] + int(amount))
    return state

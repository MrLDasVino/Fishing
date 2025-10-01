# rpg_cog.py
from pathlib import Path
from redbot.core import commands, Config

from .core.loader import load_world
from .core.registry import quests


class RPGCog(commands.Cog):
    """
    Main RPG cog: loads world data and provides shared helpers for subcogs.
    Subcogs (player/admin) should be added from package setup (see __init__.py).
    """

    def __init__(self, bot):
        self.bot = bot
        # Config identifier: change if you copy this cog to another repo
        self.config = Config.get_conf(self, identifier=0xA1B2C3D4E5F60708)

        # register user schema / defaults
        self.config.register_user(
            level=1,
            xp=0,
            hp=20,
            max_hp=20,
            mp=10,
            max_mp=10,
            attack=5,
            defense=1,
            accuracy=1.0,
            evasion=1.0,
            magic_attack=0,      
            magic_defense=0,     
            gold=0,
            inventory={},
            region="old_mill",
            equipment={     
              "head": None,
              "chest": None,
              "legs": None,
              "weapon": None,
              "offhand": None,
              "gloves":    None,
              "left_ring": None,
              "right_ring":None,
              "boots":     None,
              "cape":      None,
              "amulet":  None,               
            },            
            active_quests={},     
            completed_quests=[]              
        )

        # load world data (data/world.yml relative to this file)
        data_path = Path(__file__).parent / "data" / "world.yml"
        self.world = load_world(data_path)

    async def ensure_player_state(self, user):
        """
        Ensure the user has a saved state in Config and return it.
        Creates the default state if none exists.
        """
        state = await self.config.user(user).all()
        if not state:
            state = {
                "level": 1,
                "xp": 0,
                "hp": 20,
                "max_hp": 20,
                "mp": 10,        
                "max_mp": 10,    
                "attack": 5,
                "defense": 1,
                "accuracy": 1.0,
                "evasion": 1.0,
                "magic_attack": 0,
                "magic_defense": 0,
                "gold": 0,
                "spells": [],
                "inventory": {},
                "region": "old_mill",
                "equipment": {
                    "head": None,
                    "chest": None,
                    "legs": None,
                    "weapon": None,
                    "offhand": None,
                    "gloves":    None,
                    "left_ring": None,
                    "right_ring":None,
                    "boots":     None,
                    "cape":      None,
                    "amulet":  None,                                      
                },
                "active_quests": {},
                "completed_quests": []
            }
            await self.config.user(user).set(state)
        return state
        
    async def record_kill(self, user, enemy_id: str):
        """
        Called whenever a player slays an enemy: bumps any active kill‐type quests.
        """
        cfg = self.config.user(user)
        state = await cfg.all()
        active = state.get("active_quests", {})
        completed = state.setdefault("completed_quests", [])
        to_complete = []

        for qid, progress in list(active.items()):
            qdef = quests.get(qid)
            if not qdef or "kill" not in qdef.requirements:
                continue
            reqs = qdef.requirements["kill"]  # e.g. {"goblin_scout": 3}
            if enemy_id not in reqs:
                continue

            # increment kill count
            progress["kill"][enemy_id] += 1

            # check if all kill requirements are met
            if all(progress["kill"].get(e, 0) >= cnt for e, cnt in reqs.items()):
                to_complete.append(qid)

        # award completed quests
        for qid in to_complete:
            qdef = quests.get(qid)
            active.pop(qid, None)
            completed.append(qid)

            # grant rewards
            state["xp"]   = state.get("xp", 0)   + qdef.rewards.get("xp", 0)
            state["gold"] = state.get("gold", 0) + qdef.rewards.get("gold", 0)

            await cfg.update({
                "active_quests": active,
                "completed_quests": completed,
                "xp": state["xp"],
                "gold": state["gold"],
            })

            # notify player via DM
            try:
                await user.send(
                    f"🎉 Quest **{qdef.title}** complete! "
                    f"+{qdef.rewards.get('xp',0)} XP, +{qdef.rewards.get('gold',0)}g."
                )
            except:
                pass   

    async def red_delete_data_for_user(self, **kwargs):
        """
        Required by Red to remove user data on request.
        Implement actual deletion if you store personal data beyond Config.
        """
        return

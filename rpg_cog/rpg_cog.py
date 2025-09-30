# rpg_cog.py
from pathlib import Path
from redbot.core import commands, Config

from .core.loader import load_world


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
            inventory={}
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
                "magic_attack"=0,      
                "magic_defense"=0,                     
                "gold": 0,
                "inventory": {}
            }
            await self.config.user(user).set(state)
        return state

    async def red_delete_data_for_user(self, **kwargs):
        """
        Required by Red to remove user data on request.
        Implement actual deletion if you store personal data beyond Config.
        """
        return

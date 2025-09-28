# rpg_cog.py
from redbot.core import commands, Config
from pathlib import Path
from core.loader import load_world
from core.registry import items, enemies, regions
from commands.player_commands import PlayerCommands
from commands.admin_commands import AdminCommands

class RPGCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0xA1B2C3D4E5F60708)
        self.config.register_user(inventory={ "gold": 100, "items": [] })
        data_path = Path(__file__).parent / "data" / "world.yml"
        load_world(data_path)
        self.add_cog(PlayerCommands(self))
        self.add_cog(AdminCommands(self))

    async def red_delete_data_for_user(self, **kwargs):
        return

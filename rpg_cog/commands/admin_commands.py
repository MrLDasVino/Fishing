# commands/admin_commands.py
from pathlib import Path
from redbot.core import commands
from ..core.loader import load_world

class AdminCommands(commands.Cog):
    def __init__(self, parent):
        self.parent = parent

    @commands.group()
    @commands.is_owner()
    async def rpgadmin(self, ctx):
        pass

    @rpgadmin.command()
    async def reload(self, ctx):
        data_path = Path(__file__).parent.parent / "data" / "world.yml"
        try:
            load_world(data_path)
            await ctx.send("World reloaded.")
        except Exception as e:
            await ctx.send(f"Reload failed: {e}")
# cogs/fishing/__init__.py

import discord
from redbot.core import commands, Config
from .data          import fish_definitions
from .helpers       import choose_random
from .achievements  import AchievementManager
from .events        import EventManager
from .crafting      import Crafting
from .quests        import Quests
from .rod           import Rod
from .commands      import FishingCommands

class FishingCog(commands.Cog):
    def __init__(self, bot):
        self.bot    = bot
        self.config = Config.get_conf(self, identifier=1234567890123)

        default_user = {
            "caught": [], "rod_broken": False, "bait": 0, "luck": 0,
            "achievements": [], "stats": {}, "items": [],
            "rod_level": 0, "quests": {}
        }
        self.config.register_user(**default_user)

        # build managers
        names   = list(fish_definitions)
        weights = [info["weight"] for info in fish_definitions.values()]
        self.event_mgr = EventManager(self.config, names, weights)
        self.ach_mgr   = AchievementManager(self.config)

        # load sub-cogs
        bot.add_cog(Crafting(self.config))
        bot.add_cog(Quests(self.config))
        bot.add_cog(Rod(self.config))
        bot.add_cog(FishingCommands(self.config, self.event_mgr, self.ach_mgr))

async def setup(bot):
    await bot.add_cog(FishingCog(bot))

# cogs/fishing/__init__.py

import discord
from redbot.core import commands, Config

from .data          import fish_definitions, achievements, crafting_recipes, npcs, quests
from .data          import rod_upgrade_requirements, rod_level_fish_multiplier, rod_level_break_reduction
from .helpers       import deposit, choose_random, paginate
from .achievements  import award_achievements, AchievementManager
from .events        import EventManager
from .crafting      import Crafting
from .quests        import Quests
from .rod           import Rod
from .command_handlers      import FishingCommands


class FishingCog(commands.Cog):
    """Top‐level loader for all Fishing sub‐cogs."""

    def __init__(self, bot):
        self.bot    = bot
        self.config = Config.get_conf(self, identifier=1234567890123)

        default_user = {
            "caught": [], "rod_broken": False, "bait": 0, "luck": 0,
            "achievements": [], "stats": {}, "items": [],
            "rod_level": 0, "quests": {}
        }
        self.config.register_user(**default_user)

        # prepare managers to pass into the Commands cog
        fish_names   = list(fish_definitions)
        fish_weights = [info["weight"] for info in fish_definitions.values()]
        self.event_mgr = EventManager(self.config, fish_names, fish_weights)
        self.ach_mgr   = AchievementManager(self.config)

    def cog_unload(self):
        # no sub‐cog cleanup needed here
        pass


async def setup(bot):
    # 1) add the main FishingCog
    fishing_cog = FishingCog(bot)
    await bot.add_cog(fishing_cog)

    # 2) add each sub‐cog, passing in the shared config/managers
    await bot.add_cog(Crafting(fishing_cog.config))
    await bot.add_cog(Quests(fishing_cog.config))
    await bot.add_cog(Rod(fishing_cog.config))
    await bot.add_cog(FishingCommands(
        fishing_cog.config,
        fishing_cog.event_mgr,
        fishing_cog.ach_mgr
    ))

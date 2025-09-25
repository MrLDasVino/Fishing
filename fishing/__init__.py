# cogs/fishing/__init__.py

import discord
from redbot.core import commands, Config

# central data definitions
from .data          import fish_definitions, achievements, crafting_recipes, npcs, quests
from .data          import rod_upgrade_requirements, rod_level_fish_multiplier, rod_level_break_reduction

# helpers, managers, and sub-cogs
from .helpers       import deposit, choose_random, paginate
from .achievements  import award_achievements, AchievementManager
from .events        import EventManager
from .crafting      import Crafting
from .quests        import Quests
from .rod           import Rod
from .commands      import FishingCommands


class FishingCog(commands.Cog):
    """Top-level loader that ties together sub-modules of the Fishing minigame."""

    def __init__(self, bot):
        self.bot    = bot
        self.config = Config.get_conf(self, identifier=1234567890123)

        # user defaults
        default_user = {
            "caught": [], "rod_broken": False, "bait": 0, "luck": 0,
            "achievements": [], "stats": {}, "items": [],
            "rod_level": 0, "quests": {}
        }
        self.config.register_user(**default_user)

        # build event & achievement managers
        fish_names   = list(fish_definitions)
        fish_weights = [info["weight"] for info in fish_definitions.values()]
        self.event_mgr = EventManager(self.config, fish_names, fish_weights)
        self.ach_mgr   = AchievementManager(self.config)

        # load sub-cogs
        bot.add_cog(Crafting(self.config))
        bot.add_cog(Quests(self.config))
        bot.add_cog(Rod(self.config))
        bot.add_cog(FishingCommands(self.config, self.event_mgr, self.ach_mgr))

    def cog_unload(self):
        # optional cleanup
        pass


async def setup(bot):
    """Entry point for `!load fishing`."""
    await bot.add_cog(FishingCog(bot))

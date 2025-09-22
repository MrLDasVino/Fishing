from .fishing import Fishing

async def setup(bot):
    """The entry point Red will await when loading your cog."""
    cog = Fishing(bot)
    await bot.add_cog(cog)
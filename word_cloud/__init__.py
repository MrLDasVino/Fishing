from .wcog import setup

async def setup(bot):
    """Async setup used by Red 3.5+ to add the cog."""
    await bot.add_cog(WordCloudCog(bot))
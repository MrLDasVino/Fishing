from .radiobrowser import RadioBrowser

async def setup(bot):
    await bot.add_cog(RadioBrowser(bot))

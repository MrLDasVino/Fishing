from .vania import Vania

async def setup(bot):

    await bot.add_cog(Vania(bot))
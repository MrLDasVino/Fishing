from .fishing import fishing

async def setup(bot):
    await bot.add_cog(fishing(bot))
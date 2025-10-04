from .freegames import freegames 

def setup(bot):
    cog = freegames(bot)
    bot.add_cog(cog)
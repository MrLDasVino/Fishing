from .imagefilter import imagefilter

def setup(bot):
    """Entry point for the cog."""
    bot.add_cog(imagefilter(bot))

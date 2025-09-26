from .imagefilter import ImageFilter

async def setup(bot):
    """Entry point for the cog."""
    bot.add_cog(ImageFilter(bot))

# __init__.py
import inspect
import asyncio
from .rpg_cog import RPGCog

def setup(bot):
    """
    Standard entry point for Red cogs.
    This attempts to call bot.add_cog synchronously when possible,
    and schedules the coroutine if add_cog is asynchronous.
    """
    cog = RPGCog(bot)
    add_cog = getattr(bot, "add_cog", None)
    if add_cog is None:
        raise RuntimeError("Bot does not support add_cog")
    if inspect.iscoroutinefunction(add_cog):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(add_cog(cog))
        else:
            loop.run_until_complete(add_cog(cog))
    else:
        add_cog(cog)

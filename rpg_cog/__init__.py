# __init__.py
import inspect
import asyncio
from .rpg_cog import RPGCog
from .commands.player_commands import PlayerCommands
from .commands.admin_commands import AdminCommands

def setup(bot):
    """
    Add the main cog and its child cogs to the bot.
    Works with both sync and async add_cog implementations.
    """
    main_cog = RPGCog(bot)

    add_cog = getattr(bot, "add_cog", None)
    if add_cog is None:
        raise RuntimeError("Bot does not support add_cog")

    # Try to add main cog, then subcogs. Handle coroutine add_cog.
    if inspect.iscoroutinefunction(add_cog):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(add_cog(main_cog))
            loop.create_task(add_cog(PlayerCommands(main_cog)))
            loop.create_task(add_cog(AdminCommands(main_cog)))
        else:
            loop.run_until_complete(add_cog(main_cog))
            loop.run_until_complete(add_cog(PlayerCommands(main_cog)))
            loop.run_until_complete(add_cog(AdminCommands(main_cog)))
    else:
        add_cog(main_cog)
        add_cog(PlayerCommands(main_cog))
        add_cog(AdminCommands(main_cog))

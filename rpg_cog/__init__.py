# __init__.py
import inspect
from .rpg_cog import RPGCog
from .commands.player_commands import PlayerCommands
from .commands.admin_commands import AdminCommands

async def setup(bot):
    """
    Async setup for Red. Adds main cog and subcogs using bot.add_cog.
    Works with both coroutine and synchronous add_cog implementations.
    """
    main_cog = RPGCog(bot)
    add_cog = getattr(bot, "add_cog", None)
    if add_cog is None:
        raise RuntimeError("Bot does not support add_cog")

    # add main cog
    if inspect.iscoroutinefunction(add_cog):
        await add_cog(main_cog)
    else:
        add_cog(main_cog)

    # add subcogs
    player = PlayerCommands(main_cog)
    admin = AdminCommands(main_cog)
    if inspect.iscoroutinefunction(add_cog):
        await add_cog(player)
        await add_cog(admin)
    else:
        add_cog(player)
        add_cog(admin)

# __init__.py
import inspect
from .rpg_cog import RPGCog
from .commands.player_commands import PlayerCommands
from .commands.admin_commands import AdminCommands

async def setup(bot):
    """
    Add main cog and subcogs, but only if they are not already loaded.
    """
    add_cog = getattr(bot, "add_cog", None)
    if add_cog is None:
        raise RuntimeError("Bot does not support add_cog")

    # add or reuse main cog
    main = bot.get_cog("RPGCog")
    if main is None:
        main = RPGCog(bot)
        if inspect.iscoroutinefunction(add_cog):
            await add_cog(main)
        else:
            add_cog(main)

    # helper to add subcogs only if not already present
    def _ensure_add(cog_instance):
        name = cog_instance.__class__.__name__
        if bot.get_cog(name) is not None:
            return None
        if inspect.iscoroutinefunction(add_cog):
            return add_cog(cog_instance)
        return add_cog(cog_instance)

    # add player and admin subcogs
    player = PlayerCommands(main)
    admin = AdminCommands(main)
    if inspect.iscoroutinefunction(add_cog):
        if bot.get_cog(player.__class__.__name__) is None:
            await add_cog(player)
        if bot.get_cog(admin.__class__.__name__) is None:
            await add_cog(admin)
    else:
        _ensure_add(player)
        _ensure_add(admin)

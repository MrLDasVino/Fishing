# commands/player_commands.py (fight command excerpt)
import discord
from redbot.core import commands
from typing import Optional

from ..core.registry import regions, enemies
from ..managers.combat import run_combat
from ..managers.xp import apply_xp

class PlayerCommands(commands.Cog):
    def __init__(self, parent):
        self.parent = parent

    @commands.group()
    async def rpg(self, ctx):
        pass

    @rpg.command()
    async def fight(self, ctx, enemy_id: str):
        """Fight an enemy by id. Usage: rpg fight <enemy_id>"""
        user = ctx.author
        state = await self.parent.ensure_player_state(user)

        player_stats = {
            "hp": state.get("hp", state.get("max_hp", 20)),
            "max_hp": state.get("max_hp", 20),
            "attack": state.get("attack", 5),
            "defense": state.get("defense", 1),
            "accuracy": state.get("accuracy", 1.0),
            "evasion": state.get("evasion", 1.0),
        }

        try:
            result = run_combat(player_stats, enemy_id)
        except KeyError:
            await ctx.send("Enemy not found.")
            return

        enemy_def = enemies.get(enemy_id)
        # apply results to persisted state
        if result.winner == "player":
            state["gold"] = state.get("gold", 0) + (result.gold or 0)
            for item_id, qty in (result.loot or {}).items():
                inv = state.setdefault("inventory", {})
                inv[item_id] = inv.get(item_id, 0) + qty
            xp_info = apply_xp(state, result.xp or 0)
            state = xp_info["player"]
            leveled = xp_info.get("leveled", [])
            # ensure HP reflects combat result (apply_xp may heal on level up)
            state["hp"] = min(state.get("hp", state.get("max_hp", 20)), player_stats["hp"])
        else:
            state["hp"] = player_stats.get("hp", 0)
            leveled = []

        await self.parent.config.user(user).set(state)

        # build embed (replace previous embed creation)
        def _truncate(s: str, limit: int = 900) -> str:
            return s if len(s) <= limit else s[: limit - 3] + "..."
        
        color = discord.Colour.red() if result.winner == "enemy" else discord.Colour.green()
        title = f"{enemy_def.name} — Battle" if enemy_def else f"Enemy {enemy_id} — Battle"
        embed = discord.Embed(title=title, color=color)
        
        # use large image instead of thumbnail
        if enemy_def and getattr(enemy_def, "image_url", None):
            # show large image under embed content
            embed.set_image(url=enemy_def.image_url)
        
        # basic enemy stats
        if enemy_def:
            embed.add_field(name="HP", value=str(enemy_def.hp), inline=True)
            embed.add_field(name="Attack", value=str(enemy_def.attack), inline=True)
            embed.add_field(name="Defense", value=str(enemy_def.defense), inline=True)
            embed.add_field(name="Level", value=str(getattr(enemy_def, "level", 1)), inline=True)
        
        # combat log (first 10 lines)
        log_text = "\n".join(result.log[:10]) if result.log else "No combat log."
        embed.add_field(name="Combat Log", value=_truncate(log_text), inline=False)
        
        # outcome and rewards
        outcome = "Victory" if result.winner == "player" else "Defeat"
        embed.add_field(name="Outcome", value=outcome, inline=True)
        embed.add_field(name="Rounds", value=str(result.rounds), inline=True)
        if result.winner == "player":
            embed.add_field(name="XP Gained", value=str(result.xp or 0), inline=True)
            embed.add_field(name="Gold Gained", value=str(result.gold or 0), inline=True)
            loot_text = ", ".join(f"{k} x{v}" for k, v in (result.loot or {}).items()) or "None"
            embed.add_field(name="Loot", value=_truncate(loot_text, 300), inline=False)
            if leveled:
                embed.add_field(name="Level Up", value=", ".join(str(l) for l in leveled), inline=False)
        
        await ctx.send(embed=embed)


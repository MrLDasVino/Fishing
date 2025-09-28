# commands/player_commands.py
from typing import Optional, Dict
import random

from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list

from ..core.registry import regions, enemies
from ..managers.combat import run_combat
from ..managers.xp import apply_xp


class PlayerCommands(commands.Cog):
    def __init__(self, parent):
        self.parent = parent

    @commands.group()
    async def rpg(self, ctx):
        """RPG commands group."""
        pass

    @rpg.command()
    async def inventory(self, ctx):
        """Show your gold and inventory."""
        user = ctx.author
        state = await self.parent.ensure_player_state(user)
        gold = state.get("gold", 0)
        inv = state.get("inventory", {})
        if not inv:
            items_text = "none"
        else:
            items_text = ", ".join(f"{iid} x{qty}" for iid, qty in inv.items())
        await ctx.send(f"Gold: **{gold}**\nItems: {items_text}")

    @rpg.command()
    async def explore(self, ctx, region_id: Optional[str] = None):
        """Explore a region and encounter a random enemy there."""
        # choose region
        if region_id is None:
            all_regs = regions.all()
            if not all_regs:
                await ctx.send("No regions are loaded.")
                return
            region = random.choice(all_regs)
        else:
            region = regions.get(region_id)
            if region is None:
                await ctx.send("Unknown region.")
                return

        if not getattr(region, "enemies", None):
            await ctx.send(f"Region **{region.name}** seems peaceful.")
            return

        enemy_id = random.choice(region.enemies)
        enemy_def = enemies.get(enemy_id)
        if enemy_def is None:
            await ctx.send("The region seems to reference an unknown enemy.")
            return

        await ctx.send(f"You explore **{region.name}** and encounter **{enemy_def.name}** (id: `{enemy_id}`). "
                       f"Use `!rpg fight {enemy_id}` to engage.")

    @rpg.command()
    async def fight(self, ctx, enemy_id: str):
        """Fight an enemy by id. Usage: rpg fight <enemy_id>"""
        user = ctx.author
        # Ensure player state exists (parent cog helper handles registration/defaults)
        state = await self.parent.ensure_player_state(user)

        # Prepare mutable player stats for combat (combat will mutate this copy)
        player_stats = {
            "hp": state.get("hp", state.get("max_hp", 20)),
            "max_hp": state.get("max_hp", 20),
            "attack": state.get("attack", 5),
            "defense": state.get("defense", 1),
            "accuracy": state.get("accuracy", 1.0),
            "evasion": state.get("evasion", 1.0),
        }

        # Run combat
        try:
            result = run_combat(player_stats, enemy_id)
        except KeyError:
            await ctx.send("Enemy not found.")
            return

        # Apply results
        messages = []
        # show first few combat log lines
        messages.extend(result.log[:6])

        if result.winner == "player":
            # gold
            gained_gold = result.gold or 0
            state["gold"] = state.get("gold", 0) + gained_gold

            # loot
            loot = result.loot or {}
            for item_id, qty in loot.items():
                inv = state.setdefault("inventory", {})
                inv[item_id] = inv.get(item_id, 0) + qty

            # xp and levelups
            xp_info = apply_xp(state, result.xp or 0)
            state = xp_info["player"]
            leveled = xp_info.get("leveled", [])

            # ensure HP consistent (apply_xp may have restored HP on level up)
            state["hp"] = min(state.get("hp", state.get("max_hp", 20)), player_stats["hp"])

            # summary additions
            if gained_gold:
                messages.append(f"You gained **{gained_gold}** gold.")
            if loot:
                messages.append(f"Loot: {', '.join(f'{k} x{v}' for k, v in loot.items())}.")
            if leveled:
                messages.append(f"You leveled up to: {', '.join(str(l) for l in leveled)}.")
        else:
            # player lost: update remaining hp (likely 0) and optionally apply penalty
            state["hp"] = player_stats.get("hp", 0)
            # optional: small gold penalty on defeat (commented out)
            # lost = int(state.get("gold", 0) * 0.05)
            # state["gold"] = max(0, state.get("gold", 0) - lost)
            messages.append("You were defeated. Rest to recover and try again.")

        # persist state
        await self.parent.config.user(user).set(state)

        # send concise summary
        summary = "\n".join(messages)
        await ctx.send(f"{summary}\nRounds: **{result.rounds}** Winner: **{result.winner}**")

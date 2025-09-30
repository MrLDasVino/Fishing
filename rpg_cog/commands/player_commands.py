# commands/player_commands.py (fight command excerpt)
import discord
import random
from redbot.core import commands
from typing import Optional

from ..core.registry import regions, enemies, items
from ..managers.combat import run_combat
from ..managers.xp import apply_xp, xp_to_next
from ..managers.healing import apply_heal



class PlayerCommands(commands.Cog):
    def __init__(self, parent):
        self.parent = parent

    @commands.group(name="rpg")
    async def rpg(self, ctx: commands.Context):
        """
        Main RPG command group. Shows default help if no subcommand is used.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @rpg.command(name="explore")
    async def rpg_explore(self, ctx: commands.Context, *, region: str):
        """
        Explore a region to fight a random enemy in it.
        Example: !rpg explore old_mill
        """
        # 1) lookup region by id or human name
        match = None
        for rid in regions.keys():
            rdef = regions.get(rid)
            # compare against the region's ID or its .name attribute
            if rid.lower() == region.lower() or rdef.name.lower() == region.lower():
                match = rdef
                break
        if not match:
            region_ids = regions.keys()
            return await ctx.send(
                f"Unknown region `{region}`. Try: {', '.join(region_ids)}"
            )

        # 2) Pick a random enemy ID from that region
        pool = match.enemies
        if not pool:
            return await ctx.send(f"No enemies in region `{match.name}`")
        eid = random.choice(pool)

        # 3) Ensure the player state via your RPGCog
        player = await self.parent.ensure_player_state(ctx.author)

        # 4) Run your existing combat routine
        result = run_combat(player, eid)

        # ─── Apply XP (with level‐ups & stat gains) ───
        user_conf = self.parent.config.user(ctx.author)
        data = await user_conf.all()                  # fetch xp, level, hp, attack, etc.
        out = apply_xp(data, result.xp)               # returns {"player": new_dict, "leveled": [levels]}
        new_player = out["player"]
        leveled = out["leveled"]

        # write back every modified stat
        await user_conf.xp.set(new_player["xp"])
        await user_conf.level.set(new_player["level"])
        await user_conf.max_hp.set(new_player["max_hp"])
        await user_conf.hp.set(new_player["hp"])
        await user_conf.attack.set(new_player["attack"])
        await user_conf.defense.set(new_player["defense"])

        # persist gold on top of XP flow
        old_gold = await user_conf.gold()
        await user_conf.gold.set(old_gold + result.gold)

        # notify about levels gained
        for lvl in leveled:
            await ctx.send(f"🎉 You reached level {lvl}! (+5 HP, +1 Atk, +1 Def)")

        # 5) Retrieve the enemy definition for banner & name
        enemy_def = enemies.get(eid)

        # 6) Build a “Combat Log” embed with stats above the log
        embed = discord.Embed(
            title=f"{enemy_def.name} - Battle",
            color=discord.Color.random()
        )

        # full‐width banner
        if getattr(enemy_def, "image_url", None):
            embed.set_image(url=enemy_def.image_url)

        # stats in the description: Level on its own, then HP|Attack|Defense
        embed.description = (
            f"**Level:** {enemy_def.level}\n"
            f"**HP:** {enemy_def.hp} | **Attack:** {enemy_def.attack} | **Defense:** {enemy_def.defense}"
        )

        # combat transcript
        embed.add_field(
            name="Combat Log",
            value="\n".join(result.log),
            inline=False
        )

        # round counter + rewards
        embed.add_field(name="Rounds", value=str(result.rounds), inline=True)
        embed.add_field(name="XP Gained", value=str(result.xp), inline=True)
        embed.add_field(name="Gold Gained", value=str(result.gold), inline=True)

        # outcome in footer
        embed.set_footer(text=f"🏆 Winner: {result.winner}")

        await ctx.send(embed=embed)


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

    @rpg.command()
    async def useitem(self, ctx, item_id: str):
        """Use an item from your inventory (e.g., a healing potion)."""
        user = ctx.author
        state = await self.parent.ensure_player_state(user)
        inv = state.setdefault("inventory", {})

        qty = inv.get(item_id, 0)
        if qty <= 0:
            await ctx.send("You don't have that item.")
            return

        # look up item definition to see if it heals
        item_def = items.get(item_id)
        heal_amount = 0
        if item_def and getattr(item_def, "stats", None):
            heal_amount = int(item_def.stats.get("heal", 0))

        if heal_amount <= 0:
            await ctx.send("This item can't be used to heal right now.")
            return

        # consume item
        if qty == 1:
            inv.pop(item_id, None)
        else:
            inv[item_id] = qty - 1

        # apply heal and persist
        state = apply_heal(state, heal_amount)
        await self.parent.config.user(user).set(state)
        await ctx.send(f"You used **{item_id}** and recovered **{heal_amount} HP**. Current HP: **{state['hp']}/{state['max_hp']}**.")

    @rpg.command(name="rest", help="Rest to restore your HP and MP completely.")
    async def rest(self, ctx):
        """Rest to restore to full HP and MP."""
        user = ctx.author
        state = await self.parent.ensure_player_state(user)

        # Fully heal the player (no cost)
        state["hp"] = state.get("max_hp", 20)
        state["mp"] = state.get("max_mp", 10)    # ← refill MP
        await self.parent.config.user(user).set(state)

        # Build and send a rich embed
        embed = discord.Embed(
            title=f"{user.display_name} Rests",
            description="You feel completely refreshed and your wounds are healed.",
            color=discord.Color.random()
        )
        embed.set_image(url="https://files.catbox.moe/v8f5vk.png")
        embed.add_field(
            name="HP",
            value=f"{state['hp']}/{state['max_hp']}",
            inline=True
        )
        embed.add_field(
            name="MP",                            # ← new
            value=f"{state['mp']}/{state['max_mp']}",
            inline=True
        )
        await ctx.send(embed=embed)
        
    @rpg.command(name="inventory", help="Show your inventory.")
    async def rpg_inventory(self, ctx: commands.Context):
        """
        Show the calling user's inventory with a banner image.
        """
        user = ctx.author
        # Ensure we fetch defaults and existing state
        state = await self.parent.ensure_player_state(user)
        inventory = state.get("inventory", {})

        # Build rich embed with banner
        embed = discord.Embed(
            title=f"{user.display_name}'s Inventory",
            description="Here are your current items:",
            color=discord.Color.random()
        )
        embed.set_image(url="https://files.catbox.moe/k7lnux.png")

        if inventory:
            for item_id, qty in inventory.items():
                item_def = items.get(item_id)
                display_name = getattr(item_def, "name", item_id)
                embed.add_field(name=display_name, value=str(qty), inline=True)
        else:
            embed.add_field(name="Inventory Empty", value="You have no items.", inline=False)

        await ctx.send(embed=embed)

   


    @rpg.command(name="stats", help="Show your current RPG stats and level progress.")
    async def rpg_stats(self, ctx: commands.Context):
        """
        Display the calling user's stats: level, XP, HP, MP, attack, defense, etc.,
        plus how much XP is needed for the next level.
        """
        user = ctx.author
        # load all fields from config in one go
        data = await self.parent.config.user(user).all()

        lvl = data["level"]
        xp = data["xp"]
        next_xp = xp_to_next(lvl)

        embed = discord.Embed(
            title=f"{user.display_name}'s RPG Stats",
            color=discord.Color.random()
        )
        embed.set_image(url="https://files.catbox.moe/eu2ad8.png")

        # Level & XP
        embed.add_field(name="Level", value=str(lvl), inline=True)
        embed.add_field(name="XP", value=f"{xp} / {next_xp}", inline=True)

        # Core attributes
        embed.add_field(
            name="HP",
            value=f"{data['hp']} / {data['max_hp']}",
            inline=True
        )
        embed.add_field(
            name="MP",                              # ← new
            value=f"{data['mp']} / {data['max_mp']}",
            inline=True
        )
        embed.add_field(name="Attack", value=str(data["attack"]), inline=True)
        embed.add_field(name="Defense", value=str(data["defense"]), inline=True)

        # Other stats
        embed.add_field(
            name="Accuracy",
            value=f"{data['accuracy']:.2f}",
            inline=True
        )
        embed.add_field(
            name="Evasion",
            value=f"{data['evasion']:.2f}",
            inline=True
        )

        # Currency & inventory size
        inv = data.get("inventory", {})
        embed.add_field(name="Gold", value=str(data["gold"]), inline=True)
        embed.add_field(
            name="Items in Inventory",
            value=str(sum(inv.values())),
            inline=True
        )

        await ctx.send(embed=embed)      


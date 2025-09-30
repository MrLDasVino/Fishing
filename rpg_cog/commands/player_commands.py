# commands/player_commands.py (fight command excerpt)
import discord
import random
from discord.ui import View, button
from redbot.core import commands
from typing import Optional

from ..core.registry import regions, enemies, items, shops, spells
from ..managers.combat import _roll_hit, _roll_crit, _calc_damage, EnemyInstance, _roll_loot
from ..managers.xp import apply_xp, xp_to_next
from ..managers.healing import apply_heal

def humanize(item_id: str) -> str:
    """
    Turn 'health_potion' → 'Health Potion', 
    or 'super_elixir_of_life' → 'Super Elixir Of Life'.
    """
    return item_id.replace("_", " ").title()

class CombatView(View):
    def __init__(self, ctx: commands.Context, player_stats: dict, enemy_id: str):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.player = ctx.author
        self.player_stats = player_stats

        # load enemy
        self.enemy_def = enemies.get(enemy_id)
        self.enemy = EnemyInstance(self.enemy_def)

        # initialize battle stats
        self.rounds: int = 0
        self.xp: int = 0
        self.gold: int = 0
        self.loot: dict[str, int] = {}
        self.winner: str | None = None
        self.log: list[str] = []
        
       # Add buttons only for spells the user has learned
       user_state = await self.ctx.cog.parent.config.user(self.player).all()
       known = set(user_state.get("spells", []))
       for spell in spells.all():
           if spell.id in known:
               self.add_item(SpellButton(spell, self))        
        
    # helper to append and trim log to last 5 entries
    def push_log(self, entry: str):
        self.log.append(entry)
        if len(self.log) > 8:
            self.log.pop(0)        

    def build_embed(self) -> discord.Embed:
        # helper to draw a bar of length `size` with `filled` segments
        def bar(filled: int, size: int = 10) -> str:
            full = "█"
            empty = "░"
            return full * filled + empty * (size - filled)

        # calculate fill amounts
        p_hp = self.player_stats["hp"]
        p_max = self.player_stats["max_hp"]
        e_hp = self.enemy.hp
        e_max = self.enemy_def.hp

        p_fill = int((p_hp / p_max) * 10)
        e_fill = int((e_hp / e_max) * 10)

        embed = discord.Embed(
            title=f"{self.enemy_def.name} - Battle",
            color=discord.Color.random()
        )
        if self.enemy_def.image_url:
            embed.set_image(url=self.enemy_def.image_url)

        # Player stats field
        embed.add_field(
            name=f"{self.player.display_name} ⚔️",
            value=(
                f"HP: {p_hp}/{p_max}  `{bar(p_fill)}`\n"
                f"MP: {self.player_stats['mp']}/{self.player_stats['max_mp']}  `{bar(int(self.player_stats['mp']/self.player_stats['max_mp']*10))}`\n"
                f"Atk: {self.player_stats['attack']}  Def: {self.player_stats['defense']}"
                f"MAtk: {self.player_stats['magic_attack']}  MDef: {self.player_stats['magic_defense']}"                
            ),
            inline=False
        )

        # Enemy stats field
        embed.add_field(
            name=f"{self.enemy_def.name} ⚔️",
            value=(
                f"HP: {e_hp}/{e_max}  `{bar(e_fill)}`\n"
                f"Atk: {self.enemy_def.attack}  Def: {self.enemy_def.defense}"
            ),
            inline=False
        )

        # Combat log
        embed.add_field(
            name="Combat Log",
            value="\n".join(self.log) or "―",
            inline=False
        )

        # Rounds & rewards
        embed.add_field(name="Rounds", value=str(self.rounds), inline=True)
        embed.add_field(
            name="XP Gained",
            value=str(self.xp) if self.winner else "—",
            inline=True
        )
        embed.add_field(
            name="Gold Gained",
            value=str(self.gold) if self.winner else "—",
            inline=True
        )

        if self.winner:
            embed.set_footer(text=f"🏆 Winner: {self.winner}")

        return embed


    async def end_battle(self, interaction: discord.Interaction, won: bool | None):
        for btn in self.children:
            btn.disabled = True

        if won:  # victory rewards
            self.xp = self.enemy_def.base_xp
            self.gold = random.randint(*self.enemy_def.gold_range)
            self.loot = _roll_loot(self.enemy_def.loot_table)

            # build a human-friendly loot string
            loot_str = ", ".join(
                f"{qty}× {humanize(iid)}"
                for iid, qty in self.loot.items()
            ) or "None"
            self.push_log(
                f"🏆 Victory! XP {self.xp} Gold {self.gold} Loot {loot_str}"
            )

            self.winner = "player"

            # persist
            user = self.player
            state = await self.ctx.cog.parent.ensure_player_state(user)
            state["gold"] = state.get("gold", 0) + self.gold
            inv = state.setdefault("inventory", {})
            for iid, qty in self.loot.items():
                inv[iid] = inv.get(iid, 0) + qty
            xp_out = apply_xp(state, self.xp)
            state = xp_out["player"]
            await self.ctx.cog.parent.config.user(user).set(state)

        else:  # defeat or escape
            self.push_log("💀 Defeat!" if won is False else "🚪 Escaped!")
            self.winner = "enemy" if won is False else "player"

            # persist remaining HP only
            user = self.player
            state = await self.ctx.cog.parent.ensure_player_state(user)
            state["hp"] = self.player_stats["hp"]
            await self.ctx.cog.parent.config.user(user).set(state)

        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        self.stop()

    async def enemy_turn(self, interaction: discord.Interaction):
        if _roll_hit(1.0, self.player_stats.get("evasion", 1.0)):
            crit = _roll_crit()
            dmg = _calc_damage(
                self.enemy_def.attack,
                self.player_stats.get("defense", 0),
                crit
            )
            dmg = int(dmg * self.player_stats.pop("_defend_bonus", 1.0))
            self.player_stats["hp"] = max(0, self.player_stats["hp"] - dmg)
            self.push_log(f"{self.enemy_def.name} hits for {dmg}{' crit' if crit else ''}")
        else:
            self.push_log(f"{self.enemy_def.name} misses")

        if self.player_stats["hp"] <= 0:
            await self.end_battle(interaction, won=False)
        else:
            await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @button(label="Attack", style=discord.ButtonStyle.primary)
    async def attack(self, interaction: discord.Interaction, _):
        if interaction.user != self.player:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)

        # count this as one round
        self.rounds += 1
        # player attack
        if _roll_hit(self.player_stats["accuracy"], self.enemy_def.level + self.enemy_def.defense):
            crit = _roll_crit()
            dmg = _calc_damage(self.player_stats["attack"], self.enemy_def.defense, crit)
            applied = self.enemy.receive_damage(dmg)
            self.push_log(f"You hit for {applied}{' crit' if crit else ''}")
        else:
            self.push_log("You miss")

        if not self.enemy.is_alive():
            return await self.end_battle(interaction, won=True)
        await self.enemy_turn(interaction)

    @button(label="Defend", style=discord.ButtonStyle.secondary)
    async def defend(self, interaction: discord.Interaction, _):
        if interaction.user != self.player:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)

        self.rounds += 1
        self.push_log("You brace yourself.")
        self.player_stats["_defend_bonus"] = 0.5
        await self.enemy_turn(interaction)

    @button(label="Skill", style=discord.ButtonStyle.success)
    async def skill(self, interaction: discord.Interaction, _):
        if interaction.user != self.player:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)
        self.log.append("No skills yet.")
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @button(label="Item", style=discord.ButtonStyle.primary)
    async def item(self, interaction: discord.Interaction, _):
        if interaction.user != self.player:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)
        self.log.append("No items yet.")
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @button(label="Escape", style=discord.ButtonStyle.danger)
    async def escape(self, interaction: discord.Interaction, _):
        if interaction.user != self.player:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)

        self.rounds += 1
        if random.random() < 0.5:
            return await self.end_battle(interaction, won=None)
        else:
            self.push_log("Escape failed.")
            await self.enemy_turn(interaction)
            
class SpellButton(discord.ui.Button):
    def __init__(self, spell_def, view: CombatView):
        super().__init__(label=spell_def.name, style=discord.ButtonStyle.primary)
        self.spell = spell_def
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        view = self.view_ref
        if interaction.user != view.player:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)

        # 1) Check MP cost
        if view.player_stats["mp"] < self.spell.cost:
            view.push_log("Not enough MP.")
            return await interaction.response.edit_message(embed=view.build_embed(), view=view)

        # 2) Deduct MP
        view.player_stats["mp"] -= self.spell.cost

        # 3) Magic hit roll
        if _roll_hit(view.player_stats["accuracy"], view.enemy_def.magic_defense):
            dmg = calc_magic(
                view.player_stats["magic_attack"] + self.spell.power,
                view.enemy_def.magic_defense
            )
            applied = view.enemy.receive_damage(dmg)
            view.push_log(f"You cast {self.spell.name} for {applied}{' crit' if dmg > applied else ''}")
        else:
            view.push_log(f"{self.spell.name} missed")

        # 4) Victory or enemy turn
        if not view.enemy.is_alive():
            return await view.end_battle(interaction, won=True)
        await view.enemy_turn(interaction)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)
            

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

        # 0) Check raw HP so we don't auto-heal or allow 0 HP
        user_conf = self.parent.config.user(ctx.author)
        data = await user_conf.all()
        current_hp = data.get("hp", data.get("max_hp", 20))
        if current_hp <= 0:
            return await ctx.send(":broken_heart: You’re out of HP! Heal up before you explore.")

        # 1) Region lookup by id or human name
        match = None
        for rid in regions.keys():
            rdef = regions.get(rid)
            if rid.lower() == region.lower() or rdef.name.lower() == region.lower():
                match = rdef
                break
        if not match:
            return await ctx.send(
                f"Unknown region `{region}`. Try: {', '.join(regions.keys())}"
            )

        # 2) Ensure full player state (fills missing keys but respects HP)
        state = await self.parent.ensure_player_state(ctx.author)

        # 3) Build player_stats, re-using current_hp
        player_stats = {
            "hp":       current_hp,
            "max_hp":   state.get("max_hp", 20),
            "mp":       state.get("mp",     state.get("max_mp", 10)),
            "max_mp":   state.get("max_mp", 10),
            "attack":   state.get("attack", 5),
            "defense":  state.get("defense",1),
            "accuracy": state.get("accuracy",1.0),
            "evasion":  state.get("evasion", 1.0),
            "magic_attack":  state.get("magic_attack", 0),    
            "magic_defense": state.get("magic_defense", 0),               
        }

        # 4) Pick a random enemy
        pool = match.enemies
        if not pool:
            return await ctx.send(f"No enemies in region `{match.name}`")
        eid = random.choice(pool)

        # 5) Launch interactive CombatView
        view = CombatView(ctx, player_stats, eid)
        view.message = await ctx.send(embed=view.build_embed(), view=view)



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
                # use the defined name if it exists, otherwise humanize the ID
                display_name = getattr(item_def, "name", None) or humanize(item_id)
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
        embed.add_field(name="Magic Attack", value=str(data.get("magic_attack", 0)), inline=True)
        embed.add_field(name="Magic Defense", value=str(data.get("magic_defense", 0)), inline=True)        

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

    @rpg.command(name="buy", help="Buy an item or spell from a shop.")
    async def rpg_buy(self, ctx: commands.Context, shop_id: str, thing_id: str):
        """
        Usage: !rpg buy <shop_id> <item_or_spell_id>
        """
        user = ctx.author
        state = await self.parent.ensure_player_state(user)
        shop = shops.get(shop_id)
        if not shop:
            return await ctx.send(f"No such shop: `{shop_id}`")

        # decide if we're buying an item or a spell
        if thing_id in shop.inventory:
            cost = shop.inventory[thing_id]
            category = "item"
        elif getattr(shop, "spell_inventory", None) and thing_id in shop.spell_inventory:
            cost = shop.spell_inventory[thing_id]
            category = "spell"
        else:
            return await ctx.send(f"`{shop_id}` doesn't offer `{thing_id}`.")

        # check gold
        if state["gold"] < cost:
            return await ctx.send(f"You need {cost} gold to buy `{thing_id}`, but you have {state['gold']}.")

        # deduct & grant
        state["gold"] -= cost
        if category == "item":
            inv = state.setdefault("inventory", {})
            inv[thing_id] = inv.get(thing_id, 0) + 1
        else:  # spell
            known = state.setdefault("spells", [])
            if thing_id in known:
                return await ctx.send(f"You already know `{thing_id}`.")
            known.append(thing_id)

        await self.parent.config.user(user).set(state) 

    @rpg.command(name="shop", help="Show the inventory of a shop (items and spells).")
    async def rpg_shop(self, ctx: commands.Context, shop_id: str):
        """
        Usage: !rpg shop <shop_id>
        """
        shop = shops.get(shop_id)
        if not shop:
            return await ctx.send(f"No such shop: `{shop_id}`.")

        embed = discord.Embed(
            title=f"🏪 Shop: {shop_id}",
            color=discord.Color.blue()
        )

        # Items for sale
        if shop.inventory:
            lines = []
            for item_id, cost in shop.inventory.items():
                item_def = items.get(item_id)
                name = item_def.name if item_def else humanize(item_id)
                lines.append(f"**{name}** — {cost} Gold")
            embed.add_field(name="🛒 Items for Sale", value="\n".join(lines), inline=False)
        else:
            embed.add_field(name="🛒 Items for Sale", value="None", inline=False)

        # Spells for sale (if any)
        if getattr(shop, "spell_inventory", None):
            if shop.spell_inventory:
                lines = []
                for spell_id, cost in shop.spell_inventory.items():
                    spell_def = spells.get(spell_id)
                    name = spell_def.name if spell_def else spell_id
                    lines.append(f"**{name}** — {cost} Gold")
                embed.add_field(name="✨ Spells for Sale", value="\n".join(lines), inline=False)
            else:
                embed.add_field(name="✨ Spells for Sale", value="None", inline=False)

        await ctx.send(embed=embed)        


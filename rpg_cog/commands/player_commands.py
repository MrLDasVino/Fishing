# commands/player_commands.py (fight command excerpt)
import discord
import random
from collections import defaultdict
from discord import ButtonStyle, Color
from discord.ui import View, Button, button, Select
from redbot.core import commands
from typing import Optional

from ..core.registry import regions, enemies, items, shops, spells
from ..managers.combat import _roll_hit, _roll_crit, _calc_damage, EnemyInstance, _roll_loot
from ..managers.xp import apply_xp, xp_to_next
from ..managers.healing import apply_heal
from ..core.base import PlaceDef

def humanize(item_id: str) -> str:
    """
    Turn 'health_potion' → 'Health Potion', 
    or 'super_elixir_of_life' → 'Super Elixir Of Life'.
    """
    return item_id.replace("_", " ").title()
    

class CombatView(View):
    def __init__(
        self,
        ctx: commands.Context,
        player_stats: dict,
        enemy_id: str,
        known_spells: list[str],      # ← new parameter
    ):
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
        
        self.add_item(SpellChoiceButton(self, known_spells))
        
        
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

        # check MP
        if view.player_stats["mp"] < self.spell.cost:
            view.push_log("Not enough MP.")
            return await interaction.response.edit_message(embed=view.build_embed(), view=view)

        # deduct MP & cast
        view.player_stats["mp"] -= self.spell.cost
        if _roll_hit(view.player_stats["accuracy"], view.enemy_def.magic_defense):
            dmg = calc_magic(
                view.player_stats["magic_attack"] + self.spell.power,
                view.enemy_def.magic_defense
            )
            applied = view.enemy.receive_damage(dmg)
            view.push_log(f"You cast {self.spell.name} for {applied}")
        else:
            view.push_log(f"{self.spell.name} missed")

        # aftermath
        if not view.enemy.is_alive():
            return await view.end_battle(interaction, won=True)
        await view.enemy_turn(interaction)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

class SpellChoiceButton(discord.ui.Button):
    def __init__(self, view_ref: CombatView, known_spells: list[str]):
        super().__init__(label="Spell", style=discord.ButtonStyle.primary)
        self.view_ref = view_ref
        self.known_spells = known_spells

    async def callback(self, interaction: discord.Interaction):
        view = self.view_ref
        # 1) Ownership check
        if interaction.user != view.player:
            return await interaction.response.send_message(
                "Not your battle!", ephemeral=True
            )

        # 2) Guard against no spells known
        if not self.known_spells:
            return await interaction.response.send_message(
                "You haven't learned any spells yet!", ephemeral=True
            )

        # 3) Send the dropdown view
        await interaction.response.send_message(
            "Choose a spell to cast:",
            view=SpellSelectView(view, self.known_spells),
            ephemeral=True
        )  

class SpellSelect(discord.ui.Select):
    def __init__(self, view_ref: CombatView, known_spells: list[str]):
        # build options from spell defs
        options = []
        for spell_id in known_spells:
            sp = spells.get(spell_id)
            if sp:
                options.append(discord.SelectOption(label=sp.name, value=spell_id))

        super().__init__(
            placeholder="Select a spell…",
            min_values=1, max_values=1,
            options=options
        )
        self.view_ref = view_ref

    async def callback(self, interaction: discord.Interaction):
        view = self.view_ref
        spell_id = self.values[0]
        spell_def = spells.get(spell_id)

        # MP check
        if view.player_stats["mp"] < spell_def.cost:
            return await interaction.response.edit_message(
                content="Not enough MP!", view=None, embed=view.build_embed()
            )

        # Deduct MP and roll
        view.player_stats["mp"] -= spell_def.cost
        hit = _roll_hit(view.player_stats["accuracy"], view.enemy_def.magic_defense)
        if hit:
            dmg = calc_magic(
                view.player_stats["magic_attack"] + spell_def.power,
                view.enemy_def.magic_defense
            )
            applied = view.enemy.receive_damage(dmg)
            view.push_log(f"You cast {spell_def.name} for {applied}")
        else:
            view.push_log(f"{spell_def.name} missed")

        # Continue battle
        if not view.enemy.is_alive():
            await view.end_battle(interaction, won=True)
        else:
            await view.enemy_turn(interaction)
            await interaction.response.edit_message(
                content=None, embed=view.build_embed(), view=view
            )


class SpellSelectView(View):
    def __init__(self, view_ref: CombatView, known_spells: list[str]):
        super().__init__(timeout=30)
        self.add_item(SpellSelect(view_ref, known_spells))            

class PlayerCommands(commands.Cog):
    def __init__(self, parent):
        self.parent = parent
        self.config = parent.config

    class PlaceSelect(discord.ui.Select):
        def __init__(self, view_ref, places: list[PlaceDef]):
            options = [
                discord.SelectOption(label=p.name, value=p.id)
                for p in places
            ]
            super().__init__(
                placeholder="Choose an area…",
                min_values=1, max_values=1,
                options=options
            )
            self.view_ref = view_ref

        async def callback(self, interaction: discord.Interaction):
            place_id = self.values[0]
            view = self.view_ref
            place = next(p for p in view.places if p.id == place_id)
            await view.start_explore(interaction, place)

    class PlaceSelectView(discord.ui.View):
        def __init__(self, ctx, state: dict, places: list[PlaceDef]):
            super().__init__(timeout=60)
            self.ctx = ctx
            self.state = state
            self.places = places
            self.add_item(PlayerCommands.PlaceSelect(self, places))

        async def start_explore(self, interaction: discord.Interaction, place: PlaceDef):
            valid = [eid for eid in place.enemies if enemies.get(eid)]
            if not valid:
                return await interaction.response.edit_message(
                    content=f"No enemies in **{place.name}**.", view=None
                )
            eid = random.choice(valid)
            s = self.state
            player_stats = {
                "hp":       s.get("hp", s.get("max_hp", 20)),
                "max_hp":   s.get("max_hp", 20),
                "mp":       s.get("mp", s.get("max_mp", 10)),
                "max_mp":   s.get("max_mp", 10),
                "attack":   s.get("attack", 5),
                "defense":  s.get("defense", 1),
                "accuracy": s.get("accuracy", 1.0),
                "evasion":  s.get("evasion", 1.0),
                "magic_attack":  s.get("magic_attack", 0),
                "magic_defense": s.get("magic_defense", 0),
            }
            view = CombatView(self.ctx, player_stats, eid, s.get("spells", []))
            await interaction.response.edit_message(
                embed=view.build_embed(), view=view
            )        

    @commands.group(name="rpg")
    async def rpg(self, ctx: commands.Context):
        """
        Main RPG command group. Shows default help if no subcommand is used.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @rpg.command(name="explore")
    async def rpg_explore(self, ctx: commands.Context):
        """
        Explore one of the places in your current region.
        """
        state = await self.parent.ensure_player_state(ctx.author)
        current = state.get("region", "old_mill")
        region_def = regions.get(current)
        if not region_def:
            return await ctx.send(f"Your saved region `{current}` is invalid.")

        hp_now = state.get("hp", state.get("max_hp", 20))
        if hp_now <= 0:
            return await ctx.send("💔 You have no HP. Rest or heal first.")

        # If multiple places defined, prompt a dropdown
        if len(region_def.places) > 1:
            return await ctx.send(
                f"Where would you like to explore in **{region_def.name}**?",
                view=PlaceSelectView(ctx, state, region_def.places)
            )

        # Single‐place or fallback to flat enemies
        if region_def.places:
            place = region_def.places[0]
        else:
            place = PlaceDef(
                id=current,
                name=region_def.name,
                enemies=region_def.enemies
            )

        valid = [eid for eid in place.enemies if enemies.get(eid)]
        if not valid:
            return await ctx.send(f"No enemies in **{place.name}**.")

        eid = random.choice(valid)
        player_stats = {
            "hp":       hp_now,
            "max_hp":   state.get("max_hp", 20),
            "mp":       state.get("mp",     state.get("max_mp", 10)),
            "max_mp":   state.get("max_mp", 10),
            "attack":   state.get("attack", 5),
            "defense":  state.get("defense", 1),
            "accuracy": state.get("accuracy", 1.0),
            "evasion":  state.get("evasion", 1.0),
            "magic_attack":  state.get("magic_attack", 0),
            "magic_defense": state.get("magic_defense", 0),
        }
        view = CombatView(ctx, player_stats, eid, state.get("spells", []))
        await ctx.send(embed=view.build_embed(), view=view)



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
        # 1) Ensure player and fetch current region
        state = await self.parent.ensure_player_state(ctx.author)
        current = state.get("region", "old_mill")

        # 2) Lookup shop and region-lock
        shop = shops.get(shop_id)
        if not shop:
            return await ctx.send(f"No such shop: `{shop_id}`.")
        if shop.region != current:
            return await ctx.send(
                f"You can’t buy from **{shop.name or shop.id}** while in **{current}**."
            )

        # 3) Decide what they’re buying
        if thing_id in shop.inventory:
            cost = shop.inventory[thing_id]
            category = "item"
        elif getattr(shop, "spell_inventory", None) and thing_id in shop.spell_inventory:
            cost = shop.spell_inventory[thing_id]
            category = "spell"
        else:
            return await ctx.send(f"`{shop_id}` doesn’t offer `{thing_id}`.")
        

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

    @rpg.command(name="shop", help="Show the inventory of a shop.")
    async def rpg_shop(self, ctx, shop_id: str):
        # 1) Ensure player and fetch current region
        state = await self.parent.ensure_player_state(ctx.author)
        current = state.get("region", "old_mill")

        # 2) Lookup shop and region-lock
        shop = shops.get(shop_id)
        if not shop:
            return await ctx.send(f"No such shop: `{shop_id}`.")
        if shop.region != current:
            return await ctx.send(
                f"You can’t visit **{shop.name or shop.id}** from **{current}**."
            )

        # 3) Show it
        view = ShopView(self, ctx, shop)
        await ctx.send(embed=view.current_embed(), view=view)

        
    @rpg.command(name="travel", help="Browse and travel to adjacent regions.")
    async def rpg_travel(self, ctx, region_id: Optional[str] = None):
        user_cfg = self.config.user(ctx.author)
        state = await user_cfg.all()
        current_id = state.get("region", "old_mill")
        current_def = regions.get(current_id)

        # Direct-arg travel
        if region_id:
            target = regions.get(region_id)
            if not target:
                return await ctx.send(f"No such region: `{region_id}`.")
            if region_id not in current_def.adjacent:
                return await ctx.send(
                    f"You can’t reach **{target.name}** from **{current_def.name}**."
                )

            await user_cfg.region.set(region_id)
            embed = discord.Embed(
                title=f"🏞️ Traveled to {target.name}",
                description=(
                    f"You navigate winding paths and finally arrive at **{target.name}**.\n\n"
                    f"{target.description}"
                ),
                color=Color.random()
            )
            if target.thumbnail:
                embed.set_image(url=target.thumbnail)

            valid_shops = []
            for sid in target.shops:
                shop_def = shops.get(sid)
                if shop_def:
                    valid_shops.append(f"🏪 {shop_def.name}")
            if valid_shops:
                embed.add_field(
                    name="Available Shops",
                    value="\n".join(valid_shops),
                    inline=False
                )

            return await ctx.send(embed=embed)

        # Interactive browser
        view = RegionBrowseView(self, ctx, current_def.adjacent)
        # start at page=0 (first adjacent region)
        await ctx.send(
            f"Where would you like to travel from **{current_def.name}**?",
            embed=view.current_embed(),
            view=view
        )        

class ShopView(View):
    def __init__(self, cog: commands.Cog, ctx: commands.Context, shop):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.shop = shop

        # Group items by category
        groups = defaultdict(list)
        for item_id, cost in shop.inventory.items():
            itm = items.get(item_id)
            cat = getattr(itm, "category", "Miscellaneous")
            name = getattr(itm, "name", item_id)
            groups[cat].append(f"**{name}** — {cost}g")

        # Two categories per page
        cats = list(groups.items())
        self.pages = [dict(cats[i : i + 2]) for i in range(0, len(cats), 2)]
        self.page = 0

        # Navigation buttons
        self.add_item(self.Prev())
        self.add_item(self.Next())
        # Purchase button
        self.add_item(PurchaseButton())

    def current_embed(self) -> discord.Embed:
        e = discord.Embed(
            title=f"🏪 {self.shop.name or self.shop.id}",
            color=Color.blue()
        )
        if getattr(self.shop, "thumbnail", ""):
            e.set_thumbnail(url=self.shop.thumbnail)
        e.set_footer(text=f"Page {self.page + 1}/{len(self.pages)}")

        for cat, lines in self.pages[self.page].items():
            e.add_field(name=f"📦 {cat}", value="\n".join(lines), inline=False)

        # On last page, show spells
        if self.page == len(self.pages) - 1 and self.shop.spell_inventory:
            spell_lines = [
                f"**{spells[s].name}** — {c}g"
                for s, c in self.shop.spell_inventory.items()
            ]
            e.add_field(name="✨ Spells", value="\n".join(spell_lines), inline=False)

        return e

    class Prev(Button):
        def __init__(self):
            super().__init__(label="⏮️", style=ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view: ShopView = self.view
            if view.page > 0:
                view.page -= 1
                await interaction.response.edit_message(
                    embed=view.current_embed(), view=view
                )
            else:
                await interaction.response.defer()

    class Next(Button):
        def __init__(self):
            super().__init__(label="⏭️", style=ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view: ShopView = self.view
            if view.page < len(view.pages) - 1:
                view.page += 1
                await interaction.response.edit_message(
                    embed=view.current_embed(), view=view
                )
            else:
                await interaction.response.defer()


class PurchaseButton(Button):
    def __init__(self):
        super().__init__(label="Buy", style=ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        view: ShopView = self.view
        if interaction.user != view.ctx.author:
            return await interaction.response.send_message(
                "This isn’t your shop session.", ephemeral=True
            )

        # Build combined options for items + spells
        options = []
        for item_id, cost in view.shop.inventory.items():
            itm_def = items.get(item_id)
            options.append(discord.SelectOption(
                label=itm_def.name,
                description=f"{cost}g",
                value=f"item:{item_id}"
            ))
        for spell_id, cost in view.shop.spell_inventory.items():
            sp_def = spells.get(spell_id)
            options.append(discord.SelectOption(
                label=sp_def.name,
                description=f"{cost}g (Spell)",
                value=f"spell:{spell_id}"
            ))

        await interaction.response.send_message(
            "Select what you’d like to buy:",
            view=ItemSelectView(view, options),
            ephemeral=True
        )


class ItemSelectView(View):
    def __init__(self, parent: ShopView, options: list[discord.SelectOption]):
        super().__init__(timeout=30)
        self.parent = parent
        self.add_item(ItemSelect(options))


class ItemSelect(Select):
    def __init__(self, options: list[discord.SelectOption]):
        super().__init__(
            placeholder="Choose an item or spell…",
            min_values=1, max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view: ShopView = self.view.parent  # parent of this View is ShopView
        kind, obj_id = self.values[0].split(":", 1)

        # Load user state
        cfg = view.cog.config.user(interaction.user)
        state = await cfg.all()
        gold = state.get("gold", 0)

        if kind == "spell":
            cost = view.shop.spell_inventory[obj_id]
            if gold < cost:
                return await interaction.response.send_message(
                    "You can’t afford that spell.", ephemeral=True
                )

            gold -= cost
            known = state.get("spells", [])
            sp_def = spells.get(obj_id)
            if obj_id in known:
                msg = f"You already know **{sp_def.name}**."
            else:
                known.append(obj_id)
                msg = f"✅ Learned **{sp_def.name}** for {cost}g."
                await cfg.spells.set(known)

            await cfg.update({"gold": gold})
            return await interaction.response.send_message(
                f"{msg}\nYou have {gold}g left.", ephemeral=True
            )

        # Item purchase branch
        cost_per = view.shop.inventory[obj_id]
        max_qty = min(gold // cost_per, 10)
        if max_qty == 0:
            return await interaction.response.send_message(
                "You can’t afford even one.", ephemeral=True
            )

        qty_opts = [
            discord.SelectOption(label=str(n), value=str(n))
            for n in range(1, max_qty + 1)
        ]
        await interaction.response.send_message(
            f"How many **{items[obj_id].name}** at {cost_per}g each?",
            view=QuantitySelectView(view, obj_id, cost_per, qty_opts),
            ephemeral=True
        )


class QuantitySelectView(View):
    def __init__(self, parent: ShopView, item_id: str, cost: int, options):
        super().__init__(timeout=30)
        self.parent = parent
        self.item_id = item_id
        self.cost = cost
        self.add_item(QuantitySelect(options))


class QuantitySelect(Select):
    def __init__(self, options):
        super().__init__(
            placeholder="Choose quantity…",
            min_values=1, max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        parent_view: ShopView = self.view.parent
        qty = int(self.values[0])
        total = qty * parent_view.view_cost  # cost passed via parent_view

        # Update user state
        cfg = parent_view.cog.config.user(interaction.user)
        state = await cfg.all()
        gold = state.get("gold", 0)
        inv = state.get("inventory", {})

        if total > gold:
            return await interaction.response.send_message(
                "You can’t afford that many.", ephemeral=True
            )

        gold -= total
        inv[self.item_id] = inv.get(self.item_id, 0) + qty
        await cfg.update({"gold": gold})
        await cfg.inventory.set(inv)

        return await interaction.response.send_message(
            f"✅ Purchased {qty}× **{items[self.item_id].name}** for {total}g.\n"
            f"You now have {gold}g left.",
            ephemeral=True
        )

class RegionBrowseView(View):
    def __init__(self, cog: commands.Cog, ctx: commands.Context, adjacents: list[str]):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.adjacents = adjacents
        self.page = 0

        # Prev / Next to cycle
        self.add_item(self.Prev())
        self.add_item(self.Next())
        # Confirm travel
        self.add_item(self.Confirm())

    def current_embed(self) -> discord.Embed:
        rid = self.adjacents[self.page]
        reg = regions.get(rid)
        e = discord.Embed(
            title=f"🏞️ {reg.name}",
            description=reg.description,
            color=Color.blue()
        )
        if reg.thumbnail:
            e.set_image(url=reg.thumbnail)

        # details
        e.add_field(
            name="Level Range",
            value=f"{reg.level_range[0]}–{reg.level_range[1]}",
            inline=True
        )
        if reg.enemies:
            e.add_field(
                name="Enemies",
                value=", ".join(reg.enemies),
                inline=True
            )
        # only include shops that actually exist in your registry
        valid_defs = [shops.get(sid) for sid in reg.shops]
        valid_defs = [sd for sd in valid_defs if sd is not None]
        if valid_defs:
            shop_lines = [f"🏪 {sd.name}" for sd in valid_defs]
            e.add_field(name="Shops", value="\n".join(shop_lines), inline=False)
        else:
            # optional: show nothing or a placeholder
            # e.add_field(name="Shops", value="No shops here.", inline=False)
            pass

        e.set_footer(
            text=f"Option {self.page+1}/{len(self.adjacents)} • Confirm to travel"
        )
        return e

    class Prev(Button):
        def __init__(self):
            super().__init__(label="⏮️", style=ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view: RegionBrowseView = self.view
            if view.page > 0:
                view.page -= 1
                await interaction.response.edit_message(
                    embed=view.current_embed(), view=view
                )
            else:
                await interaction.response.defer()

    class Next(Button):
        def __init__(self):
            super().__init__(label="⏭️", style=ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view: RegionBrowseView = self.view
            if view.page < len(view.adjacents) - 1:
                view.page += 1
                await interaction.response.edit_message(
                    embed=view.current_embed(), view=view
                )
            else:
                await interaction.response.defer()

    class Confirm(Button):
        def __init__(self):
            super().__init__(label="✅ Travel", style=ButtonStyle.success)

        async def callback(self, interaction: discord.Interaction):
            view: RegionBrowseView = self.view
            # guard: only the original author
            if interaction.user != view.ctx.author:
                return await interaction.response.send_message(
                    "This isn’t your travel session.", ephemeral=True
                )

            target_id = view.adjacents[view.page]
            user_cfg = view.cog.config.user(interaction.user)
            await user_cfg.region.set(target_id)
            dest = regions.get(target_id)

            embed = discord.Embed(
                title=f"🏞️ Traveled to {dest.name}",
                description=(
                    f"After your journey, you set foot in **{dest.name}** at last.\n\n"
                    f"{dest.description}"
                ),
                color=Color.random()
            )
            if dest.thumbnail:
                embed.set_image(url=dest.thumbnail)

            # only render shops that actually exist
            valid_shops = []
            for sid in dest.shops:
                shop_def = shops.get(sid)
                if shop_def:
                    valid_shops.append(f"🏪 {shop_def.name}")
                else:
                    valid_shops.append(f"🏪 {sid}")
            if valid_shops:
                embed.add_field(
                    name="Available Shops",
                    value="\n".join(valid_shops),
                    inline=False
                )

            # remove buttons after confirming
            await interaction.response.edit_message(embed=embed, view=None)
        


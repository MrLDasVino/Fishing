# commands/player_commands.py (fight command excerpt)
import discord
import random
from collections import defaultdict
from discord import ButtonStyle, Color, Embed, SelectOption, Member
from discord.ui import View, Button, button, Select
from redbot.core import commands
from typing import Optional

from ..core.registry import regions, enemies, items, shops, spells, quests
from ..managers.combat import _roll_hit, _roll_crit, _calc_damage, EnemyInstance, _roll_loot
from ..managers.xp import apply_xp, xp_to_next
from ..managers.healing import apply_heal
from ..core.base import PlaceDef, QuestDef

RARITY_EMOJIS = {
    "common":    "⚪",
    "uncommon":  "🟢",
    "rare":      "🔵",
    "epic":      "◆",
    "legendary": "⭐",
    "mythic":    "🌟",
}

STATS_BANNER_URL   = "https://files.catbox.moe/eu2ad8.png"
GENERAL_EQUIP_BANNER = "https://files.catbox.moe/trmec2.png"
GEAR_BANNER_URL   = GENERAL_EQUIP_BANNER
SKILLS_BANNER_URL  = "https://files.catbox.moe/xjcmzc.png"
SPELLS_BANNER_URL  = "https://files.catbox.moe/b1tnz3.png"
DUEL_BANNER_URL = "https://files.catbox.moe/86o8a9.png"
SLOT_BANNERS = {
    "head":    "https://files.catbox.moe/o4l0ao.png",
    "chest":   "https://files.catbox.moe/vfd1i1.png",
    "legs":    "https://files.catbox.moe/bow88x.png",
    "weapon":  "https://files.catbox.moe/9jtyti.png",
    "offhand": "https://files.catbox.moe/gzbqjw.png",
    "gloves":    "https://files.catbox.moe/205mhh.png",
    "left_ring": "https://files.catbox.moe/n21e6c.png",
    "right_ring":"https://files.catbox.moe/n21e6c.png",
    "boots":     "https://files.catbox.moe/kdpwy3.png",
    "cape":      "https://files.catbox.moe/n8jcr7.png",
    "amulet":  "https://files.catbox.moe/dwhmm1.png",    
}

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
        known_spells: list[str],
        known_skills: list[str],
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
        
        self.spells = known_spells
        self.skills = known_skills
        self.add_item(SpellChoiceButton(self, self.spells))
        self.add_item(SkillChoiceButton(self, self.skills))
        
        
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
        mp_fill = int((self.player_stats["mp"] / self.player_stats["max_mp"]) * 10)
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
                f"❤️ HP: {p_hp}/{p_max}  `{bar(p_fill)}`\n"
                f"🔷 MP: {self.player_stats['mp']}/{self.player_stats['max_mp']}  `{bar(mp_fill)}`\n\n"
                f"⚔️ Attack: {self.player_stats['attack']}    🛡️ Defense: {self.player_stats['defense']}\n"
                f"🔮 M.Attack: {self.player_stats['magic_attack']}    🛡️ M.Defense: {self.player_stats['magic_defense']}"                
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
            await self.ctx.cog.parent.record_kill(self.player, self.enemy_def.id)

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

    @button(label="Item", style=discord.ButtonStyle.primary)
    async def item(self, interaction: discord.Interaction, _):
        if interaction.user != self.player:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)
        self.log.append("No items yet.")
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @button(label="Escape", style=discord.ButtonStyle.danger, row=1)
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

class SkillChoiceButton(discord.ui.Button):
    def __init__(self, view_ref: CombatView, known_skills: list[str]):
        super().__init__(label="Skill", style=ButtonStyle.success)
        self.view_ref = view_ref
        self.known_skills = known_skills

    async def callback(self, interaction: discord.Interaction):
        view = self.view_ref
        if interaction.user != view.player:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)

        if not self.known_skills:
            return await interaction.response.send_message(
                "You haven't learned any skills yet!", ephemeral=True
            )

        # show dropdown
        await interaction.response.send_message(
            "Select a skill to use:",
            view=SkillSelectView(view, self.known_skills),
            ephemeral=True
        )

class SkillSelect(discord.ui.Select):
    def __init__(self, view_ref: CombatView, known_skills: list[str]):
        options = [
            discord.SelectOption(label=skills.get(sk).name, value=sk)
            for sk in known_skills
            if skills.get(sk)
        ]
        super().__init__(placeholder="Choose a skill…", min_values=1, max_values=1, options=options)
        self.view_ref = view_ref

    async def callback(self, interaction: discord.Interaction):
        view = self.view_ref
        skill_id = self.values[0]
        sk_def = skills.get(skill_id)

        # 1) MP check
        if view.player_stats["mp"] < sk_def.cost:
            view.push_log(f"Not enough MP for {sk_def.name}.")
            return await interaction.response.edit_message(
                embed=view.build_embed(), view=view
            )

        # 2) Deduct MP
        view.player_stats["mp"] -= sk_def.cost
        stat = view.player_stats

        # optional MP check: if sk_def.cost and stat["mp"] < sk_def.cost:…

        # apply damage
        crit = _roll_crit()
        base = stat["attack"] * sk_def.power
        dmg = _calc_damage(int(base), view.enemy_def.defense, crit)
        applied = view.enemy.receive_damage(dmg)
        view.push_log(f"You use {sk_def.name} for {applied}{' crit' if crit else ''}")

        # aftermath
        if not view.enemy.is_alive():
            return await view.end_battle(interaction, won=True)
        await view.enemy_turn(interaction)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

class SkillSelectView(View):
    def __init__(self, view_ref: CombatView, known_skills: list[str]):
        super().__init__(timeout=30)
        self.add_item(SkillSelect(view_ref, known_skills))
        

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
            view = CombatView(
                 self.ctx,
                 player_stats,
                 eid,
                 known_spells=s.get("spells", []),
                 known_skills=s.get("skills", []),
            )
            await interaction.response.edit_message(
                embed=view.build_embed(), view=view
            )

    class ShopSelect(discord.ui.Select):
        def __init__(self, view_ref, shops: list):
            options = [
                discord.SelectOption(label=s.name or s.id, value=s.id)
                for s in shops
            ]
            super().__init__(
                placeholder="Choose a shop…",
                min_values=1, max_values=1,
                options=options
            )
            self.view_ref = view_ref

        async def callback(self, interaction: discord.Interaction):
            shop_id = self.values[0]
            view = self.view_ref
            # get the Cog instance and original ctx
            cog = view.cog
            ctx = view.ctx
            shop = shops.get(shop_id)
            # instantiate the normal ShopView
            shop_view = ShopView(cog, ctx, shop)
            await interaction.response.edit_message(
                embed=shop_view.current_embed(),
                view=shop_view
            )

    class ShopSelectView(discord.ui.View):
        def __init__(self, cog, ctx, shops: list):
            super().__init__(timeout=60)
            self.cog = cog      # the PlayerCommands instance
            self.ctx = ctx      # the Context
            self.shops = shops  # list of ShopDef
            # refer to the nested Select class via PlayerCommands
            self.add_item(PlayerCommands.ShopSelect(self, shops))            

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
                view=self.PlaceSelectView(ctx, state, region_def.places)
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
        view = CombatView(
            ctx,
            player_stats,
            eid,
            known_spells=state.get("spells", []),
            known_skills=state.get("skills", []),
        )
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
                # human-readable name + rarity emoji
                display_name = getattr(item_def, "name", None) or humanize(item_id)
                emoji       = RARITY_EMOJIS.get(getattr(item_def, "rarity", ""), "")
                embed.add_field(name=f"{emoji} {display_name}", value=str(qty), inline=True)
        else:
            embed.add_field(name="Inventory Empty", value="You have no items.", inline=False)

        await ctx.send(embed=embed)


    @rpg.command(name="stats", help="Show your current RPG stats and level progress.")
    async def rpg_stats(self, ctx: commands.Context):
        """Display stats with paging buttons."""
        user = ctx.author
        # load all fields
        data = await self.parent.config.user(user).all()
        # send the multi-page view instead of a single embed
        view = StatsView(self, ctx, data)
        await ctx.send(embed=view.current_embed(), view=view) 
 
    @rpg.command(name="shop", help="Show or choose a shop in your current region.")
    async def rpg_shop(self, ctx, shop_id: Optional[str] = None):
        # 1) fetch state & current region
        state = await self.parent.ensure_player_state(ctx.author)
        current = state.get("region", "old_mill")
        region_def = regions.get(current)
        if not region_def:
            return await ctx.send(f"Your saved region `{current}` is invalid.")

        # 2) gather valid shops here
        valid_shops = [
            shops.get(sid) for sid in region_def.shops
            if shops.get(sid)
        ]
        if not valid_shops:
            return await ctx.send(f"No shops in **{region_def.name}**.")

        # 3) if no ID provided and multiple shops, show dropdown
        if not shop_id and len(valid_shops) > 1:
            return await ctx.send(
                f"Which shop in **{region_def.name}** would you like to visit?",
                view=self.ShopSelectView(self, ctx, valid_shops)
            )

        # 4) determine the target shop
        if shop_id:
            shop = shops.get(shop_id)
            if not shop:
                return await ctx.send(f"No such shop: `{shop_id}`.")
            if shop.region != current:
                return await ctx.send(
                    f"You can’t visit **{shop.name or shop.id}** from **{current}**."
                )
        else:
            # exactly one shop—auto-select it
            shop = valid_shops[0]

        # 5) show the normal ShopView
        view = ShopView(self, ctx, shop)
        await ctx.send(
            embed=view.current_embed(),
            view=view
        )
        
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
            # Level requirement check
            player_level = state.get("level", 1)
            if player_level < target.min_level:
                return await ctx.send(
                    f"🚫 You must be at least level {target.min_level} to travel to **{target.name}**."
                )

            await user_cfg.region.set(region_id)
            arrival = target.travel_text or f"You navigate winding paths and finally arrive at **{target.name}**."
            embed = discord.Embed(
                title=f"🏞️ Traveled to {target.name}",
                description=f"{arrival}\n\n{target.description}",
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

    @rpg.command(name="quests", help="Browse and accept quests available in your region.")
    async def rpg_quests(self, ctx: commands.Context):
        state = await self.parent.ensure_player_state(ctx.author)
        current = state.get("region", "old_mill")
        region_def = regions.get(current)
        
        # filter available quests
        available = [
            q for q in quests.all()
            if q.region == current
            and q.id not in state.get("active_quests", {})
            and q.id not in state.get("completed_quests", [])
        ]
        if not available:
            return await ctx.send(f"No new quests in **{region_def.name}**.")

        # build a rich embed
        embed = Embed(
            title=f"📝 Quests in {region_def.name}",
            description="Select a quest to accept from the dropdown below.",
            color=Color.random()
        )

        # use the region thumbnail as a banner
        if region_def.thumbnail:
            embed.set_image(url=region_def.thumbnail)

        # list each quest as a field
        for q in available:
            embed.add_field(name=q.title, value=q.description, inline=False)

        # send with the selection view
        await ctx.send(embed=embed, view=QuestSelectView(self, ctx, available))
        
    @rpg.command(name="equip", help="Equip or unequip your gear.")
    async def rpg_equip(self, ctx: commands.Context):
        """
        Let the player pick a slot (weapon, head, etc.) to (un)equip.
        """
        state = await self.parent.ensure_player_state(ctx.author)
        
        # 1) Create the Embed
        equip_embed = Embed(
            title="🛡️ Manage Equipment",
            description="Select a slot to equip or unequip gear.",
            color=Color.random()
        )
        
        # 2) Add your banner
        equip_embed.set_image(url=GENERAL_EQUIP_BANNER)
        
        # 3) Send it with the view
        await ctx.send(embed=equip_embed, view=SlotSelectView(self, ctx, state))

    @rpg.group(name="give", invoke_without_command=True)
    async def rpg_give(self, ctx):
        """
        Give gold or items to another player.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @rpg_give.command(name="gold")
    async def give_gold(self, ctx, target: Member, amount: int):
        """
        Transfer gold to someone else.
        Usage: [p]rpg give gold @User 50
        """
        sender = ctx.author
        # ensure both states exist
        await self.parent.ensure_player_state(sender)
        await self.parent.ensure_player_state(target)

        cfg_s = self.parent.config.user(sender)
        cfg_t = self.parent.config.user(target)
        state_s = await cfg_s.all()
        state_t = await cfg_t.all()

        if amount <= 0 or state_s["gold"] < amount:
            return await ctx.send("❌ You don’t have enough gold.")

        # perform transfer
        await cfg_s.update({"gold": state_s["gold"] - amount})
        await cfg_t.update({"gold": state_t["gold"] + amount})

        await ctx.send(f"💰 {sender.display_name} gave {amount}g to {target.display_name}.")

    @rpg_give.command(name="item")
    async def give_item(self, ctx, target: Member, item_id: str, quantity: int = 1):
        """
        Give items from your inventory.
        Usage: [p]rpg give item @User potion_common 2
        """
        sender = ctx.author
        await self.parent.ensure_player_state(sender)
        await self.parent.ensure_player_state(target)

        cfg_s = self.parent.config.user(sender)
        cfg_t = self.parent.config.user(target)
        state_s = await cfg_s.all()
        state_t = await cfg_t.all()

        inv_s = state_s.get("inventory", {})
        have = inv_s.get(item_id, 0)
        if quantity <= 0 or have < quantity:
            return await ctx.send("❌ You don’t have that many items to give.")

        # remove from sender
        inv_s[item_id] = have - quantity
        if inv_s[item_id] == 0:
            inv_s.pop(item_id)
        await cfg_s.inventory.set(inv_s)

        # add to recipient
        inv_t = state_t.setdefault("inventory", {})
        inv_t[item_id] = inv_t.get(item_id, 0) + quantity
        await cfg_t.inventory.set(inv_t)

        # human-friendly name
        item_def = items.get(item_id)
        name = item_def.name if item_def else item_id

        await ctx.send(
            f"🎁 {sender.display_name} gave {quantity}× **{name}** to {target.display_name}."
        )        

    @rpg.command(name="duel")
    async def rpg_duel(self, ctx, opponent: Member, wager: int = 0):
        """
        Challenge a player to duel. Optionally wager gold.
        Usage: [p]rpg duel @User [wager]
        """
        challenger = ctx.author
        if opponent.bot or opponent == challenger:
            return await ctx.send("Invalid target.")
        # ensure state
        state_c = await self.parent.ensure_player_state(challenger)
        state_o = await self.parent.ensure_player_state(opponent)

        # validate wager
        if wager < 0 or state_c["gold"] < wager or state_o["gold"] < wager:
            return await ctx.send("❌ Both players must have that much gold to wager.")

        # lock in wager
        if wager > 0:
            cfg = self.parent.config
            await cfg.user(challenger).update({"gold": state_c["gold"] - wager})
            await cfg.user(opponent).update({"gold": state_o["gold"] - wager})

        # snapshot stats
        def snap(s):
            return {
                "hp":      s.get("hp", s.get("max_hp", 20)),
                "max_hp":  s.get("max_hp", 20),
                "mp":      s.get("mp", s.get("max_mp", 10)),
                "max_mp":  s.get("max_mp", 10),
                "attack":  s.get("attack", 5),
                "defense": s.get("defense", 1),
                "accuracy":s.get("accuracy", 1.0),
                "evasion": s.get("evasion", 1.0),
            }

        stats_c = snap(state_c)
        stats_o = snap(state_o)

        view = DuelView(self, ctx, challenger, opponent, stats_c, stats_o, wager)
        header = f"⚔️ {challenger.display_name} challenges {opponent.display_name} to a duel!"
        await ctx.send(header, embed=view.build_embed(), view=view)        

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
            name  = getattr(itm, "name", item_id)
            emoji = RARITY_EMOJIS.get(itm.rarity, "")
            groups[cat].append(f"{emoji} **{name}** — {cost}g")

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
            color=Color.random()
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
            emoji = RARITY_EMOJIS.get(itm_def.rarity, "")
            options.append(SelectOption(
                label=f"{emoji} {itm_def.name}",
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
            f"How many **{items.get(obj_id).name}** at {cost_per}g each?",
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
            color=Color.random()
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
        valid_defs = [shops.get(sid) for sid in reg.shops if shops.get(sid)]
        if valid_defs:
            shop_lines = [f"🏪 {sd.name}" for sd in valid_defs]
            e.add_field(name="Shops", value="\n".join(shop_lines), inline=False)

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

            # only the original author can confirm
            if interaction.user != view.ctx.author:
                return await interaction.response.send_message(
                    "This isn’t your travel session.", ephemeral=True
                )

            target_id = view.adjacents[view.page]
            dest = regions.get(target_id)

            # ─── Level requirement check ────────────────────────────────────────
            state = await view.cog.config.user(interaction.user).all()
            player_level = state.get("level", 1)
            if player_level < getattr(dest, "min_level", 1):
                return await interaction.response.send_message(
                    f"🚫 You must be at least level {dest.min_level} to travel to **{dest.name}**.",
                    ephemeral=True
                )
            # ───────────────────────────────────────────────────────────────────

            # perform the travel
            user_cfg = view.cog.config.user(interaction.user)
            await user_cfg.region.set(target_id)

            # build the arrival embed
            arrival = dest.travel_text or f"After your journey, you set foot in **{dest.name}** at last."
            embed = discord.Embed(
                title=f"🏞️ Traveled to {dest.name}",
                description=f"{arrival}\n\n{dest.description}",
                color=Color.random()
            )
            if dest.thumbnail:
                embed.set_image(url=dest.thumbnail)

            valid_shops = []
            for sid in dest.shops:
                shop_def = shops.get(sid)
                label = shop_def.name if shop_def else sid
                valid_shops.append(f"🏪 {label}")
            if valid_shops:
                embed.add_field(
                    name="Available Shops",
                    value="\n".join(valid_shops),
                    inline=False
                )

            # remove buttons after confirming
            await interaction.response.edit_message(embed=embed, view=None)

            

class StatsView(View):
    def __init__(self, cog: commands.Cog, ctx: commands.Context, data: dict):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.data = data
        self.page = 0
        # Add one button per page
        for idx, label in enumerate(("Stats", "Gear", "Skills", "Spells")):
            # Highlight current page by using primary style
            style = ButtonStyle.primary if idx == self.page else ButtonStyle.secondary
            self.add_item(self.PageButton(label, idx, style))

    class PageButton(Button):
        def __init__(self, label: str, idx: int, style: ButtonStyle):
            super().__init__(label=label, style=style)
            self.idx = idx

        async def callback(self, interaction: discord.Interaction):
            view: StatsView = self.view
            # Update page
            view.page = self.idx
            # Refresh all buttons’ styles
            for btn in view.children:
                btn.style = ButtonStyle.primary if getattr(btn, "idx", None) == view.page else ButtonStyle.secondary
            # Edit the message with the new embed
            await interaction.response.edit_message(embed=view.current_embed(), view=view)

    def current_embed(self) -> discord.Embed:
        """Return embed based on self.page."""
        user = self.ctx.author
        d = self.data
        if self.page == 0:
            embed = discord.Embed(
                title=f"{user.display_name}'s RPG Stats",
                color=discord.Color.random()
            )
            embed.set_image(url=STATS_BANNER_URL)            
            # replicate your existing fields
            lvl = d["level"]
            xp, next_xp = d["xp"], xp_to_next(lvl)
            embed.add_field(name="Level", value=str(lvl), inline=True)
            embed.add_field(name="XP", value=f"{xp} / {next_xp}", inline=True)
            embed.add_field(name="HP", value=f"{d['hp']} / {d['max_hp']}", inline=True)
            embed.add_field(name="MP", value=f"{d['mp']} / {d['max_mp']}", inline=True)
            embed.add_field(name="Attack", value=str(d["attack"]), inline=True)
            embed.add_field(name="Defense", value=str(d["defense"]), inline=True)
            embed.add_field(name="Magic Attack", value=str(d.get("magic_attack", 0)), inline=True)
            embed.add_field(name="Magic Defense", value=str(d.get("magic_defense", 0)), inline=True)
            embed.add_field(name="Accuracy", value=f"{d['accuracy']:.2f}", inline=True)
            embed.add_field(name="Evasion", value=f"{d['evasion']:.2f}", inline=True)
            embed.add_field(name="Gold", value=str(d["gold"]), inline=True)
            inv_count = sum(d.get("inventory", {}).values())
            embed.add_field(name="Items in Inventory", value=str(inv_count), inline=True)
            return embed

        if self.page == 1:
            embed = discord.Embed(
                title=f"{user.display_name}'s Equipped Gear",
                color=discord.Color.random()
            )
            embed.set_image(url=GEAR_BANNER_URL)
            equip = d.get("equipment", {})
            for slot, item_id in equip.items():
                name = items.get(item_id).name if item_id else "Empty"
                embed.add_field(name=slot.replace("_", " ").title(), value=name, inline=True)
            return embed

        if self.page == 2:
            embed = discord.Embed(
                title=f"{user.display_name}'s Skills",
                color=discord.Color.random()
            )
            embed.set_image(url=SKILLS_BANNER_URL)
            skills = d.get("skills", [])  # adjust key if you name it differently
            if skills:
                embed.description = "\n".join(f"- {s}" for s in skills)
            else:
                embed.description = "No skills learned."
            return embed

        # page == 3: spells
        embed = discord.Embed(
            title=f"{user.display_name}'s Spells",
            color=discord.Color.random()
        )
        embed.set_image(url=SPELLS_BANNER_URL)
        learned = d.get("spells", [])
        if learned:
            embed.description = "\n".join(f"- {spells.get(sp).name}" for sp in learned)
        else:
            embed.description = "No spells learned."
        return embed            
        
class QuestSelectView(View):
    def __init__(self, cog, ctx, quest_defs: list[QuestDef]):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.quests = quest_defs
        self.add_item(QuestSelect(self, quest_defs))

class QuestSelect(Select):
    def __init__(self, view: QuestSelectView, quest_defs: list[QuestDef]):
        options = [
            discord.SelectOption(label=q.title, value=q.id, description=q.description)
            for q in quest_defs
        ]
        super().__init__(placeholder="Choose a quest…",
                         min_values=1, max_values=1,
                         options=options)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        qid = self.values[0]
        qdef = next(q for q in self.view_ref.quests if q.id == qid)
        user = interaction.user
        cfg = self.view_ref.cog.parent.config.user(user)

        # region guard (extra safety)
        state = await cfg.all()
        if state.get("region") != qdef.region:
            return await interaction.response.send_message(
                "You must be in the right region to accept this quest.", ephemeral=True
            )

        # register quest
        active = state.setdefault("active_quests", {})
        # initialize progress counters based on requirements
        active[qid] = {   # e.g. {"kill": {"goblin_scout": 0}}
            key: {eid: 0 for eid in reqs} 
            for key, reqs in qdef.requirements.items()
        }
        await cfg.active_quests.set(active)

        await interaction.response.edit_message(
            content=f"✅ You’ve accepted **{qdef.title}**!",
            embed=None, view=None
        )
        
class SlotSelectView(View):
    def __init__(self, cog, ctx, state: dict):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.state = state

        slots = list(state.get("equipment", {}).keys())
        options = []
        for slot in slots:
            pretty = slot.replace("_", " ").title()
            current = state["equipment"].get(slot)
            desc = f"Equipped: {items.get(current).name}" if current else "Empty"
            options.append(
                discord.SelectOption(label=pretty, value=slot, description=desc)
            )
        self.add_item(SlotSelect(options))

class SlotSelect(Select):
    def __init__(self, options: list[SelectOption]):
        super().__init__(
            placeholder="Choose slot…",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # 1) Grab the slot key and player state
        slot = self.values[0]
        view: SlotSelectView = self.view
        inv = view.state.get("inventory", {})

        # 2) Build the list of equippable items in that slot
        choices: list[SelectOption] = []
        for item_id, qty in inv.items():
            it = items.get(item_id)
            if it and it.equip_slot == slot:
                # pull the emoji by the item’s rarity
                emoji = RARITY_EMOJIS.get(it.rarity, "")
                choices.append(SelectOption(
                    label=f"{emoji} {it.name}",
                    value=item_id,
                    description=f"{qty} in inventory"
                ))

        # Always allow an “Unequip” option
        choices.insert(0, SelectOption(
            label="Unequip",
            value="__unequip__",
            description="Remove currently equipped item"
        ))

        # 3) Pretty-print the slot name
        pretty_slot = slot.replace("_", " ").title()

        # 4) Build the embed and apply the slot’s banner
        embed = Embed(
            title=f"⚙️ Slot: {pretty_slot}",
            description="Select an item to equip, or choose to unequip.",
            color=Color.green()
        )
        banner_url = SLOT_BANNERS.get(slot)
        if banner_url:
            embed.set_image(url=banner_url)

        # 5) Edit the original message with the new embed and next view
        await interaction.response.edit_message(
            embed=embed,
            view=EquipSelectView(view.cog, view.ctx, slot, choices)
        )



class EquipSelectView(View):
    def __init__(self, cog, ctx, slot: str, options: list[discord.SelectOption]):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.slot = slot
        self.add_item(EquipSelect(options, slot))

class EquipSelect(Select):
    def __init__(self, options, slot: str):
        super().__init__(
            placeholder="Choose gear…",
            min_values=1,
            max_values=1,
            options=options
        )
        self.slot = slot

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        cfg = self.view.cog.parent.config.user(user)
        state = await cfg.all()

        old_id = state["equipment"].get(self.slot)
        new_id = self.values[0]

        # Unequip logic
        if new_id == "__unequip__":
            if old_id:
                old = items.get(old_id)
                for stat, val in old.modifiers.items():
                    state[stat] -= val
                state["equipment"][self.slot] = None
                await cfg.update({self.slot: None, **{stat: state[stat] for stat in old.modifiers}})
                msg = f"Unequipped **{old.name}** from {self.slot}."
            else:
                msg = "Nothing to unequip."
            await interaction.response.edit_message(content=msg, embed=None, view=None)
            return

        # Equip logic
        it = items.get(new_id)
        if not it or it.equip_slot != self.slot:
            return await interaction.response.send_message(
                "Invalid item for this slot.", ephemeral=True
            )
        # Level requirement check
        player_level = state.get("level", 1)
        if player_level < it.min_level:
            return await interaction.response.send_message(
                f"🚫 You must be at least level {it.min_level} to equip **{it.name}**.", ephemeral=True
            )

        # Remove old modifiers
        if old_id:
            old = items.get(old_id)
            for stat, val in old.modifiers.items():
                state[stat] -= val

        # Apply new modifiers
        for stat, val in it.modifiers.items():
            state[stat] = state.get(stat, 0) + val

        state["equipment"][self.slot] = new_id

        # Persist both equipment map & stat changes
        update_payload = {"equipment": state["equipment"]}
        for stat in it.modifiers:
            update_payload[stat] = state[stat]
        await cfg.update(update_payload)

        await interaction.response.edit_message(
            content=f"Equipped **{it.name}** in {self.slot}.",
            embed=None,
            view=None
        )
        
class DuelView(View):
    def __init__(
        self,
        cog,
        ctx,
        p1: Member,
        p2: Member,
        stats_p1: dict,
        stats_p2: dict,
        wager: int = 0
    ):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.p1, self.p2 = p1, p2
        # map member.id → stats dict
        self.stats = {p1.id: stats_p1, p2.id: stats_p2}
        self.turn = random.choice([p1.id, p2.id])
        self.rounds = 0
        self.log: list[str] = []
        self.wager = wager
        # Deduct wager from both immediately if >0
        if wager > 0:
            cfg = cog.parent.config
            for m in (p1, p2):
                state = random  # placeholder
            # We'll deduct in rpg_duel before sending view

    def build_embed(self) -> Embed:
        def bar(cur, mx):
            filled = int((cur / mx) * 10)
            return "█"*filled + "░"*(10 - filled)

        s1 = self.stats[self.p1.id]
        s2 = self.stats[self.p2.id]
        e = Embed(
            title=f"⚔️ Duel: {self.p1.display_name} vs {self.p2.display_name}",
            description=f"Turn: {self.ctx.guild.get_member(self.turn).display_name}",
            color=Color.random()
        )
        e.set_image(url=DUEL_BANNER_URL)
        # Player 1
        e.add_field(
            name=self.p1.display_name,
            value=(
                f"HP: {s1['hp']}/{s1['max_hp']}  `{bar(s1['hp'], s1['max_hp'])}`\n"
                f"MP: {s1['mp']}/{s1['max_mp']}`  `{bar(s1['mp'], s1['max_mp'])}`\n"
                f"Atk: {s1['attack']}  Def: {s1['defense']}"
            ),
            inline=False
        )
        # Player 2
        e.add_field(
            name=self.p2.display_name,
            value=(
                f"HP: {s2['hp']}/{s2['max_hp']}  `{bar(s2['hp'], s2['max_hp'])}`\n"
                f"MP: {s2['mp']}/{s2['max_mp']}`  `{bar(s2['mp'], s2['max_mp'])}`\n"
                f"Atk: {s2['attack']}  Def: {s2['defense']}"
            ),
            inline=False
        )
        e.add_field(name="Log", value="\n".join(self.log[-6:]) or "―", inline=False)
        e.set_footer(text=f"Rounds: {self.rounds}  Pot: {self.wager*2}g")
        return e

    # ─── Attack ───────────────────────────────────────────────────────────────
    @button(label="Attack", style=ButtonStyle.primary)
    async def attack(self, interaction, _):
        if interaction.user.id != self.turn:
            return await interaction.response.send_message("Not your turn!", ephemeral=True)

        attacker = interaction.user
        defender = self.p2 if attacker.id == self.p1.id else self.p1
        atk = self.stats[attacker.id]
        df  = self.stats[defender.id]

        self.rounds += 1
        if _roll_hit(atk["accuracy"], df["evasion"]):
            crit = _roll_crit()
            dmg  = _calc_damage(atk["attack"], df["defense"], crit)
            df["hp"] = max(0, df["hp"] - dmg)
            self.log.append(f"{attacker.display_name} hits {defender.display_name} for {dmg}{' crit' if crit else ''}")
        else:
            self.log.append(f"{attacker.display_name} misses")

        if df["hp"] <= 0:
            return await self.end_duel(interaction, winner=attacker)

        # reset any defend bonus
        atk.pop("_defend_bonus", None)
        self.turn = defender.id
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # ─── Defend ───────────────────────────────────────────────────────────────
    @button(label="Defend", style=ButtonStyle.secondary)
    async def defend(self, interaction, _):
        if interaction.user.id != self.turn:
            return await interaction.response.send_message("Not your turn!", ephemeral=True)

        self.rounds += 1
        self.stats[interaction.user.id]["_defend_bonus"] = 0.5
        self.log.append(f"{interaction.user.display_name} braces for impact")
        self.turn = (self.p2 if interaction.user.id == self.p1.id else self.p1).id
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # ─── Spell ────────────────────────────────────────────────────────────────
    @button(label="Spell", style=ButtonStyle.success)
    async def cast_spell(self, interaction, _):
        if interaction.user.id != self.turn:
            return await interaction.response.send_message("Not your turn!", ephemeral=True)

        known = await self.cog.parent.config.user(interaction.user).spells()  # list[str]
        if not known:
            return await interaction.response.send_message("No spells learned.", ephemeral=True)

        # send ephemeral select menu
        await interaction.response.send_message(
            "Select a spell:", view=SpellSelectView(self, known),
            ephemeral=True
        )

    # ─── Skill ─────────────────────────────────────────────────────────────
    @button(label="Skill", style=ButtonStyle.success)
    async def skill_button(self, interaction, _):
        if interaction.user.id != self.turn:
            return await interaction.response.send_message("Not your turn!", ephemeral=True)

        # fetch known skills from Config
        known = await self.cog.parent.config.user(interaction.user).skills()
        if not known:
            return await interaction.response.send_message("You haven’t learned any skills.", ephemeral=True)

        # fire off an ephemeral selection menu
        await interaction.response.send_message(
            "Choose a skill to use:", 
            view=SkillSelectView(self, known),
            ephemeral=True
        )

    # ─── Item ─────────────────────────────────────────────────────────────────
    @button(label="Item", style=ButtonStyle.primary)
    async def use_item(self, interaction, _):
        if interaction.user.id != self.turn:
            return await interaction.response.send_message("Not your turn!", ephemeral=True)

        state = await self.cog.parent.config.user(interaction.user).all()
        inv = {iid: qty for iid, qty in state["inventory"].items() if items.get(iid).stats.get("heal", 0) > 0}
        if not inv:
            return await interaction.response.send_message("No healing items.", ephemeral=True)

        options = [
            SelectOption(label=items[i].name, value=i, description=f"Heal {items[i].stats['heal']} HP")
            for i in inv
        ]
        await interaction.response.send_message(
            "Select an item to use:", view=ItemSelectView(self, options),
            ephemeral=True
        )

    # ─── Forfeit ──────────────────────────────────────────────────────────────
    @button(label="Forfeit", style=ButtonStyle.danger)
    async def forfeit(self, interaction, _):
        if interaction.user.id not in (self.p1.id, self.p2.id):
            return await interaction.response.send_message("Not your duel!", ephemeral=True)

        winner = self.p2 if interaction.user.id == self.p1.id else self.p1
        return await self.end_duel(interaction, winner=winner)

    # ─── End Duel ─────────────────────────────────────────────────────────────
    async def end_duel(self, interaction, winner: Member):
        # disable all buttons
        for btn in self.children:
            btn.disabled = True

        loser = self.p2 if winner.id == self.p1.id else self.p1
        self.log.append(f"🏆 {winner.display_name} wins!")

        # payout wager
        cfg = self.cog.parent.config
        if self.wager > 0:
            winner_state = await cfg.user(winner).all()
            await cfg.user(winner).update({"gold": winner_state["gold"] + self.wager*2})

        # persist both players' remaining HP & MP (use ensure_player_state + set)
        for m in (self.p1, self.p2):
            # load full state, update HP/MP, then overwrite entire profile
            state = await self.cog.parent.ensure_player_state(m)
            state["hp"] = self.stats[m.id]["hp"]
            state["mp"] = self.stats[m.id]["mp"]
            await self.cog.parent.config.user(m).set(state)

        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        self.stop()

class SpellSelect(Select):
    def __init__(self, view_ref: DuelView, known_spells: list[str]):
        opts = [
            SelectOption(label=spells[s].name, value=s)
            for s in known_spells if spells.get(s)
        ]
        super().__init__(placeholder="Choose a spell…", min_values=1, max_values=1, options=opts)
        self.view_ref = view_ref

    async def callback(self, interaction):
        view = self.view_ref
        spell_id = self.values[0]
        user   = interaction.user
        stat   = view.stats[user.id]
        sp_def = spells.get(spell_id)

        # MP check
        if stat["mp"] < sp_def.cost:
            return await interaction.response.send_message("Not enough MP", ephemeral=True)

        stat["mp"] -= sp_def.cost
        if _roll_hit(stat["accuracy"], view.stats[(view.p2 if user.id==view.p1.id else view.p1).id]["evasion"]):
            dmg = _calc_damage(stat["attack"]+sp_def.power,
                               view.stats[(view.p2 if user.id==view.p1.id else view.p1).id]["defense"],
                               _roll_crit())
            target = view.p2 if user.id == view.p1.id else view.p1
            view.stats[target.id]["hp"] = max(0, view.stats[target.id]["hp"] - dmg)
            view.log.append(f"{user.display_name} casts {sp_def.name} for {dmg}")
        else:
            view.log.append(f"{sp_def.name} missed")

        if view.stats[target.id]["hp"] <= 0:
            return await view.end_duel(interaction, winner=user)

        # switch turn
        view.turn = target.id
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

class SpellSelectView(View):
    def __init__(self, duel_view, known_spells):
        super().__init__(timeout=30)
        self.add_item(SpellSelect(duel_view, known_spells))

class ItemSelect(Select):
    def __init__(self, options):
        super().__init__(placeholder="Choose item…", min_values=1, max_values=1, options=options)

    async def callback(self, interaction):
        view = self.view.parent  # DuelView is parent of this View
        item_id = self.values[0]
        user    = interaction.user
        stat    = view.stats[user.id]
        # heal
        amount = items[item_id].stats["heal"]
        stat["hp"] = min(stat["max_hp"], stat["hp"] + amount)
        # consume from config
        cfg = view.cog.parent.config.user(user)
        state = await cfg.all()
        inv = state["inventory"]
        inv[item_id] -= 1
        if inv[item_id] == 0:
            inv.pop(item_id)
        await cfg.inventory.set(inv)

        view.log.append(f"{user.display_name} uses {items[item_id].name} for {amount} HP")
        # switch turn
        view.turn = (view.p2 if user.id == view.p1.id else view.p1).id
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

class ItemSelectView(View):
    def __init__(self, duel_view, options):
        super().__init__(timeout=30)
        self.add_item(ItemSelect(options))
        
class SkillSelect(Select):
    def __init__(self, view_ref: DuelView, known_skills: list[str]):
        options = [
            SelectOption(label=sk.title(), value=sk)
            for sk in known_skills
        ]
        super().__init__(
            placeholder="Select a skill…",
            min_values=1, max_values=1,
            options=options
        )
        self.view_ref = view_ref

    async def callback(self, interaction):
        view = self.view_ref
        user = interaction.user
        skill_id = self.values[0]
        attacker = user
        defender = view.p2 if user.id == view.p1.id else view.p1

        sk_def = skills.get(skill_id)

        # MP check
        stat = view.stats[user.id]
        if stat["mp"] < sk_def.cost:
            return await interaction.response.send_message(
                f"Not enough MP for {sk_def.name}.", ephemeral=True
            )

        # Deduct MP
        stat["mp"] -= sk_def.cost
        atk = view.stats[attacker.id]
        df  = view.stats[defender.id]

        # Placeholder: scale attack by 1.5x for skills
        crit = _roll_crit()
        raw = atk["attack"] * 1.5
        dmg = _calc_damage(int(raw), df["defense"], crit)

        df["hp"] = max(0, df["hp"] - dmg)
        view.log.append(f"{attacker.display_name} uses **{skill_id}** for {dmg}{' crit' if crit else ''}")

        # check for end
        if df["hp"] <= 0:
            return await view.end_duel(interaction, winner=attacker)

        # switch turn
        view.turn = defender.id
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

class SkillSelectView(View):
    def __init__(self, duel_view: DuelView, known_skills: list[str]):
        super().__init__(timeout=30)
        self.add_item(SkillSelect(duel_view, known_skills))         
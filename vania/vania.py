import json
import random
from pathlib import Path

import discord
from redbot.core import commands
from redbot.core.data_manager import cog_data_path

class Vania(commands.Cog):
    """Belmont’s Legacy: Hunter progression with XP and skills."""

    def __init__(self, bot):
        self.bot = bot
                
        data_pkg = Path(__file__).parent / "data"
        self.monsters = self._load_file(data_pkg / "monsters.json")
        self.items = self._load_file(data_pkg / "items.json")
        self.skills_def = self._load_file(data_pkg / "skills.json")
        self.equipment = self._load_file(data_pkg / "equipment.json")
        self.bosses     = self._load_file(data_pkg / "bosses.json")
        
        # Raid state file
        data_folder = cog_data_path(self)
        data_folder.mkdir(parents=True, exist_ok=True)
        self.raid_file = data_folder / "raids.json"
        if not self.raid_file.exists():
            self.raid_file.write_text(json.dumps({}))        
        
        # Prepare JSON storage in Red’s cog data path
        data_folder = cog_data_path(self)
        data_folder.mkdir(parents=True, exist_ok=True)
        self.data_file: Path = data_folder / "profiles.json"
        if not self.data_file.exists():
            self.data_file.write_text(json.dumps({}))
            
    def _load_file(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(f"{path.name} not found in data folder")
        return json.loads(path.read_text())            

    def _load_profiles(self) -> dict:
        return json.loads(self.data_file.read_text())

    def _save_profiles(self, data: dict):
        self.data_file.write_text(json.dumps(data, indent=2))
        
    # ─── Raid & Data Helpers ──────────────────────────────────────────────
    def _load_raids(self) -> dict:
        """Load active raid state from raids.json."""
        return json.loads(self.raid_file.read_text())

    def _save_raids(self, data: dict):
        """Persist active raid state back to raids.json."""
        self.raid_file.write_text(json.dumps(data, indent=2))

    def _health_bar(self, current: int, maximum: int, length: int = 20) -> str:
        """Render a text health bar of given length."""
        filled = int(current / maximum * length)
        return "█" * filled + "─" * (length - filled)
    # ────────────────────────────────────────────────────────────────────        

    @commands.group(name="vania", invoke_without_command=True)
    async def vania(self, ctx: commands.Context):
        """Main command for Belmont’s Legacy RPG."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @vania.command(name="hunt")
    async def hunt(self, ctx: commands.Context):
        """Begin a monster hunt using monsters.json and apply gear effects."""
        profiles = self._load_profiles()
        uid = str(ctx.author.id)
        profile = profiles.get(uid, {
            "xp": 0,
            "skills": {},
            "weapon": "vine_whip",
            "armor": None,
            "hp": 100,
            "max_hp": 100
        })
    
        # Pick a random monster and fetch its image URL
        monster = random.choice(self.monsters)
        image_url = monster.get("image")
    
        # Gear stats
        weapon = next((e for e in self.equipment if e["id"] == profile.get("weapon")), {})
        armor  = next((e for e in self.equipment if e["id"] == profile.get("armor")), {}) if profile.get("armor") else {}
        xp_mod   = weapon.get("xp_mod", 1.0)
        dmg_mod  = weapon.get("damage_mod", 1.0)
        defense  = armor.get("defense", 0)
    
        # Battle outcome
        if random.random() <= monster.get("win_chance", 0.5):
            base_xp = monster.get("xp_reward", 0)
            xp_gain = int(base_xp * xp_mod)
            profile["xp"] += xp_gain
            description = f"You defeated **{monster['name']}** and gained {xp_gain} XP!"
            color = discord.Color.green()
        else:
            base_dmg = random.randint(5, 15)
            damage = max(0, int(base_dmg * dmg_mod) - defense)
            profile["hp"] = max(0, profile["hp"] - damage)
            description = f"The **{monster['name']}** wounded you for {damage} HP!"
            color = discord.Color.orange()
    
        # Collapse handling
        if profile["hp"] == 0:
            description += "\nYour HP dropped to 0. You collapse and revive at half HP."
            profile["hp"] = profile["max_hp"] // 2
    
        # Save profile
        profiles[uid] = profile
        self._save_profiles(profiles)
    
        # Build embed with image
        embed = discord.Embed(
            title="Monster Hunt",
            description=description,
            color=color
        )
        if image_url:
            embed.set_image(url=image_url)
    
        embed.add_field(name="HP", value=f"{profile['hp']}/{profile['max_hp']}", inline=True)
        embed.add_field(name="XP", value=str(profile["xp"]), inline=True)
        await ctx.send(embed=embed)



    @vania.command(name="stats")
    async def stats(self, ctx: commands.Context):
        """View your hunter’s level, XP, and equipped whip."""
        profiles = self._load_profiles()
        uid = str(ctx.author.id)
        profile = profiles.get(uid)
        if not profile:
            return await ctx.send("No profile found. Start hunting with `vania hunt`.")
    
        xp = profile["xp"]
        level = xp // 100 + 1
        weapon_id = profile.get("weapon", "vine_whip")
        armor_id = profile.get("armor")
        weapon = next((e for e in self.equipment if e["id"] == weapon_id), {})
        armor  = next((e for e in self.equipment if e["id"] == armor_id), {}) if armor_id else {}
        weapon_name = weapon.get("name", "None")
        armor_name  = armor.get("name", "None")
        skills = profile.get("skills", {})
    
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Profile",
            color=discord.Color.dark_blue()
        )
        embed.add_field(name="Level", value=level, inline=True)
        embed.add_field(name="XP", value=xp, inline=True)
        embed.add_field(name="Weapon", value=weapon_name, inline=True)
        embed.add_field(name="Armor", value=armor_name, inline=True)
    
        if skills:
            skill_list = "\n".join(f"{name}: Lv {lvl}" for name, lvl in skills.items())
            embed.add_field(name="Skills", value=skill_list, inline=False)
    
        await ctx.send(embed=embed)

    @vania.command(name="train")
    async def train(self, ctx: commands.Context, skill: str):
        """
        Spend XP to unlock or upgrade a skill.
        Example skills: WhipMastery, CrossThrow
        """
        profiles = self._load_profiles()
        uid = str(ctx.author.id)
        profile = profiles.get(uid)
        if not profile:
            return await ctx.send("Start hunting first with `vania hunt`.")

        skills = profile.setdefault("skills", {})
        current = skills.get(skill, 0)
        cost = (current + 1) * 50

        if profile["xp"] < cost:
            return await ctx.send(f"You need {cost} XP to train {skill} (you have {profile['xp']} XP).")

        profile["xp"] -= cost
        skills[skill] = current + 1
        profiles[uid] = profile
        self._save_profiles(profiles)

        embed = discord.Embed(
            title="Training Complete",
            description=f"{skill} upgraded to level {skills[skill]}!",
            color=discord.Color.green()
        )
        embed.add_field(name="XP Remaining", value=str(profile["xp"]))
        await ctx.send(embed=embed)
        
    @vania.command(name="equip")
    async def equip(self, ctx: commands.Context, item_id: str):
        """Equip a weapon or armor from equipment.json."""
        profiles = self._load_profiles()
        uid = str(ctx.author.id)
        profile = profiles.get(uid)
        if not profile:
            return await ctx.send("Start hunting first with `vania hunt`.")
    
        item = next((e for e in self.equipment if e["id"] == item_id), None)
        if not item:
            return await ctx.send(f"No equipment found with ID `{item_id}`.")
    
        # Equip by category
        if item["category"] == "weapon":
            profile["weapon"] = item_id
        elif item["category"] == "armor":
            profile["armor"] = item_id
    
        profiles[uid] = profile
        self._save_profiles(profiles)
        await ctx.send(f"You have equipped **{item['name']}** as your {item['category']}.")
       

    @vania.group(name="raid", invoke_without_command=True)
    async def raid(self, ctx: commands.Context):
        """Raid commands: schedule and start boss fights."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @raid.command(name="schedule")
    @commands.admin_or_permissions(manage_guild=True)
    async def raid_schedule(self, ctx: commands.Context, boss_id: str, channel: discord.TextChannel):
        """Schedule a raid against <boss_id> in the specified channel."""
        boss = next((b for b in self.bosses if b["id"] == boss_id), None)
        if not boss:
            return await ctx.send(f"No boss found with ID `{boss_id}`.")

        embed = discord.Embed(
            title=f"Raid Sign-Up: {boss['name']}",
            description="React with ✅ to join the raid!",
            color=discord.Color.purple()
        )
        embed.add_field(name="Boss HP", value=str(boss["hp"]), inline=False)
        msg = await channel.send(embed=embed)
        await msg.add_reaction("✅")

        raids = self._load_raids()
        raids[boss_id] = {
            "channel_id": channel.id,
            "message_id": msg.id
        }
        self._save_raids(raids)
        await ctx.send(f"Raid vs **{boss['name']}** scheduled in {channel.mention}.")

    @raid.command(name="start")
    @commands.admin_or_permissions(manage_guild=True)
    async def raid_start(self, ctx: commands.Context, boss_id: str):
        """Start the scheduled raid, resolve combat, and handle win or loss."""
        raids = self._load_raids()
        entry = raids.get(boss_id)
        if not entry:
            return await ctx.send(f"No active raid found for `{boss_id}`.")

        boss = next((b for b in self.bosses if b["id"] == boss_id), None)
        if not boss:
            return await ctx.send(f"Boss definition for `{boss_id}` missing.")

        # Fetch signup message and reactors
        channel = self.bot.get_channel(entry["channel_id"])
        try:
            msg = await channel.fetch_message(entry["message_id"])
        except discord.NotFound:
            return await ctx.send("Raid signup message not found.")

        reaction = discord.utils.get(msg.reactions, emoji="✅")
        participants = (
            [user async for user in reaction.users() if not user.bot]
            if reaction
            else []
        )
        if not participants:
            return await ctx.send("No participants joined the raid.")

        # Simulate group damage
        boss_max_hp = boss["hp"]
        boss_hp = boss_max_hp
        reports = []
        for member in participants:
            dmg = random.randint(20, 50)
            boss_hp = max(0, boss_hp - dmg)
            reports.append(f"**{member.display_name}** hits for {dmg}")
            if boss_hp == 0:
                break

        bar = self._health_bar(boss_hp, boss_max_hp)
        description = "\n".join(reports)
        description += f"\n\nBoss HP: `{boss_hp}/{boss_max_hp}`\n{bar}"
        image_url = boss.get("image")

        # Build result embed
        embed = discord.Embed(
            title=f"Raid vs {boss['name']}",
            description=description,
            color=discord.Color.red() if boss_hp > 0 else discord.Color.gold()
        )
        if image_url:
            embed.set_image(url=image_url)

        await channel.send(embed=embed)

        # Win or Loss branch
        if boss_hp == 0:
            # Victory: reward participants
            profiles = self._load_profiles()
            reward_lines = []
            for member in participants:
                uid = str(member.id)
                profile = profiles.get(uid, {"xp": 0, "hearts": 0, "relics": []})
                xp = boss["xp_reward"]
                hearts = boss["heart_reward"]
                relic = random.choice(boss["relic_pool"])
                profile["xp"] += xp
                profile["hearts"] = profile.get("hearts", 0) + hearts
                profile["relics"] = profile.get("relics", []) + [relic]
                profiles[uid] = profile
                reward_lines.append(f"{member.display_name}: +{xp} XP, +{hearts} Hearts, **{relic}**")
            self._save_profiles(profiles)

            victory_embed = discord.Embed(
                title="Raid Victory! 🎉",
                description="\n".join(reward_lines),
                color=discord.Color.green()
            )
            if image_url:
                victory_embed.set_thumbnail(url=image_url)
            await channel.send(embed=victory_embed)
        else:
            # Defeat: notify participants
            fail_embed = discord.Embed(
                title="Raid Failed 💀",
                description=(
                    f"The raid against **{boss['name']}** has failed. "
                    "The boss still stands victorious."
                ),
                color=discord.Color.dark_gray()
            )
            if image_url:
                fail_embed.set_thumbnail(url=image_url)
            await channel.send(embed=fail_embed)

        # Cleanup raid entry
        raids.pop(boss_id, None)
        self._save_raids(raids)


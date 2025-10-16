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
       

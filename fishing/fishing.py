import random
import asyncio
import discord
import bisect
from typing import Dict, Tuple, List, Optional, Any
from itertools import accumulate
from functools import wraps

from redbot.core import commands, bank, Config

QUEST_BANNER_URL = "https://files.catbox.moe/x5iczt.png"
ROD_IMAGE_URL = "https://files.catbox.moe/0h4ja9.png"



# ——— ACHIEVEMENT DECORATOR ———
def award_achievements(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        # run the wrapped command
        result = await func(self, ctx, *args, **kwargs)

        # then check & announce any new achievements
        try:
            msgs = await self._check_and_award(ctx, ctx.author)
            if msgs:
                await ctx.send("\n".join(msgs))
        except Exception:
            pass

        return result
    return wrapper
# ——————————————————————————


class Fishing(commands.Cog):
    """Fishing minigame with fish, events, achievements, rod upgrades, crafting, NPC traders and questlines."""

    def __init__(self, bot):
        self.bot = bot
        # Config
        self.config = Config.get_conf(self, identifier=1234567890123)
        default_user = {
            "caught": [],        # list of fish names and items (strings)
            "rod_broken": False,
            "bait": 0,
            "luck": 0,
            "achievements": [],  # achievement ids
            "stats": {           # tracked stats for achievements
                "casts": 0,
                "fish_caught": 0,
                "unique_fish": 0,
                "highest_value_catch": 0,
                "sell_total": 0,
                "consecutive_catches": 0,
                "bait_collected_total": 0,
            },
            "items": [],         # non-fish items like "Rod Fragment", "Rod Core", "Treasure Map", "Chum"
            "rod_level": 0,      # 0 = basic
            "quests": {},        # per-user quest state: {"active": quest_id or None, "step": int, "progress": {...}, "completed": [...]}
        }
        self.config.register_user(**default_user)

        # ---------- Fish definitions ----------
        self.fish_definitions = {
            "Tiny Minnow": {"weight": 200, "price": 2, "emoji": "><>", "rarity": "Common", "biome": "Pond"},
            "Mosquito Fish": {"weight": 180, "price": 3, "emoji": "🐟", "rarity": "Common", "biome": "Marsh"},
            "Bluegill": {"weight": 160, "price": 5, "emoji": "🐠", "rarity": "Common", "biome": "Pond"},
            "Sardine": {"weight": 150, "price": 4, "emoji": "🐟", "rarity": "Common", "biome": "Coastal"},
            "Silverside": {"weight": 150, "price": 6, "emoji": "🐟", "rarity": "Common", "biome": "Coastal"},
            "Shiner": {"weight": 140, "price": 6, "emoji": "🔆", "rarity": "Common", "biome": "River"},
            "Perch": {"weight": 120, "price": 8, "emoji": "🐡", "rarity": "Uncommon", "biome": "Lake"},
            "Mudskipper": {"weight": 115, "price": 7, "emoji": "🐸", "rarity": "Common", "biome": "Mangrove"},
            "Koi": {"weight": 110, "price": 12, "emoji": "🎏", "rarity": "Uncommon", "biome": "Garden Pond"},
            "Glass Eel": {"weight": 100, "price": 10, "emoji": "🔮", "rarity": "Uncommon", "biome": "Estuary"},
            "Gudgeon": {"weight": 95, "price": 9, "emoji": "🐟", "rarity": "Common", "biome": "Stream"},
            "Carp": {"weight": 90, "price": 11, "emoji": "🐠", "rarity": "Uncommon", "biome": "Lake"},
            "Herring": {"weight": 85, "price": 7, "emoji": "🐠", "rarity": "Common", "biome": "Coastal"},
            "Trout": {"weight": 80, "price": 14, "emoji": "🎣", "rarity": "Uncommon", "biome": "Stream"},
            "Rainbow Trout": {"weight": 75, "price": 18, "emoji": "🌈", "rarity": "Rare", "biome": "River"},
            "Salmon": {"weight": 70, "price": 20, "emoji": "🐟", "rarity": "Rare", "biome": "River"},
            "Char": {"weight": 65, "price": 18, "emoji": "❄️", "rarity": "Rare", "biome": "Cold Lake"},
            "Mackerel": {"weight": 60, "price": 16, "emoji": "🐟", "rarity": "Common", "biome": "Coastal"},
            "Pike": {"weight": 58, "price": 22, "emoji": "🦈", "rarity": "Rare", "biome": "Freshwater"},
            "Rockfish": {"weight": 56, "price": 20, "emoji": "🪨", "rarity": "Uncommon", "biome": "Reef"},
            "Largemouth Bass": {"weight": 50, "price": 26, "emoji": "🎣", "rarity": "Rare", "biome": "Lake"},
            "Rock Bass": {"weight": 48, "price": 12, "emoji": "🐡", "rarity": "Uncommon", "biome": "River"},
            "Smallmouth Bass": {"weight": 46, "price": 24, "emoji": "🐟", "rarity": "Rare", "biome": "River"},
            "Catfish": {"weight": 44, "price": 28, "emoji": "🐱‍🏍", "rarity": "Rare", "biome": "River"},
            "Sea Urchin": {"weight": 40, "price": 18, "emoji": "🟣", "rarity": "Uncommon", "biome": "Rocky Shore"},
            "Seahorse": {"weight": 38, "price": 25, "emoji": "🐴", "rarity": "Rare", "biome": "Seagrass"},
            "Flounder": {"weight": 36, "price": 30, "emoji": "🪸", "rarity": "Rare", "biome": "Coastal"},
            "Sturgeon": {"weight": 34, "price": 45, "emoji": "🐡", "rarity": "Epic", "biome": "River"},
            "Cuttlefish": {"weight": 32, "price": 34, "emoji": "🦑", "rarity": "Rare", "biome": "Coastal"},
            "Yellowtail": {"weight": 30, "price": 38, "emoji": "🟡", "rarity": "Rare", "biome": "Coastal"},
            "Amberjack": {"weight": 28, "price": 48, "emoji": "🪝", "rarity": "Epic", "biome": "Offshore"},
            "Harlequin Shrimp": {"weight": 26, "price": 44, "emoji": "🦐", "rarity": "Epic", "biome": "Reef"},
            "Snapper": {"weight": 24, "price": 32, "emoji": "🐠", "rarity": "Rare", "biome": "Reef"},
            "Octopus": {"weight": 22, "price": 70, "emoji": "🐙", "rarity": "Epic", "biome": "Reef"},
            "Pufferfish": {"weight": 20, "price": 48, "emoji": "🎈", "rarity": "Epic", "biome": "Reef"},
            "Mahi Mahi": {"weight": 18, "price": 60, "emoji": "🐬", "rarity": "Epic", "biome": "Tropical Ocean"},
            "Lionfish": {"weight": 16, "price": 55, "emoji": "🦁", "rarity": "Epic", "biome": "Reef"},
            "Electric Ray": {"weight": 14, "price": 80, "emoji": "⚡", "rarity": "Legendary", "biome": "Ocean Floor"},
            "Ghost Carp": {"weight": 12, "price": 90, "emoji": "👻", "rarity": "Legendary", "biome": "Murky Lake"},
            "Giant Grouper": {"weight": 12, "price": 95, "emoji": "🐋", "rarity": "Legendary", "biome": "Reef"},
            "Halibut": {"weight": 10, "price": 36, "emoji": "🐟", "rarity": "Epic", "biome": "Cold Ocean"},
            "Swordfish": {"weight": 9, "price": 120, "emoji": "🗡️", "rarity": "Legendary", "biome": "Open Ocean"},
            "Tuna": {"weight": 8, "price": 75, "emoji": "🐋", "rarity": "Legendary", "biome": "Open Ocean"},
            "Anglerfish": {"weight": 6, "price": 200, "emoji": "🎣", "rarity": "Mythic", "biome": "Abyssal"},
            "Dragonfish": {"weight": 5, "price": 300, "emoji": "🐉", "rarity": "Mythic", "biome": "Abyssal"},
            "Blue Marlin": {"weight": 5, "price": 180, "emoji": "🔱", "rarity": "Mythic", "biome": "Deep Ocean"},
            "Marlin": {"weight": 4, "price": 150, "emoji": "🏹", "rarity": "Legendary", "biome": "Deep Ocean"},
            "Hammerhead": {"weight": 3, "price": 140, "emoji": "🔨", "rarity": "Mythic", "biome": "Open Ocean"},
            "Great White": {"weight": 2, "price": 0, "emoji": "🦈", "rarity": "Boss", "biome": "Deep Ocean"},
            "Butterfish": {"weight": 88, "price": 9, "emoji": "🧈", "rarity": "Common", "biome": "Coastal"},
            "Sculpin": {"weight": 70, "price": 13, "emoji": "🪱", "rarity": "Uncommon", "biome": "Rocky Shore"},
            "Scorpionfish": {"weight": 26, "price": 42, "emoji": "☠️", "rarity": "Epic", "biome": "Reef"},
            "Moray Eel": {"weight": 18, "price": 50, "emoji": "🦎", "rarity": "Epic", "biome": "Reef"},
            "Moonfin Sprite": {"weight": 95, "price": 25, "emoji": "🌙", "rarity": "Uncommon", "biome": "Moonlit Lake"},
            "Glow Carp": {"weight": 85, "price": 30, "emoji": "✨", "rarity": "Rare", "biome": "Bioluminal Sea"},
            "Crystal Trout": {"weight": 70, "price": 60, "emoji": "🔹", "rarity": "Epic", "biome": "Crystal River"},
            "Phoenix Minnow": {"weight": 30, "price": 120, "emoji": "🔥", "rarity": "Legendary", "biome": "Volcanic Spring"},
            "Abyssal Wisp": {"weight": 10, "price": 220, "emoji": "🕯️", "rarity": "Mythic", "biome": "Abyssal Rift"},
            "Merrow Snapper": {"weight": 40, "price": 45, "emoji": "🧜", "rarity": "Epic", "biome": "Seagrass"},
            "Frostling": {"weight": 55, "price": 35, "emoji": "❄️", "rarity": "Rare", "biome": "Frozen Bay"},
            "Stormwing Tuna": {"weight": 12, "price": 160, "emoji": "🌩️", "rarity": "Legendary", "biome": "Tempest Ocean"},
            "Elder Koi": {"weight": 100, "price": 75, "emoji": "🀄", "rarity": "Rare", "biome": "Sacred Pond"},
            "Void Puffer": {"weight": 14, "price": 210, "emoji": "🕳️", "rarity": "Mythic", "biome": "Void Trench"},
            "Silver Seraph": {"weight": 8, "price": 275, "emoji": "🕊️", "rarity": "Mythic", "biome": "Celestial Shoal"},
            "Coral Drake": {"weight": 28, "price": 140, "emoji": "🐉", "rarity": "Legendary", "biome": "Reef"},
            "Bramble Snapper": {"weight": 48, "price": 50, "emoji": "🌿", "rarity": "Uncommon", "biome": "Enchanted Marsh"},
            "Glimmer Eel": {"weight": 22, "price": 95, "emoji": "💫", "rarity": "Epic", "biome": "Bioluminal Sea"},
            "Sunscale": {"weight": 16, "price": 180, "emoji": "☀️", "rarity": "Legendary", "biome": "Tropical Reef"},
            "Nightmare Haddock": {"weight": 20, "price": 160, "emoji": "🌑", "rarity": "Mythic", "biome": "Dreaming Deep"},
            "Arcane Sprat": {"weight": 140, "price": 14, "emoji": "🔮", "rarity": "Common", "biome": "Magic Brook"},
            "Mossback Grouper": {"weight": 48, "price": 46, "emoji": "🍃", "rarity": "Uncommon", "biome": "Swamp"},
            "Spectral Herring": {"weight": 60, "price": 70, "emoji": "👻", "rarity": "Epic", "biome": "Haunted Shoals"},
            "Goldcrest Cod": {"weight": 42, "price": 85, "emoji": "🪙", "rarity": "Rare", "biome": "Treasure Banks"},
            "Sapphire Anchovy": {"weight": 78, "price": 22, "emoji": "🔷", "rarity": "Uncommon", "biome": "Coral Gardens"},
            "Thunder Carp": {"weight": 36, "price": 130, "emoji": "⚡", "rarity": "Legendary", "biome": "Tempest Ocean"},
            "Mistling": {"weight": 92, "price": 28, "emoji": "🌫️", "rarity": "Uncommon", "biome": "Foggy Lake"},
            "Rune Snapper": {"weight": 26, "price": 110, "emoji": "🪄", "rarity": "Epic", "biome": "Ancient Reef"},
            "Plume Salmon": {"weight": 62, "price": 95, "emoji": "🪶", "rarity": "Rare", "biome": "Riverbanks"},
            "Star Pike": {"weight": 54, "price": 140, "emoji": "⭐", "rarity": "Epic", "biome": "Deep Ocean"},
            "Twilight Bass": {"weight": 44, "price": 120, "emoji": "🌒", "rarity": "Legendary", "biome": "Dusk Lakes"},
            "Eclipse Tuna": {"weight": 6, "price": 260, "emoji": "🌓", "rarity": "Mythic", "biome": "Open Ocean"},
            "Ivory Seahorse": {"weight": 34, "price": 85, "emoji": "🦩", "rarity": "Rare", "biome": "Seagrass"},
            "Cinderfish": {"weight": 20, "price": 95, "emoji": "🪵", "rarity": "Epic", "biome": "Volcanic Spring"},
            "Aurora Trout": {"weight": 72, "price": 150, "emoji": "🌈", "rarity": "Legendary", "biome": "Northern River"},
            "Mire Leviathan": {"weight": 3, "price": 0, "emoji": "🐲", "rarity": "Boss", "biome": "Bog Depths"},
            "Wispling": {"weight": 82, "price": 19, "emoji": "🕊️", "rarity": "Common", "biome": "Willow Stream"},
            "Obsidian Ray": {"weight": 18, "price": 160, "emoji": "🖤", "rarity": "Legendary", "biome": "Lava Reef"},
            "Pearl Kelp": {"weight": 28, "price": 40, "emoji": "🐚", "rarity": "Uncommon", "biome": "Seagrass"},
            "Echo Carp": {"weight": 88, "price": 32, "emoji": "🔔", "rarity": "Common", "biome": "Echo Pool"},
            "Trilobite":         {"weight":120, "price":40,  "emoji":"🐞", "rarity":"Uncommon",   "biome":"Prehistoric"},
            "Ammonite":          {"weight": 90, "price":45,  "emoji":"🐚", "rarity":"Uncommon",   "biome":"Prehistoric"},
            "Dunkleosteus":      {"weight": 40, "price":120, "emoji":"🦖", "rarity":"Epic",       "biome":"Prehistoric"},
            "Coelacanth":        {"weight": 80, "price":60,  "emoji":"🐟", "rarity":"Rare",       "biome":"Prehistoric"},
            "Titanichthys":      {"weight": 70, "price":70,  "emoji":"🏺", "rarity":"Rare",       "biome":"Prehistoric"},
            "Leedsichthys":      {"weight":100, "price":50,  "emoji":"🦕", "rarity":"Rare",       "biome":"Prehistoric"},
            "Megalodon":         {"weight": 20, "price":200, "emoji":"🦈", "rarity":"Legendary", "biome":"Prehistoric"},
            "Placoderm":         {"weight":110, "price":55,  "emoji":"🦴", "rarity":"Uncommon",   "biome":"Prehistoric"},
            "Xiphactinus":       {"weight": 60, "price":65,  "emoji":"🐡", "rarity":"Rare",       "biome":"Prehistoric"},
            "Ichthyosaur":       {"weight": 50, "price":75,  "emoji":"🦑", "rarity":"Rare",       "biome":"Prehistoric"},
            "Phytosaur":         {"weight": 55, "price":45,  "emoji":"🐊", "rarity":"Uncommon",   "biome":"Prehistoric"},
            "Stethacanthus":     {"weight": 45, "price":80,  "emoji":"🏹", "rarity":"Rare",       "biome":"Prehistoric"},
            "Helicoprion":       {"weight": 30, "price":90,  "emoji":"🌀", "rarity":"Epic",       "biome":"Prehistoric"},
            "Eusthenopteron":    {"weight": 95, "price":40,  "emoji":"🐠", "rarity":"Uncommon",   "biome":"Prehistoric"},
            "Palaeospondylus":   {"weight": 85, "price":35,  "emoji":"🐟", "rarity":"Common",     "biome":"Prehistoric"},
            "Unicorn Trout":     {"weight": 75, "price":120, "emoji":"🦄", "rarity":"Legendary",  "biome":"Magical"},
            "Faerie Guppy":      {"weight":160, "price":45,  "emoji":"🧚", "rarity":"Uncommon",   "biome":"Magical"},
            "Crystal Carp":      {"weight": 65, "price":60,  "emoji":"🔹", "rarity":"Epic",       "biome":"Magical"},
            "Mystic Koi":        {"weight":110, "price":80,  "emoji":"🔮", "rarity":"Rare",       "biome":"Magical"},
            "Phoenix Minnow":    {"weight": 40, "price":150, "emoji":"🔥", "rarity":"Mythic",     "biome":"Magical"},
            "Hydra Bass":        {"weight": 50, "price":140, "emoji":"🐉", "rarity":"Legendary",  "biome":"Magical"},
            "Spirit Cod":        {"weight": 70, "price":95,  "emoji":"👻", "rarity":"Rare",       "biome":"Magical"},
            "Mana Mackerel":     {"weight": 60, "price":85,  "emoji":"🪄", "rarity":"Rare",       "biome":"Magical"},
            "Goblin Goby":       {"weight":130, "price":40,  "emoji":"👹", "rarity":"Common",     "biome":"Magical"},
            "Pixie Pike":        {"weight": 54, "price":110, "emoji":"✨", "rarity":"Epic",       "biome":"Magical"},
            "Elf Eel":           {"weight": 55, "price":100, "emoji":"🧝", "rarity":"Rare",       "biome":"Magical"},
            "Rune Ray":          {"weight": 14, "price":130, "emoji":"🪄", "rarity":"Legendary",  "biome":"Magical"},
            "Charm Tuna":        {"weight":  8, "price":125, "emoji":"🪄", "rarity":"Legendary",  "biome":"Magical"},
            "Illusion Herring":  {"weight": 38, "price":100, "emoji":"🔮", "rarity":"Epic",       "biome":"Magical"},
            "Enchanted Salmon":  {"weight": 75, "price":110, "emoji":"🪶", "rarity":"Epic",       "biome":"Magical"},
            "Nebula Eel":        {"weight": 50, "price":100, "emoji":"🌌", "rarity":"Epic",       "biome":"Space"},
            "Meteor Minnow":     {"weight":150, "price":35,  "emoji":"☄️", "rarity":"Uncommon",   "biome":"Space"},
            "Galactic Tuna":     {"weight": 18, "price":230, "emoji":"🐋", "rarity":"Mythic",     "biome":"Space"},
            "Star Whale":        {"weight": 10, "price":300, "emoji":"🌠", "rarity":"Legendary",  "biome":"Space"},
            "Comet Carp":        {"weight": 88, "price":90,  "emoji":"☄",  "rarity":"Rare",       "biome":"Space"},
            "Asteroid Salmon":   {"weight": 85, "price":85,  "emoji":"🪨", "rarity":"Rare",       "biome":"Space"},
            "Pluto Perch":       {"weight":120, "price":45,  "emoji":"🪐", "rarity":"Uncommon",   "biome":"Space"},
            "Solar Flounder":    {"weight": 36, "price":110, "emoji":"☀️", "rarity":"Epic",       "biome":"Space"},
            "Lunar Bass":        {"weight": 44, "price":120, "emoji":"🌕", "rarity":"Legendary",  "biome":"Space"},
            "Cosmic Cod":        {"weight": 42, "price":100, "emoji":"🌠", "rarity":"Rare",       "biome":"Space"},
            "Orbit Trout":       {"weight": 80, "price":95,  "emoji":"🔄", "rarity":"Uncommon",   "biome":"Space"},
            "Quasar Pike":       {"weight": 54, "price":140, "emoji":"✨", "rarity":"Epic",       "biome":"Space"},
            "Gravity Grouper":   {"weight": 48, "price":115, "emoji":"🌍", "rarity":"Rare",       "biome":"Space"},
            "Supernova Snapper": {"weight": 24, "price":160, "emoji":"💥", "rarity":"Legendary",  "biome":"Space"},
            "Astro Anglerfish":  {"weight":  6, "price":220, "emoji":"🚀", "rarity":"Mythic",     "biome":"Space"},            
        }
        # Derived prices
        self.fish_prices = {name: info["price"] for name, info in self.fish_definitions.items()}

        # Achievements                
        self.achievements: Dict[str, Tuple[str, str, str]] = {
            "first_cast": ("First Cast", "Cast your line for the first time.", "general"),
            "first_fish": ("First Fish", "Catch your first fish.", "catch"),
            "fish_10": ("Getting Warm", "Catch 10 fish total.", "catch"),
            "fish_100": ("Dedicated Angler", "Catch 100 fish total.", "catch"),
            "unique_5": ("Variety Pack", "Catch 5 different fish species.", "collection"),
            "unique_25": ("Menagerie", "Catch 25 different fish species.", "collection"),
            "mythic_catch": ("Mythic Hook", "Catch any Mythic rarity fish.", "rarity"),
            "epic_streak_3": ("Epic Streak", "Catch 3 epic-or-better fish consecutively.", "streak"),
            "sell_1000": ("Merchant", "Sell fish totaling 1000 currency.", "economy"),
            "treasure_hunter": ("Treasure Hunter", "Find a treasure chest event.", "event"),
            "pearl_finder": ("Pearl Finder", "Find a pearl.", "event"),
            "map_collector": ("Map Collector", "Find a Treasure Map.", "collection"),
            "sea_monster_survivor": ("Sea Monster Survivor", "Survive a sea monster event and get a reward.", "event"),
            "double_catch": ("Lucky Pair", "Get a double catch.", "event"),
            "bait_collector": ("Bait Hoarder", "Collect 20 bait in total.", "resource"),
            "rod_repaired": ("Back in Action", "Repair your rod for the first time.", "general"),
            "first_chum": ("First Chum", "Craft your first Chum.", "craft"),
            "trophy_maker": ("Trophy Maker", "Craft your first Trophy.", "craft"),
            "fragment_collector": ("Fragment Collector", "Collect 10 Rod Fragments.", "resource"),
            "core_seeker": ("Core Seeker", "Obtain your first Rod Core.", "resource"),
            "rod_master_1": ("Rod Novice", "Upgrade your rod to level 1.", "rod"),
            "rod_master_2": ("Rod Expert", "Upgrade your rod to level 2.", "rod"),
            "rod_master_3": ("Rod Legend", "Upgrade your rod to level 3.", "rod"),
            "double_trouble": ("Double Trouble", "Trigger 5 double catches.", "event"),
            "net_haul": ("Net Hauler", "Get an event that yields 10+ fish total.", "event"),
            "treasure_collect": ("Treasure Collector", "Find 5 treasure chests.", "event"),
            "pearl_hoarder": ("Pearl Hoarder", "Find 3 pearls.", "event"),
            "map_explorer": ("Map Explorer", "Collect 3 Treasure Maps.", "event"),
            "sea_legend": ("Sea Legend", "Catch any Boss fish.", "boss"),
            "abyssal_finder": ("Abyssal Finder", "Catch an Abyssal or Mythic fish.", "rarity"),
            "mythic_hunter": ("Mythic Hunter", "Catch 3 Mythic fish total.", "rarity"),
            "legend_chaser": ("Legend Chaser", "Catch 5 Legendary fish total.", "rarity"),
            "spectral_hunter": ("Ghost Bounty", "Catch a Spectral Herring or similar spectral fish.", "special"),
            "festival_fan": ("Festival Fan", "Benefit from the Festival event 3 times.", "event"),
            "npc_friend": ("Friend of the Town", "Complete 5 quests from any NPC.", "quest"),
            "quest_master": ("Quest Master", "Complete 25 quests total.", "quest"),
            "merchant_of_mean": ("Merchant of Mean", "Sell 500 total value of fish.", "economy"),
            "crafting_ace": ("Crafting Ace", "Craft every recipe at least once.", "craft"),
            "oceanographer": ("Oceanographer", "Catch at least one fish from every biome.", "collection"),
            "collector_100": ("Collector", "Have 100 fish in your collection (duplicates count).", "collection"),
            "seasoned_angler": ("Seasoned Angler", "Cast 1000 times.", "general"),
            "bait_hoarder_plus": ("Bait Baron", "Collect 100 bait total.", "resource"),
            "salvage_expert": ("Salvage Expert", "Find 20 salvage events.", "event"),
            "hotspot_hunter": ("Hotspot Hunter", "Use a hotspot or map and catch a rare fish.", "special"),
            "cosmic_watcher": ("Cosmic Watcher", "Trigger a meteor_shower or moon_phase event.", "event"),
        }


        # Rarity ranks
        self.rarity_rank = {
            "Common": 0,
            "Uncommon": 1,
            "Rare": 2,
            "Epic": 3,
            "Legendary": 4,
            "Mythic": 5,
            "Boss": 6,
        }

        # Rod upgrade system
        self.rod_upgrade_requirements = {
            1: {"fragments": 3, "coins": 0},
            2: {"fragments": 6, "coins": 50},
            3: {"fragments": 10, "coins": 150},
        }
        self.rod_level_fish_multiplier = {0: 1.0, 1: 1.2, 2: 1.4, 3: 1.6}
        self.rod_level_break_reduction = {0: 1.0, 1: 0.8, 2: 0.6, 3: 0.4}

        # Crafting recipes
        self.crafting_recipes = {
            "chum": {
                "name": "Chum",
                "requirements": {"any_fish": 3},
                "result": {"item": "Chum"},
                "description": "Combine any 3 fish to craft Chum (consumable). Using Chum gives +3 luck.",
            },
            "trophy": {
                "name": "Trophy",
                "requirements": {"any_fish": 5},
                "result": {"coins": 100},
                "description": "Combine any 5 fish to craft a Trophy and immediately receive 100 coins.",
            },
            "fragments_from_epic": {
                "name": "Epic Refinement",
                "requirements": {"rarity:Epic": 2},
                "result": {"items": {"Rod Fragment": 2}},
                "description": "Refine two Epic fish into 2 Rod Fragments (removes the fish).",
            },
        }

        # NPCs and questlines
        self.npcs = {
            "maris": {
                "display": "Maris the Merchant",
                "greeting": "Maris smiles and polishes a brass scale. 'Looking for work or wares?'",
                "quests": ["maris_fragment_hunt", "merchant_supply", "reef_expedition", "legend_hunt", "artifact_recovery"],
                "image": "https://files.catbox.moe/muc0lg.png",
            },
            "oldfinn": {
                "display": "Old Finn",
                "greeting": "'Hm, a keen eye for fish? I remember the river in my day…'",
                "quests": ["finn_first_catch", "boss_sightings", "river_cleanse", "river_runner", "high_stakes_sale"],
                "image": "https://files.catbox.moe/pxc6vz.png",
            },
            "lira": {
                "display": "Lira the Tidewatcher",
                "greeting": "'The tides speak to those who listen.'",
                "quests": ["tide_pool_mini", "midnight_hunt", "tide_change_event", "coastal_call", "treasure_finder"],
                "image": "https://files.catbox.moe/mv7rsg.png",
            },
            "garron": {
                "display": "Garron the Salvor",
                "greeting": "'I barter salvage and stories. Bring me trinkets.'",
                "quests": ["drifter_hunt", "drifting_crate_run", "reef_expedition", "salvage_strike"],
                "image": "https://files.catbox.moe/0rfed5.png",
            },
            "selene": {
                "display": "Selene the Moonseer",
                "greeting": "'The moon favors careful anglers.'",
                "quests": ["moon_phase_patrol", "midnight_hunt", "aurora_call", "abyssal_ambush", "boss_battle"],
                "image": "https://files.catbox.moe/3ehdme.png",
            },
            "berta": {
                "display": "Berta the Baitsmith",
                "greeting": "'Need bait? Or a quick job to earn some?'",
                "quests": ["easy_bait_run", "angler_apprentice", "seasonal_bounty", "beginners_luck", "pond_patrol"],
                "image": "https://files.catbox.moe/j6jlvc.png",
            },
            "thorin": {
                "display": "Thorin the Tactician",
                "greeting": "'I can set up a challenge if you're brave.'",
                "quests": ["epic_refinement", "legend_hunt", "mythic_probe", "epic_extraction"],
                "image": "https://files.catbox.moe/gey7m6.png",
            },
            "nym": {
                "display": "Nym of the Marsh",
                "greeting": "'The marsh keeps its secrets; trade me what you find.'",
                "quests": ["mire_tasks", "mossback_call", "river_cleanse", "legendary_capture"],
                "image": "https://files.catbox.moe/a78qlb.png",
            },
        }
        self.quests = {
            "finn_first_catch": {
                "title": "A Young Angler's Proving",
                "steps": [
                    {"type": "collect_fish", "rarity": "Common", "count": 3, "desc": "Catch 3 Common fish."},
                    {"type": "visit_npc", "npc": "oldfinn", "desc": "Return to Old Finn."},
                ],
                "rewards": {"coins": 25, "items": {"Rod Fragment": 1}},
                "repeatable": False,
            },
            "maris_fragment_hunt": {
                "title": "Fragments for a Discount",
                "steps": [
                    {"type": "deliver_item", "item": "Rod Fragment", "count": 3, "desc": "Bring 3 Rod Fragments."},
                ],
                "rewards": {"coins": 75, "items": {"Rod Core": 1}},
                "repeatable": True,
            },
            "easy_bait_run": {
                "title": "Bait Run",
                "steps": [
                    {"type": "collect_fish", "rarity": "Common", "count": 2, "desc": "Catch 2 Common fish."},
                ],
                "rewards": {"coins": 10, "items": {"Chum": 1}},
                "repeatable": True,
            },
            "river_cleanse": {
                "title": "River Cleanse",
                "steps": [
                    {"type": "collect_fish", "rarity": "Common", "count": 4, "desc": "Collect 4 Common fish from the river."},
                    {"type": "deliver_item", "item": "Treasure Map", "count": 1, "desc": "Deliver any Treasure Map."},
                ],
                "rewards": {"coins": 30, "items": {"Rod Fragment": 1}},
                "repeatable": False,
            },
            "angler_apprentice": {
                "title": "Angler Apprentice",
                "steps": [
                    {"type": "collect_fish", "rarity": "Uncommon", "count": 3, "desc": "Catch 3 Uncommon fish."},
                    {"type": "sell_value", "amount": 50, "desc": "Sell fish totalling 50 coins."},
                ],
                "rewards": {"coins": 50, "items": {"Chum": 2}},
                "repeatable": True,
            },
            "reef_expedition": {
                "title": "Reef Expedition",
                "steps": [
                    {"type": "collect_fish", "rarity": "Rare", "count": 2, "desc": "Catch 2 Rare fish from reef biomes."},
                    {"type": "deliver_item", "item": "Coral Trinket", "count": 1, "desc": "Deliver a Coral Trinket if you have one."},
                ],
                "rewards": {"coins": 100, "items": {"Rod Fragment": 2}},
                "repeatable": False,
            },
            "midnight_hunt": {
                "title": "Midnight Hunt",
                "steps": [
                    {"type": "collect_fish", "rarity": "Rare", "count": 3, "desc": "Catch 3 Rare fish at night."},
                    {"type": "visit_npc", "npc": "maris", "desc": "Report back to Maris."},
                ],
                "rewards": {"coins": 150, "items": {"Chum": 3}},
                "repeatable": True,
            },
            "epic_refinement": {
                "title": "Epic Refinement",
                "steps": [
                    {"type": "collect_fish", "rarity": "Epic", "count": 2, "desc": "Gather 2 Epic fish."},
                    {"type": "deliver_item", "item": "Rod Fragment", "count": 1, "desc": "Deliver 1 Rod Fragment."},
                ],
                "rewards": {"coins": 250, "items": {"Rod Core": 1}},
                "repeatable": False,
            },
            "boss_sightings": {
                "title": "Boss Sightings",
                "steps": [
                    {"type": "visit_npc", "npc": "oldfinn", "desc": "Hear the old tales from Old Finn."},
                    {"type": "collect_fish", "rarity": "Boss", "count": 1, "desc": "Survive and secure evidence of a Boss encounter."},
                ],
                "rewards": {"coins": 0, "items": {"Map": 1}},
                "repeatable": False,
            },
            "mythic_probe": {
                "title": "Mythic Probe",
                "steps": [
                    {"type": "collect_fish", "rarity": "Mythic", "count": 1, "desc": "Catch one Mythic rarity fish."},
                ],
                "rewards": {"coins": 500, "items": {"Rod Core": 1}},
                "repeatable": False,
            },
            "seasonal_bounty": {
                "title": "Seasonal Bounty",
                "steps": [
                    {"type": "collect_fish", "rarity": "Uncommon", "count": 5, "desc": "Catch 5 Uncommon fish during this season."},
                    {"type": "sell_value", "amount": 200, "desc": "Sell fish totalling 200 coins this season."},
                ],
                "rewards": {"coins": 200, "items": {"Chum": 5}},
                "repeatable": True,
            },
            "merchant_supply": {
                "title": "Merchant Supply",
                "steps": [
                    {"type": "deliver_item", "item": "Rod Fragment", "count": 5, "desc": "Bring 5 Rod Fragments to the merchant."},
                ],
                "rewards": {"coins": 300, "items": {"Rod Core": 1}},
                "repeatable": True,
            },
            "legend_hunt": {
                "title": "Legend Hunt",
                "steps": [
                    {"type": "collect_fish", "rarity": "Legendary", "count": 2, "desc": "Bring back 2 Legendary fish."},
                    {"type": "visit_npc", "npc": "maris", "desc": "Claim your reward from Maris."},
                ],
                "rewards": {"coins": 400, "items": {"Rod Core": 2}},
                "repeatable": False,
            },
            "tide_pool_mini": {
                "title": "Tide Pool Mini",
                "steps": [
                    {"type": "collect_fish", "rarity": "Common", "count": 3, "desc": "Collect 3 small fish from a tide pool."},
                ],
                "rewards": {"coins": 20, "items": {}},
                "repeatable": True,
            },
            "drifter_hunt": {
                "title": "Drifter Hunt",
                "steps": [
                    {"type": "collect_fish", "rarity": "Common", "count": 2, "desc": "Grab some fish from floating debris."},
                ],
                "rewards": {"coins": 30, "items": {}},
                "repeatable": True,
            },
            "drifting_crate_run": {
                "title": "Crate Run",
                "steps": [
                    {"type": "collect_fish", "rarity": "Uncommon", "count": 2, "desc": "Collect two Uncommon fish from drifting waters."},
                ],
                "rewards": {"coins": 45, "items": {"Rod Fragment": 1}},
                "repeatable": True,
            },
            "moon_phase_patrol": {
                "title": "Moon Patrol",
                "steps": [
                    {"type": "collect_fish", "rarity": "Rare", "count": 1, "desc": "Catch a Rare fish under moonlight."},
                    {"type": "visit_npc", "npc": "selene", "desc": "Report success to Selene."},
                ],
                "rewards": {"coins": 120, "items": {"Chum": 2}},
                "repeatable": False,
            },
            "aurora_call": {
                "title": "Aurora Call",
                "steps": [
                    {"type": "collect_fish", "rarity": "Legendary", "count": 1, "desc": "Catch a Legendary fish influenced by aurora."},
                ],
                "rewards": {"coins": 220, "items": {"Rod Fragment": 2}},
                "repeatable": False,
            },
            "mire_tasks": {
                "title": "Mire Tasks",
                "steps": [
                    {"type": "collect_fish", "rarity": "Uncommon", "count": 3, "desc": "Catch 3 Uncommon fish in the marsh."},
                ],
                "rewards": {"coins": 40, "items": {"Chum": 1}},
                "repeatable": True,
            },
            "mossback_call": {
                "title": "Mossback Call",
                "steps": [
                    {"type": "collect_fish", "rarity": "Uncommon", "count": 4, "desc": "Gather 4 Mossback-style fish."},
                    {"type": "visit_npc", "npc": "nym", "desc": "Report to Nym of the Marsh."},
                ],
                "rewards": {"coins": 90, "items": {"Rod Fragment": 1}},
                "repeatable": False,
            },    
            "beginners_luck": {
            "title": "Beginner's Luck",
            "difficulty": "Easy",
            "steps": [
                {"type": "collect_fish", "rarity": "Common", "count": 2,
                 "desc": "Catch 2 Common fish anywhere."}
            ],
            "rewards": {"coins": 20},
            "repeatable": True,
            },
            "pond_patrol": {
                "title": "Pond Patrol",
                "difficulty": "Easy",
                "steps": [
                    {"type": "collect_fish", "rarity": "Common", "count": 3,
                     "desc": "Catch 3 Common fish in a garden pond."}
                ],
                "rewards": {"coins": 30, "items": {"Chum": 1}},
                "repeatable": True,
            },
            "river_runner": {
                "title": "River Runner",
                "difficulty": "Easy",
                "steps": [
                    {"type": "collect_fish", "rarity": "Uncommon", "count": 2,
                     "desc": "Catch 2 Uncommon fish in a river."}
                ],
                "rewards": {"coins": 40},
                "repeatable": True,
            },
            "high_stakes_sale": {
                "title": "High-Stakes Sale",
                "difficulty": "Medium",
                "steps": [
                    {"type": "sell_value", "amount": 200,
                     "desc": "Sell fish totalling 200 coins."}
                ],
                "rewards": {"coins": 80},
                "repeatable": True,
            },
            "coastal_call": {
                "title": "Coastal Call",
                "difficulty": "Medium",
                "steps": [
                    {"type": "collect_fish", "rarity": "Rare", "count": 1,
                     "desc": "Land 1 Rare fish along the coast."}
                ],
                "rewards": {"coins": 100, "items": {"Treasure Map": 1}},
                "repeatable": True,
            },
            "salvage_strike": {
                "title": "Salvage Strike",
                "difficulty": "Medium",
                "steps": [
                    {"type": "collect_fish", "rarity": "Common", "count": 1,
                     "desc": "Find any salvage event reward (e.g. a Rod Fragment)."}
                ],
                "rewards": {"coins": 60, "items": {"Rod Fragment": 1}},
                "repeatable": True,
            },
            "treasure_finder": {
                "title": "Treasure Finder",
                "difficulty": "Medium",
                "steps": [
                    {"type": "deliver_item", "item": "Treasure Map", "count": 1,
                     "desc": "Turn in a Treasure Map."}
                ],
                "rewards": {"coins": 120, "items": {"Rod Core": 1}},
                "repeatable": False,
            },
            "artifact_recovery": {
                "title": "Artifact Recovery",
                "difficulty": "Hard",
                "steps": [
                    {"type": "deliver_item", "item": "Coral Trinket", "count": 2,
                     "desc": "Deliver 2 Coral Trinkets."}
                ],
                "rewards": {"coins": 250, "items": {"Rod Core": 2}},
                "repeatable": False,
            },
            "epic_extraction": {
                "title": "Epic Extraction",
                "difficulty": "Hard",
                "steps": [
                    {"type": "collect_fish", "rarity": "Epic", "count": 2,
                     "desc": "Catch 2 Epic fish."}
                ],
                "rewards": {"coins": 300, "items": {"Rod Fragment": 3}},
                "repeatable": False,
            },
            "legendary_capture": {
                "title": "Legendary Capture",
                "difficulty": "Hard",
                "steps": [
                    {"type": "collect_fish", "rarity": "Legendary", "count": 1,
                     "desc": "Bring in 1 Legendary fish."}
                ],
                "rewards": {"coins": 400, "items": {"Rod Core": 1}},
                "repeatable": False,
            },
            "abyssal_ambush": {
                "title": "Abyssal Ambush",
                "difficulty": "Very Hard",
                "steps": [
                    {"type": "collect_fish", "rarity": "Mythic", "count": 1,
                     "desc": "Hook a Mythic fish in the abyss."}
                ],
                "rewards": {"coins": 500, "items": {"Rod Core": 2}},
                "repeatable": False,
            },
            "boss_battle": {
                "title": "Boss Battle",
                "difficulty": "Elite",
                "steps": [
                    {"type": "collect_fish", "rarity": "Boss", "count": 1,
                     "desc": "Defeat and catch a Boss fish."}
                ],
                "rewards": {"coins": 800, "items": {"Map": 2}},
                "repeatable": False,    
            },
        }

        # Event registry
        self.event_handlers = {
            "nothing": (self._event_nothing, 35),
            "junk": (self._event_junk, 6),
            "fish": (self._event_fish, 28),
            "double": (self._event_double, 5),
            "shark": (self._event_shark, 3),
            "break": (self._event_break, 4),
            "treasure": (self._event_treasure, 4),
            "bottle": (self._event_bottle, 4),
            "storm": (self._event_storm, 2),
            "net": (self._event_net, 3),
            "bait_find": (self._event_bait_find, 5),
            "lucky_streak": (self._event_lucky_streak, 1),
            "curse": (self._event_curse, 1),
            "merchant": (self._event_merchant, 2),
            "pearl": (self._event_pearl, 2),
            "map": (self._event_map, 1),
            "sea_monster": (self._event_sea_monster, 1),
            "hook_snag": (self._event_hook_snag, 3),
            "festival": (self._event_festival, 1),
            "charity": (self._event_charity, 1),
            "salvage": (self._event_salvage, 2),
            "message": (self._event_message, 2),
            "bubble_burst": (self._event_bubble_burst, 4),
            "kelp_tangle": (self._event_kelp_tangle, 3),
            "whale_song": (self._event_whale_song, 1),
            "siren_call": (self._event_siren_call, 1),
            "tide_pool": (self._event_tide_pool, 3),
            "meteor_shower": (self._event_meteor_shower, 1),
            "coral_gift": (self._event_coral_gift, 2),
            "water_sprite": (self._event_water_sprite, 3),
            "whirlpool": (self._event_whirlpool, 2),
            "fisherman_friend": (self._event_fisherman_friend, 2),
            "barnacle_pearl": (self._event_barnacle_pearl, 2),
            "crystal_wash": (self._event_crystal_wash, 1),
            "echo_call": (self._event_echo_call, 1),
            "drifting_crate": (self._event_drifting_crate, 2),
            "phantom_net": (self._event_phantom_net, 2),
            "lazy_sun": (self._event_lazy_sun, 2),
            "thunder_clap": (self._event_thunder_clap, 1),
            "sponge_cache": (self._event_sponge_cache, 3),
            "tide_change": (self._event_tide_change, 1),
            "moon_phase": (self._event_moon_phase, 1),
            "rift_glimpse": (self._event_rift_glimpse, 1),
        }
        
        # ——— Pre-cache keys & base weights for faster picks ———
        self._event_keys          = list(self.event_handlers)
        self._event_base_weights  = [self.event_handlers[k][1] for k in self._event_keys]

        # Pre-cache fish name/weight arrays
        self._fish_names    = list(self.fish_definitions)
        self._fish_weights  = [info["weight"] for info in self.fish_definitions.values()]
        # ————————————————————————————————————————————————

    # ---------- Helpers ----------
    def _random_fish(self) -> str:
        # O(1) access to cached arrays
        return random.choices(self._fish_names, weights=self._fish_weights, k=1)[0]

    async def _deposit(self, member, amount: int, ctx):
        new_bal = await bank.deposit_credits(member, amount)
        currency = await bank.get_currency_name(ctx.guild) if ctx and ctx.guild else "credits"
        return new_bal, currency

    async def _has_achievement(self, user, ach_id: str) -> bool:
        earned = await self.config.user(user).achievements()
        return ach_id in earned

    async def _award_achievement(self, ctx, user, ach_id: str) -> Optional[str]:
        if ach_id not in self.achievements:
            return None
        
        # 1) Mark it earned
        user_conf = self.config.user(user)
        earned = await user_conf.achievements()
        if ach_id in earned:
            return None
        earned.append(ach_id)
        await user_conf.achievements.set(earned)
        
        # 2) Figure out name/description
        name, desc, _ = self.achievements[ach_id]
        
        # 3) Compute rewards
        reward = 0
        add_items: Dict[str, int] = {}
        
        # legacy small rewards
        if ach_id in ("first_cast", "first_fish"):
            reward = 5
        
        # existing larger rewards
        if ach_id == "mythic_catch":
            reward = 100
        if ach_id == "treasure_hunter":
            reward = 25
        
        # new achievement rewards
        if ach_id == "first_chum":
            reward = 10
        if ach_id == "trophy_maker":
            reward = 25
        if ach_id == "fragment_collector":
            reward = 50
        if ach_id == "core_seeker":
            reward = 150
        if ach_id == "rod_master_1":
            reward = 20
        if ach_id == "rod_master_2":
            reward = 60
        if ach_id == "rod_master_3":
            reward = 180
        if ach_id == "npc_friend":
            add_items = {"Chum": 1}
        if ach_id == "quest_master":
            reward = 300
        if ach_id == "oceanographer":
            reward = 200
        if ach_id == "collector_100":
            reward = 150
        if ach_id == "seasoned_angler":
            reward = 100
        
        # 4) Build announcement text
        currency = await bank.get_currency_name(ctx.guild) if ctx and ctx.guild else "credits"
        parts: List[str] = [f"🏆 Achievement unlocked: **{name}** — {desc}"]
        
        # 5) Deposit coins if any
        if reward > 0:
            new_bal = await bank.deposit_credits(user, reward)
            parts.append(f"You received **{reward} {currency}**! New balance: **{new_bal} {currency}**.")
        
        # 6) Grant any item-only rewards
        if add_items:
            items_cfg = await user_conf.items()
            for iname, cnt in add_items.items():
                for _ in range(cnt):
                    items_cfg.append(iname)
            await user_conf.items.set(items_cfg)
            added = ", ".join(f"{c}× {n}" for n, c in add_items.items())
            parts.append(f"You also received {added}.")
        
        text = "\n".join(parts)

        return text



    async def _check_and_award(self, ctx, user) -> List[str]:
        user_conf = self.config.user(user)
        stats = await user_conf.stats()
        caught = await user_conf.caught()
        earned = await user_conf.achievements()
        messages: List[str] = []

        if stats.get("casts", 0) >= 1 and "first_cast" not in earned:
            m = await self._award_achievement(ctx, user, "first_cast")
            if m:
                messages.append(m)

        # Mythic‐catch: did they ever catch a Mythic?
        if any(self.fish_definitions.get(f,{}).get("rarity") == "Mythic" for f in caught) \
           and "mythic_catch" not in earned:
            m = await self._award_achievement(ctx, user, "mythic_catch")
            if m:
                messages.append(m)

        # Oceanographer: caught every biome?
        try:
            caught_biomes = {self.fish_definitions[f]["biome"]
                             for f in set(caught) if f in self.fish_definitions}
            all_biomes = {info["biome"] for info in self.fish_definitions.values()}
            if all_biomes and caught_biomes >= all_biomes and "oceanographer" not in earned:
                m = await self._award_achievement(ctx, user, "oceanographer")
                if m:
                    messages.append(m)
        except Exception:
            pass                

        if stats.get("fish_caught", 0) >= 1 and "first_fish" not in earned:
            m = await self._award_achievement(ctx, user, "first_fish")
            if m:
                messages.append(m)

        if stats.get("fish_caught", 0) >= 10 and "fish_10" not in earned:
            m = await self._award_achievement(ctx, user, "fish_10")
            if m:
                messages.append(m)

        if stats.get("fish_caught", 0) >= 100 and "fish_100" not in earned:
            m = await self._award_achievement(ctx, user, "fish_100")
            if m:
                messages.append(m)

        unique = len(set(x for x in caught if x and not x.lower().startswith("treasure")))
        if unique >= 5 and "unique_5" not in earned:
            m = await self._award_achievement(ctx, user, "unique_5")
            if m:
                messages.append(m)
        if unique >= 25 and "unique_25" not in earned:
            m = await self._award_achievement(ctx, user, "unique_25")
            if m:
                messages.append(m)

        if stats.get("sell_total", 0) >= 1000 and "sell_1000" not in earned:
            m = await self._award_achievement(ctx, user, "sell_1000")
            if m:
                messages.append(m)

        if stats.get("bait_collected_total", 0) >= 20 and "bait_collector" not in earned:
            m = await self._award_achievement(ctx, user, "bait_collector")
            if m:
                messages.append(m)

        return messages

    async def _inc_stat(self, user, key: str, amount: int = 1):
        conf = self.config.user(user)
        stats = await conf.stats()
        stats[key] = stats.get(key, 0) + amount
        await conf.stats.set(stats)

    async def _maybe_update_unique_and_highest(self, user, fish_name: str):
        conf = self.config.user(user)
        stats = await conf.stats()
        caught = await conf.caught()
        stats["fish_caught"] = stats.get("fish_caught", 0) + 1
        stats["unique_fish"] = len(set(x for x in caught if x and not x.lower().startswith("treasure")))
        price = self.fish_prices.get(fish_name, 0)
        stats["highest_value_catch"] = max(stats.get("highest_value_catch", 0), price)
        stats["consecutive_catches"] = stats.get("consecutive_catches", 0) + 1
        await conf.stats.set(stats)

           
    # ---------- Event handlers ----------
    async def _event_nothing(self, ctx, user_conf):
        stats = await user_conf.stats()
        stats["consecutive_catches"] = 0
        await user_conf.stats.set(stats)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "…No bites this time. Better luck next cast!"

    async def _event_junk(self, ctx, user_conf):
        junk_items = [
            "an old boot",
            "a tin can",
            "a broken bottle",
            "a soggy hat",
            "a rusty key",
            "a tangle of seaweed",
            "a fish skeleton",
        ]
        item = random.choice(junk_items)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, f"👎 You pulled up {item}. Better luck next time!"

    async def _event_fish(self, ctx, user_conf):
        catch = self._random_fish()
        data = await user_conf.caught()
        data.append(catch)
        await user_conf.caught.set(data)
        await self._maybe_update_unique_and_highest(ctx.author, catch)
        await self._inc_stat(ctx.author, "casts", 1)
        await self._advance_quest_on_catch(ctx.author, catch)
        msgs = await self._check_and_award(ctx, ctx.author)
        info = self.fish_definitions[catch]
        base = f"{info['emoji']} You caught a **{catch}** ({info['rarity']})!"
        if msgs:
            return False, base + "\n\n" + "\n".join(msgs)
        return False, base

    async def _event_double(self, ctx, user_conf):
        catch1 = self._random_fish()
        catch2 = self._random_fish()
        data = await user_conf.caught()
        data.extend([catch1, catch2])
        await user_conf.caught.set(data)
        await self._maybe_update_unique_and_highest(ctx.author, catch1)
        await self._maybe_update_unique_and_highest(ctx.author, catch2)
        await self._inc_stat(ctx.author, "casts", 1)
        await self._advance_quest_on_catch(ctx.author, catch1)
        await self._advance_quest_on_catch(ctx.author, catch2)
        msg_ach = None
        if not await self._has_achievement(ctx.author, "double_catch"):
            msg_ach = await self._award_achievement(ctx, ctx.author, "double_catch")
        info1 = self.fish_definitions[catch1]
        info2 = self.fish_definitions[catch2]
        base = f"{info1['emoji']}{info2['emoji']} Double catch! You got **{catch1}** and **{catch2}**!"
        other_msgs = await self._check_and_award(ctx, ctx.author)
        parts = [base]
        if msg_ach:
            parts.append(msg_ach)
        if other_msgs:
            parts.extend(other_msgs)
        return False, "\n\n".join(parts)

    async def _event_shark(self, ctx, user_conf):
        data = await user_conf.caught()
        if data:
            lost = data.pop()
            await user_conf.caught.set(data)
            await self._inc_stat(ctx.author, "casts", 1)
            stats = await user_conf.stats()
            stats["consecutive_catches"] = 0
            await user_conf.stats.set(stats)
            return False, f"🦈 A shark snatches your **{lost}**! Ouch."
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "🦈 A shark swims by, but you had nothing yet to lose."

    async def _event_break(self, ctx, user_conf):
        await user_conf.rod_broken.set(True)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "Snap! Your rod just broke. You’ll need to repair it."

    async def _event_treasure(self, ctx, user_conf):
        coins = random.randint(10, 60)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        await self._inc_stat(ctx.author, "casts", 1)
        # small chance for rod fragment
        if random.random() < 0.06:
            items = await user_conf.items()
            items.append("Rod Fragment")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "fragment_collector"):
                items_now = await user_conf.items()
                if items_now.count("Rod Fragment") >= 10:
                    await self._award_achievement(ctx, ctx.author, "fragment_collector")
        except Exception:
            pass
            fragmsg = " You also find a **Rod Fragment** among the loot!"
        else:
            fragmsg = ""
        msg_ach = None
        if not await self._has_achievement(ctx.author, "treasure_hunter"):
            msg_ach = await self._award_achievement(ctx, ctx.author, "treasure_hunter")
        base = f"🎁 You hauled up a treasure chest and got **{coins} {currency}**! Your new balance is **{new_bal} {currency}**.{fragmsg}"
        if msg_ach:
            return False, base + "\n\n" + msg_ach
        return False, base

    async def _event_bottle(self, ctx, user_conf):
        coins = random.randint(5, 30)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, f"📜 You found a message in a bottle and earned **{coins} {currency}**! Your new balance is **{new_bal} {currency}**."

    async def _event_storm(self, ctx, user_conf):
        if random.random() < 0.2:
            await user_conf.rod_broken.set(True)
            await self._inc_stat(ctx.author, "casts", 1)
            return False, "⛈️ A sudden storm! Your line snaps back and your rod breaks."
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "⛈️ A sudden storm! Your line snaps back with nothing to show."

    async def _event_net(self, ctx, user_conf):
        net_fish_count = random.randint(1, 5)
        caught = [self._random_fish() for _ in range(net_fish_count)]
        data = await user_conf.caught()
        data.extend(caught)
        await user_conf.caught.set(data)
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.08:
            items = await user_conf.items()
            items.append("Rod Fragment")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "fragment_collector"):
                items_now = await user_conf.items()
                if items_now.count("Rod Fragment") >= 10:
                    await self._award_achievement(ctx, ctx.author, "fragment_collector")
        except Exception:
            pass            
            found = " You also find a **Rod Fragment** tangled in the net."
        else:
            found = ""
        names = ", ".join(caught)
        for f in caught:
            await self._advance_quest_on_catch(ctx.author, f)
        return False, f"🕸️ You snagged an old net with {net_fish_count} things tangled inside: {names}.{found}"

    async def _event_bait_find(self, ctx, user_conf):
        bait_found = random.randint(1, 5)
        current_bait = await user_conf.bait()
        await user_conf.bait.set(current_bait + bait_found)
        await self._inc_stat(ctx.author, "casts", 1)
        stats = await user_conf.stats()
        stats["bait_collected_total"] = stats.get("bait_collected_total", 0) + bait_found
        await user_conf.stats.set(stats)
        msgs = []
        if stats["bait_collected_total"] >= 20 and not await self._has_achievement(ctx.author, "bait_collector"):
            m = await self._award_achievement(ctx, ctx.author, "bait_collector")
            if m:
                msgs.append(m)
        base = f"🪱 You found **{bait_found}** bait in the mud. You now have **{current_bait + bait_found}** bait."
        if msgs:
            return False, base + "\n\n" + "\n".join(msgs)
        return False, base

    async def _event_lucky_streak(self, ctx, user_conf):
        await user_conf.luck.set(5)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "✨ Lucky streak! Your next few casts are more likely to find rare fish."

    async def _event_curse(self, ctx, user_conf):
        if random.random() < 0.5:
            loss = random.randint(5, 25)
            bal = await bank.get_balance(ctx.author)
            if bal >= loss:
                await bank.withdraw_credits(ctx.author, loss)
                currency = await bank.get_currency_name(ctx.guild)
                await self._inc_stat(ctx.author, "casts", 1)
                return False, f"🔮 An old charm curses you — you lost **{loss} {currency}**."
        await user_conf.rod_broken.set(True)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "🔮 A cursed tug! Your rod is damaged by some dark force."

    async def _event_merchant(self, ctx, user_conf):
        inventory = await user_conf.caught()
        await self._inc_stat(ctx.author, "casts", 1)
        if not inventory:
            tips = random.randint(1, 10)
            new_bal, currency = await self._deposit(ctx.author, tips, ctx)
            return False, f"🧑‍🚀 A traveling merchant stops by and leaves **{tips} {currency}** as thanks."
        fish = random.choice(inventory)
        premium = int(self.fish_prices.get(fish, 10) * random.uniform(1.2, 2.0))
        inventory.remove(fish)
        await user_conf.caught.set(inventory)
        new_bal, currency = await self._deposit(ctx.author, premium, ctx)
        return False, f"🧑‍🚀 A merchant offers **{premium} {currency}** for your **{fish}** and buys it on the spot. New balance: **{new_bal} {currency}**."

    async def _event_pearl(self, ctx, user_conf):
        value = random.randint(50, 150)
        new_bal, currency = await self._deposit(ctx.author, value, ctx)
        await self._inc_stat(ctx.author, "casts", 1)
        msg_ach = None
        if not await self._has_achievement(ctx.author, "pearl_finder"):
            msg_ach = await self._award_achievement(ctx, ctx.author, "pearl_finder")
        base = f"💎 You found a lustrous pearl worth **{value} {currency}**. Your new balance is **{new_bal} {currency}**."
        if msg_ach:
            return False, base + "\n\n" + msg_ach
        return False, base

    async def _event_map(self, ctx, user_conf):
        items = await user_conf.items()
        items.append("Treasure Map")
        await user_conf.items.set(items)
        await self._inc_stat(ctx.author, "casts", 1)
        if not await self._has_achievement(ctx.author, "map_collector"):
            msg = await self._award_achievement(ctx, ctx.author, "map_collector")
            if msg:
                return False, "🗺️ You found a Treasure Map! Use it later to start a treasure hunt.\n\n" + msg
        return False, "🗺️ You found a Treasure Map! Use it later to start a treasure hunt."

    async def _event_sea_monster(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.5:
            data = await user_conf.caught()
            lost = []
            for _ in range(min(3, len(data))):
                lost.append(data.pop(random.randrange(len(data))))
            await user_conf.caught.set(data)
            return False, f"🪸 A sea monster thrashes by and steals: {', '.join(lost)}! Escape barely."
        else:
            rare = self._random_fish()
            data = await user_conf.caught()
            data.append(rare)
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, rare)
            if not await self._has_achievement(ctx.author, "sea_monster_survivor"):
                msg = await self._award_achievement(ctx, ctx.author, "sea_monster_survivor")
                if msg:
                    return False, f"🪸 You managed to hook a **{rare}** from the sea monster's grip!\n\n{msg}"
            return False, f"🪸 You managed to hook a **{rare}** from the sea monster's grip!"

    async def _event_hook_snag(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.6:
            await user_conf.rod_broken.set(True)
            return False, "⛓️ Your hook snagged on something sharp and your rod snapped!"
        return False, "⛓️ Your hook snagged on an old anchor but you freed it."

    async def _event_festival(self, ctx, user_conf):
        await user_conf.luck.set(3)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "🎉 Festival of Fishermen! Sold fish pay more for a short while."

    async def _event_charity(self, ctx, user_conf):
        bal = await bank.get_balance(ctx.author)
        donation = min(random.randint(1, 10), bal)
        if donation > 0:
            await bank.withdraw_credits(ctx.author, donation)
            currency = await bank.get_currency_name(ctx.guild)
            await self._inc_stat(ctx.author, "casts", 1)
            return False, f"🤝 You gave **{donation} {currency}** to a community cause."
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "🤝 You feel generous but have no funds to donate."

    async def _event_salvage(self, ctx, user_conf):
        coins = random.randint(5, 40)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        await self._inc_stat(ctx.author, "casts", 1)
        r = random.random()
        if r < 0.03:
            items = await user_conf.items()
            items.append("Rod Core")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "core_seeker"):
                await self._award_achievement(ctx, ctx.author, "core_seeker")
        except Exception:
            pass            
            return False, f"🛠️ You salvage rare parts, get **{coins} {currency}** and a **Rod Core**!"
        if r < 0.10:
            items = await user_conf.items()
            items.append("Rod Fragment")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "fragment_collector"):
                items_now = await user_conf.items()
                if items_now.count("Rod Fragment") >= 10:
                    await self._award_achievement(ctx, ctx.author, "fragment_collector")
        except Exception:
            pass            
            return False, f"🛠️ You salvage pieces, get **{coins} {currency}** and a **Rod Fragment**!"
        if random.random() < 0.15:
            data = await user_conf.caught()
            data.append("Treasure Map")
            await user_conf.caught.set(data)
            return False, f"🛠️ You salvage usable pieces and find **{coins} {currency}** and a Treasure Map!"
        return False, f"🛠️ You salvage metal and get **{coins} {currency}**."

    async def _event_message(self, ctx, user_conf):
        if random.random() < 0.5:
            bait = random.randint(1, 3)
            current = await user_conf.bait()
            await user_conf.bait.set(current + bait)
            await self._inc_stat(ctx.author, "casts", 1)
            return False, f"✉️ A friendly note contains **{bait}** bait. Use it to attract better fish."
            coins = random.randint(5, 20)
            new_bal, currency = await self._deposit(ctx.author, coins, ctx)
            await self._inc_stat(ctx.author, "casts", 1)
            return False, f"✉️ You find **{coins} {currency}** tucked in a note. New balance: **{new_bal} {currency}**."
            
    async def _event_bubble_burst(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.25:
            # small fish
            catch = self._random_fish()
            data = await user_conf.caught()
            data.append(catch)
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, catch)
            return False, f" bubbles! You spot a small fish and catch a **{catch}**!"
        else:
            bait = random.randint(1, 2)
            current = await user_conf.bait()
            await user_conf.bait.set(current + bait)
            return False, f" Bubbles reveal some bait. You found **{bait}** bait."

    async def _event_kelp_tangle(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.15:
            data = await user_conf.caught()
            data.append("Seagrass Fish")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Seagrass Fish")
            return False, "🪴 Your line tangles in kelp but you free a **Seagrass Fish**!"
        return False, "🪴 Your line gets tangled in kelp — nothing worth keeping this time."

    async def _event_whale_song(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        await user_conf.luck.set((await user_conf.luck()) + 3)
        return False, "🐋 A whale sings — your luck rises for a few casts."

    async def _event_siren_call(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        r = random.random()
        if r < 0.12:
            # mythic reward
            catch = self._random_fish()
            data = await user_conf.caught()
            data.append(catch)
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, catch)
            return False, f"🧜 A siren lures something incredible — you catch a **{catch}**!"
        if r < 0.35:
            # lose an item
            items = await user_conf.items()
            if items:
                lost = items.pop(random.randrange(len(items)))
                await user_conf.items.set(items)
                return False, f"🧜 A siren's song steals **{lost}** from you!"
        return False, "🧜 A haunting song passes by. You steady the line and move on."

    async def _event_tide_pool(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        count = random.randint(2, 5)
        caught = [self._random_fish() for _ in range(count)]
        data = await user_conf.caught()
        data.extend(caught)
        await user_conf.caught.set(data)
        for c in caught:
            await self._maybe_update_unique_and_highest(ctx.author, c)
        return False, f"🌊 You explore a tide pool and net {len(caught)} fish: {', '.join(caught)}."

    async def _event_meteor_shower(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.10:
            # celestial fish
            data = await user_conf.caught()
            data.append("Star Pike")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Star Pike")
            return False, "☄️ Meteor light guides you to a **Star Pike**!"
        else:
            coins = random.randint(10, 50)
            new_bal, currency = await self._deposit(ctx.author, coins, ctx)
            return False, f"☄️ Falling sparks wash ashore coins — you get **{coins} {currency}**."

    async def _event_coral_gift(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.25:
            items = await user_conf.items()
            items.append("Coral Trinket")
            await user_conf.items.set(items)
            return False, "🪸 The coral cradles a **Coral Trinket** and gives it to you."
        coins = random.randint(5, 25)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        return False, f"🪸 Tiny coral pieces yield **{coins} {currency}**."

    async def _event_water_sprite(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.5:
            bait = random.randint(1, 3)
            current = await user_conf.bait()
            await user_conf.bait.set(current + bait)
            return False, f"🧚 A water sprite blesses you with **{bait}** bait."
        await user_conf.luck.set((await user_conf.luck()) + 1)
        return False, "🧚 A sprite whispers. Your luck increases slightly."

    async def _event_whirlpool(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        data = await user_conf.caught()
        if data:
            lost = []
            lost_count = min(random.randint(1, 3), len(data))
            for _ in range(lost_count):
                lost.append(data.pop(random.randrange(len(data))))
            await user_conf.caught.set(data)
            return False, f"🌀 A whirlpool swallows {', '.join(lost)} from your haul!"
        return False, "🌀 A whirlpool churns but you had nothing to lose."

    async def _event_fisherman_friend(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        inv = await user_conf.caught()
        if not inv:
            coins = random.randint(1, 8)
            new_bal, currency = await self._deposit(ctx.author, coins, ctx)
            return False, f"🧑‍⚖️ A helpful fisherman tips you **{coins} {currency}**."
        fish = random.choice(inv)
        premium = int(self.fish_prices.get(fish, 10) * random.uniform(1.4, 2.5))
        inv.remove(fish)
        await user_conf.caught.set(inv)
        new_bal, currency = await self._deposit(ctx.author, premium, ctx)
        return False, f"🧑‍⚖️ A friendly fisherman buys your **{fish}** for **{premium} {currency}** on the spot."

    async def _event_barnacle_pearl(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.12:
            value = random.randint(30, 120)
            new_bal, currency = await self._deposit(ctx.author, value, ctx)
            return False, f"🐚 You pry open a barnacle and find a pearl worth **{value} {currency}**!"
        return False, "🐚 Barnacles cling to nothing of value this time."

    async def _event_crystal_wash(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.10:
            data = await user_conf.caught()
            data.append("Crystal Trout")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Crystal Trout")
            return False, "🔹 A crystal wash frees a **Crystal Trout** into your net!"
        return False, "🔹 Shimmering water passes but nothing uncommon shows."

    async def _event_echo_call(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.5:
            await user_conf.luck.set((await user_conf.luck()) + 2)
            return False, "🔔 Echoes call — your next casts are luckier."
        return False, "🔔 You hear distant echoes; nothing else."

    async def _event_drifting_crate(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        coins = random.randint(5, 40)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        items = await user_conf.items()
        if random.random() < 0.10:
            items.append("Rod Fragment")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "fragment_collector"):
                items_now = await user_conf.items()
                if items_now.count("Rod Fragment") >= 10:
                    await self._award_achievement(ctx, ctx.author, "fragment_collector")
        except Exception:
            pass            
            return False, f"📦 You pull a drifting crate with **{coins} {currency}** and a **Rod Fragment**!"
        return False, f"📦 You open a drifting crate and find **{coins} {currency}**."

    async def _event_phantom_net(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.08:
            data = await user_conf.caught()
            data.append("Spectral Herring")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Spectral Herring")
            return False, "👻 A ghostly net yields a **Spectral Herring**!"
        return False, "👻 An old phantom net drops off a tangle of junk."

    async def _event_lazy_sun(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        await user_conf.luck.set((await user_conf.luck()) + 1)
        return False, "☀️ The sun is calm — common and uncommon fish are more likely."

    async def _event_thunder_clap(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        # reduce luck briefly but maybe rare storm fish
        if random.random() < 0.08:
            data = await user_conf.caught()
            data.append("Stormwing Tuna")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Stormwing Tuna")
            return False, "⚡ A thunderclap unleashes a **Stormwing Tuna**!"
        # small luck penalty
        await user_conf.luck.set(max(0, (await user_conf.luck()) - 1))
        return False, "⚡ A thunderclap startles the water; luck reduced slightly."

    async def _event_sponge_cache(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        bait_found = random.randint(1, 3)
        current = await user_conf.bait()
        await user_conf.bait.set(current + bait_found)
        if random.random() < 0.06:
            items = await user_conf.items()
            items.append("Rod Fragment")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "fragment_collector"):
                items_now = await user_conf.items()
                if items_now.count("Rod Fragment") >= 10:
                    await self._award_achievement(ctx, ctx.author, "fragment_collector")
        except Exception:
            pass            
            return False, f"🧽 A sponge cache yields **{bait_found}** bait and a **Rod Fragment**!"
        return False, f"🧽 A sponge cache yields **{bait_found}** bait."

    async def _event_tide_change(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        # temporarily give player a small luck boost and message; actual biome weighting handled elsewhere if implemented
        await user_conf.luck.set((await user_conf.luck()) + 1)
        return False, "🌊 The tide changes — coastal/reef spawns feel stronger for a short time."

    async def _event_moon_phase(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.05:
            data = await user_conf.caught()
            data.append("Silver Seraph")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Silver Seraph")
            return False, "🌕 Under the moon's eye you catch a **Silver Seraph**!"
        return False, "🌕 The moon glances off the water — a quiet, promising night."

    async def _event_rift_glimpse(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.03:
            data = await user_conf.caught()
            data.append("Abyssal Wisp")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Abyssal Wisp")
            return False, "🔱 A rift glimpse draws forth an **Abyssal Wisp**!"
        return False, "🔱 You glimpse a rift far below; nothing pulled up this time."
        
    async def _paginate_embeds(self, ctx, embeds: List[discord.Embed], timeout: float = 120.0):
        """Show embeds with reaction pagination controlled by the invoking user."""
        if not embeds:
            return await ctx.send("Nothing to show.")
        message = await ctx.send(embed=embeds[0])
        if len(embeds) == 1:
            return message
        controls = ["⏮️", "⬅️", "⏹️", "➡️", "⏭️"]
        for r in controls:
            try:
                await message.add_reaction(r)
            except Exception:
                break
        current = 0

        def check(reaction, user):
            return (
                reaction.message.id == message.id
                and user.id == ctx.author.id
                and str(reaction.emoji) in controls
            )

        while True:
            try:
                reaction, user = await ctx.bot.wait_for("reaction_add", timeout=timeout, check=check)
            except asyncio.TimeoutError:
                try:
                    await message.clear_reactions()
                except Exception:
                    pass
                break

            emoji = str(reaction.emoji)
            try:
                await message.remove_reaction(reaction.emoji, user)
            except Exception:
                pass

            if emoji == "⏹️":
                try:
                    await message.clear_reactions()
                except Exception:
                    pass
                break
            elif emoji == "⬅️":
                current = (current - 1) % len(embeds)
                try:
                    await message.edit(embed=embeds[current])
                except Exception:
                    pass
            elif emoji == "➡️":
                current = (current + 1) % len(embeds)
                try:
                    await message.edit(embed=embeds[current])
                except Exception:
                    pass
            elif emoji == "⏮️":
                current = 0
                try:
                    await message.edit(embed=embeds[current])
                except Exception:
                    pass
            elif emoji == "⏭️":
                current = len(embeds) - 1
                try:
                    await message.edit(embed=embeds[current])
                except Exception:
                    pass
        return message

    # ---------- Core fish command ----------
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command()
    @award_achievements
    async def fish(self, ctx):
    
        user_conf = self.config.user(ctx.author)
        # … rod‐broken check …

        waiting_msg = await ctx.send("🎣 You cast your line and wait patiently…")
        await asyncio.sleep(random.uniform(1.5, 5.5))

        # use pre-cached lists instead of rebuilding every time
        keys    = self._event_keys
        weights = self._event_base_weights.copy()

        # bait modifier (your existing code)
        try:
            bait_amount = await user_conf.bait()
        except Exception:
            bait_amount = 0

        if bait_amount > 0:
            if random.random() < 0.9:
                await user_conf.bait.set(bait_amount - 1)
            for i, event in enumerate(keys):
                if event in ("fish", "double"):
                    weights[i] = int(weights[i] * 1.6)

        # luck modifier
        try:
            luck = await user_conf.luck()
        except Exception:
            luck = 0
        if luck and luck > 0:
            await user_conf.luck.set(max(0, luck - 1))
            for i, k in enumerate(keys):
                if k in ("fish", "double", "treasure", "pearl", "merchant"):
                    weights[i] = int(weights[i] * 2)

        # rod level modifier
        try:
            rod_level = await user_conf.rod_level()
        except Exception:
            rod_level = 0
        fish_mult = self.rod_level_fish_multiplier.get(rod_level, 1.0)
        break_reduc = self.rod_level_break_reduction.get(rod_level, 1.0)
        for i, k in enumerate(keys):
            if k in ("fish", "double", "treasure", "pearl", "merchant"):
                weights[i] = int(weights[i] * fish_mult)
            if k in ("break", "hook_snag"):
                weights[i] = max(1, int(weights[i] * break_reduc))

        weights = [max(1, w) for w in weights]
        chosen = random.choices(keys, weights=weights, k=1)[0]
        handler = self.event_handlers[chosen][0]

        try:
            result = await handler(ctx, user_conf)
        except Exception:
            try:
                await waiting_msg.edit(content="⚠️ An error occurred while resolving the event.")
            except Exception:
                pass
            raise

        message = None
        # pull out the content string
        if isinstance(result, tuple) and len(result) >= 2:
            message = result[1]
        elif isinstance(result, str):
            message = result
        else:
            message = None
             
        if message is not None:
            ach_msgs = await self._check_and_award(ctx, ctx.author)
            if ach_msgs:
                # append any newly unlocked achievements
                message = message + "\n\n" + "\n".join(ach_msgs)             
             
        try:
            if message:
                if len(message) > 1900:
                    message = message[:1897] + "..."
                await waiting_msg.edit(content=message)
            else:
                await waiting_msg.edit(content="…An event occurred. See the channel for details.")
        except Exception:
            if message:
                await ctx.send(message)

    # ---------- fishlist with embed pagination ----------
    @commands.command()
    async def fishlist(self, ctx, *, filter_by: str = None):
        """Show available fish with price and rarity in a paged embed."""
        rarity_order = {"Common": 0, "Uncommon": 1, "Rare": 2, "Epic": 3, "Legendary": 4, "Mythic": 5, "Boss": 6}
        items = list(self.fish_definitions.items())

        if filter_by:
            key = filter_by.strip().lower()
            filtered = []
            for name, info in items:
                if info.get("rarity", "").lower() == key:
                    filtered.append((name, info)); continue
                if key in (info.get("biome", "").lower()):
                    filtered.append((name, info)); continue
                if key in name.lower():
                    filtered.append((name, info))
            items = filtered

        items = sorted(items, key=lambda kv: (rarity_order.get(kv[1].get("rarity", ""), 99), -kv[1].get("price", 0)))

        if not items:
            return await ctx.send("No fish match that filter.")

        per_page = 8
        pages: List[List[Tuple[str, Dict]]] = [items[i:i+per_page] for i in range(0, len(items), per_page)]

        def make_embed(page_idx: int):
            page_items = pages[page_idx]
            embed = discord.Embed(title="Available Fish", colour=discord.Colour.blue())
            embed.set_thumbnail(url="https://files.catbox.moe/yl5ytl.png")
            if filter_by:
                embed.description = f"Filter: **{filter_by}**"
            for name, info in page_items:
                emoji = info.get("emoji", "")
                rarity = info.get("rarity", "Unknown")
                price = info.get("price", 0)
                biome = info.get("biome", "")
                embed.add_field(
                    name=f"{emoji} {name}",
                    value=f"**Rarity:** {rarity}\n**Price:** {price}\n**Biome:** {biome}",
                    inline=False,
                )
            embed.set_footer(text=f"Page {page_idx+1}/{len(pages)} — Use reactions to navigate")
            return embed

        message = await ctx.send(embed=make_embed(0))
        if len(pages) == 1:
            return

        left = "⬅️"; right = "➡️"; first = "⏮️"; last = "⏭️"; stop = "⏹️"
        controls = [first, left, stop, right, last]
        for r in controls:
            try:
                await message.add_reaction(r)
            except Exception:
                return

        current = 0

        def check(reaction, user):
            return (
                reaction.message.id == message.id
                and user.id == ctx.author.id
                and str(reaction.emoji) in controls
            )

        while True:
            try:
                reaction, user = await ctx.bot.wait_for("reaction_add", timeout=120.0, check=check)
            except asyncio.TimeoutError:
                try:
                    await message.clear_reactions()
                except Exception:
                    pass
                break

            try:
                await message.remove_reaction(reaction.emoji, user)
            except Exception:
                pass

            emoji = str(reaction.emoji)
            if emoji == stop:
                try:
                    await message.clear_reactions()
                except Exception:
                    pass
                break
            elif emoji == left:
                current = (current - 1) % len(pages)
                try:
                    await message.edit(embed=make_embed(current))
                except Exception:
                    pass
            elif emoji == right:
                current = (current + 1) % len(pages)
                try:
                    await message.edit(embed=make_embed(current))
                except Exception:
                    pass
            elif emoji == first:
                current = 0
                try:
                    await message.edit(embed=make_embed(current))
                except Exception:
                    pass
            elif emoji == last:
                current = len(pages) - 1
                try:
                    await message.edit(embed=make_embed(current))
                except Exception:
                    pass

    # ---------- fishstats, achievements, repairrod, sell ----------
    @commands.command()
    async def fishstats(self, ctx):
        """View how many fish you’ve caught, your items, and your bank balance (embed)."""
        data = await self.config.user(ctx.author).all()
        image_url = "https://files.catbox.moe/w2zsia.png"
        bait = data["bait"]
        caught = data["caught"]
        if not caught:
            return await ctx.send(f"You haven't caught anything yet. Use `{ctx.clean_prefix}fish` to start fishing!")
        counts = {}
        for fish in caught:
            counts[fish] = counts.get(fish, 0) + 1
        emb = discord.Embed(title=f"{ctx.author.display_name}'s Fishing Stats", colour=discord.Colour.blue())
        bal = await bank.get_balance(ctx.author)
        currency = await bank.get_currency_name(ctx.guild)
        emb.set_thumbnail(url=image_url)
        emb.add_field(name="Balance", value=f"**{bal}** {currency}", inline=False)
        # fish breakdown
        breakdown = "\n".join(f"• {self.fish_definitions.get(fish, {}).get('emoji','')} {fish}: {count}" for fish, count in counts.items())
        emb.add_field(name="Caught", value=breakdown or "None", inline=False)
        emb.add_field(name="Bait", value=str(bait), inline=True)
        items = await self.config.user(ctx.author).items()
        if items:
            inv_counts = {}
            for it in items:
                inv_counts[it] = inv_counts.get(it, 0) + 1
            itemline = "\n".join(f"• {iname}: {count}" for iname, count in inv_counts.items())
            emb.add_field(name="Items", value=itemline, inline=False)
        await ctx.send(embed=emb)


    @commands.command()
    async def achievements(self, ctx):
        """Show your earned achievements and progress in an embed (paged if long)."""
        user_conf = self.config.user(ctx.author)
        earned = await user_conf.achievements()
        image_url = "https://files.catbox.moe/fldzkv.png"        
        stats = await user_conf.stats()
        caught = await user_conf.caught()
        lines = []
        if earned:
            for aid in earned:
                name, desc, _ = self.achievements.get(aid, (aid, "", ""))
                lines.append((f"🏆 {name}", desc))
        else:
            lines.append(("No achievements yet", "You haven't earned any achievements yet."))

        # progress fields
        progress_fields = [
            ("Total casts", str(stats.get("casts", 0))),
            ("Fish caught", str(stats.get("fish_caught", 0))),
            ("Unique species", str(len(set(x for x in caught if x and not x.lower().startswith("treasure"))))),
            ("Sell total", str(stats.get("sell_total", 0))),
        ]

        embeds: List[discord.Embed] = []
        per_embed = 6
        for i in range(0, len(lines), per_embed):
            chunk = lines[i:i+per_embed]
            emb = discord.Embed(title=f"{ctx.author.display_name}'s Achievements", colour=discord.Colour.gold())
            for name, desc in chunk:
                emb.add_field(name=name, value=desc, inline=False)
            # attach progress to last embed
            if i + per_embed >= len(lines):
                for pname, pval in progress_fields:
                    emb.add_field(name=pname, value=pval, inline=True)
                    emb.set_thumbnail(url=image_url)
            emb.set_footer(text=f"Page {i//per_embed+1}/{(len(lines)-1)//per_embed+1}")
            embeds.append(emb)
        await self._paginate_embeds(ctx, embeds)

    @commands.command()
    async def achievementlist(self, ctx):
        """Show all achievements and their descriptions in an embed (paged)."""
        items = list(self.achievements.items())
        image_url = "https://files.catbox.moe/6ay32m.png"
        embeds: List[discord.Embed] = []
        per_page = 8
        for i in range(0, len(items), per_page):
            chunk = items[i:i+per_page]
            emb = discord.Embed(title="All Achievements", colour=discord.Colour.dark_gold())
            emb.set_image(url=image_url)
            for aid, (name, desc, cat) in chunk:
                emb.add_field(name=f"{name} [{cat}]", value=f"{desc} — id: `{aid}`", inline=False)
            emb.set_footer(text=f"Page {i//per_page+1}/{(len(items)-1)//per_page+1}")
            embeds.append(emb)
        await self._paginate_embeds(ctx, embeds)


    @commands.command()
    async def repairrod(self, ctx):
        """Repair your broken rod for 20 coins and award achievement."""
        user_conf = self.config.user(ctx.author)
        if not await user_conf.rod_broken():
            return await ctx.send("Your rod is already in good shape!")
        cost = 20
        if not await bank.can_spend(ctx.author, cost):
            bal = await bank.get_balance(ctx.author)
            currency = await bank.get_currency_name(ctx.guild)
            return await ctx.send(
                f"❌ You need **{cost}** {currency} to repair, but you only have **{bal}** {currency}."
            )
        await bank.withdraw_credits(ctx.author, cost)
        await user_conf.rod_broken.set(False)
        ach_msg = None
        if not await self._has_achievement(ctx.author, "rod_repaired"):
            ach_msg = await self._award_achievement(ctx, ctx.author, "rod_repaired")
        if ach_msg:
            await ctx.send("🔧 Your rod is repaired! " + ach_msg)
        else:
            await ctx.send("🔧 Your rod is repaired! Time to cast again.")

    @commands.command()
    async def sell(self, ctx, amount: int, *, fish_name: str):
        """Sell a number of fish for your server currency."""
        user_conf = self.config.user(ctx.author)
        inventory = await user_conf.caught()
        match = next((fish for fish in self.fish_definitions if fish.lower() == fish_name.lower()), None)
        if not match:
            valid = ", ".join(self.fish_definitions.keys())
            return await ctx.send(f"❌ Unknown fish `{fish_name}`. You can sell: {valid}")
        have = inventory.count(match)
        if have < amount:
            return await ctx.send(f"❌ You only have {have}× **{match}** to sell.")
        for _ in range(amount):
            inventory.remove(match)
        await user_conf.caught.set(inventory)
        total = self.fish_definitions[match]["price"] * amount
        new_bal = await bank.deposit_credits(ctx.author, total)
        currency = await bank.get_currency_name(ctx.guild)
        stats = await user_conf.stats()
        stats["sell_total"] = stats.get("sell_total", 0) + total
        await user_conf.stats.set(stats)
        msgs = await self._check_and_award(ctx, ctx.author)
        message = f"💰 You sold {amount}× **{match}** for **{total}** {currency}!\nYour new balance is **{new_bal} {currency}**."
        if msgs:
            message += "\n\n" + "\n".join(msgs)
        await ctx.send(message)

    # ---------- Crafting (fish fusion) ----------
    @commands.command()
    async def craftlist(self, ctx):
        """List available crafting recipes in embeds (paged), showing the full command to use."""
        image_url = "https://files.catbox.moe/dt1sh1.png"
        items = list(self.crafting_recipes.items())
        embeds: List[discord.Embed] = []
        per_page = 6

        for i in range(0, len(items), per_page):
            chunk = items[i:i+per_page]
            emb = discord.Embed(
                title="Crafting Recipes",
                colour=discord.Colour.teal()
            )
            emb.set_thumbnail(url=image_url)

            for recipe_id, info in chunk:
                # build requirements string
                reqs = info.get("requirements", {})
                req_text = ", ".join(f"{k}:{v}" for k, v in reqs.items()) or "None"
                # build result string
                result = info.get("result", {})
                # field title shows the human name and exact command
                field_name = (
                    f"{info.get('name')} — Usage: "
                    f"`{ctx.clean_prefix}craft {recipe_id}`"
                )
                # field value shows description, requirements and result
                field_value = (
                    f"{info.get('description')}\n"
                    f"**Requires:** {req_text}\n"
                    f"**Result:** {result}"
                )
                emb.add_field(name=field_name, value=field_value, inline=False)

            emb.set_footer(
                text=f"Page {i//per_page+1}/{(len(items)-1)//per_page+1}"
            )
            embeds.append(emb)

        await self._paginate_embeds(ctx, embeds)


    @commands.command()
    async def craft(self, ctx, recipe_id: str):
        """Craft an item using a recipe id. Use `craftlist` to see available recipes."""
        recipe_id = recipe_id.lower()
        if recipe_id not in self.crafting_recipes:
            return await ctx.send("❌ Unknown recipe. Use `craftlist` to view available recipes.")
        recipe = self.crafting_recipes[recipe_id]
        reqs = recipe["requirements"]
        user_conf = self.config.user(ctx.author)
        inventory = await user_conf.caught()
        remaining_inv = list(inventory)
        removed_fish = []

        ok = True
        for key, needed in reqs.items():
            if key == "any_fish":
                if len(remaining_inv) < needed:
                    ok = False
                    break
                remaining_inv.sort(key=lambda n: self.fish_definitions.get(n, {}).get("price", 0))
                for _ in range(needed):
                    removed_fish.append(remaining_inv.pop(0))
            elif key.startswith("rarity:"):
                rarity = key.split(":", 1)[1]
                have = sum(1 for f in remaining_inv if f in self.fish_definitions and self.fish_definitions[f].get("rarity") == rarity)
                if have < needed:
                    ok = False
                    break
                to_remove = needed
                new_rem = []
                for f in remaining_inv:
                    if to_remove > 0 and f in self.fish_definitions and self.fish_definitions[f].get("rarity") == rarity:
                        removed_fish.append(f)
                        to_remove -= 1
                        continue
                    new_rem.append(f)
                remaining_inv = new_rem
            elif key.startswith("fish:"):
                fname = key.split(":", 1)[1]
                have = remaining_inv.count(fname)
                if have < needed:
                    ok = False
                    break
                removed = 0
                new_rem = []
                for f in remaining_inv:
                    if f == fname and removed < needed:
                        removed_fish.append(f)
                        removed += 1
                        continue
                    new_rem.append(f)
                remaining_inv = new_rem
            else:
                ok = False
                break

        if not ok:
            return await ctx.send("❌ You don't have the necessary fish/items to craft that recipe.")

        await user_conf.caught.set(remaining_inv)
        result = recipe["result"]
        messages = []
        if "coins" in result:
            amt = int(result["coins"])
            new_bal, currency = await self._deposit(ctx.author, amt, ctx)
            messages.append(f"🏆 Craft successful: **{recipe['name']}** — you received **{amt} {currency}**! New balance: **{new_bal} {currency}**.")
        if "item" in result:
            items = await user_conf.items()
            items.append(result["item"])
            await user_conf.items.set(items)
            messages.append(f"🔧 Craft successful: **{recipe['name']}** — you received **{result['item']}**.")
        if "items" in result:
            items_cfg = await user_conf.items()
            for iname, count in result["items"].items():
                for _ in range(count):
                    items_cfg.append(iname)
            await user_conf.items.set(items_cfg)
            added = ", ".join(f"{c}× {n}" for n, c in result["items"].items())
            messages.append(f"🔧 Craft successful: **{recipe['name']}** — you received {added}.")

        removed_summary = {}
        for r in removed_fish:
            removed_summary[r] = removed_summary.get(r, 0) + 1
        removed_lines = ", ".join(f"{v}× {k}" for k, v in removed_summary.items()) if removed_summary else "None"
        messages.insert(0, f"🛠️ You used: {removed_lines}")
        try:
            if recipe_id == "chum" and not await self._has_achievement(ctx.author, "first_chum"):
                await self._award_achievement(ctx, ctx.author, "first_chum")
            if recipe_id == "trophy" and not await self._has_achievement(ctx.author, "trophy_maker"):
                await self._award_achievement(ctx, ctx.author, "trophy_maker")
        except Exception:
            pass        
        await ctx.send("\n".join(messages))

    @commands.command()
    async def useitem(self, ctx, *, item_name: str):
        """Use a consumable item from your items list (e.g., Chum)."""
        user_conf = self.config.user(ctx.author)
        items = await user_conf.items()
        match = None
        for it in items:
            if it.lower() == item_name.lower():
                match = it
                break
        if not match:
            return await ctx.send(f"❌ You don't have **{item_name}** in your items.")

        if match == "Chum":
            items.remove(match)
            await user_conf.items.set(items)
            current = await user_conf.luck()
            await user_conf.luck.set(current + 3)
            return await ctx.send("🪼 You used **Chum**. Your luck increased by **3** for the next casts.")
        elif match == "Treasure Map":
            # consume the map
            items.remove(match)
            await user_conf.items.set(items)

            # roll your treasure—here: 20–100 coins
            import random
            coins = random.randint(20, 100)
            new_bal, currency = await self._deposit(ctx.author, coins, ctx)
            return await ctx.send(
                f"🗺️ You follow the Treasure Map's clues and dig up a chest containing **{coins} {currency}**! "
                f"Your new balance is **{new_bal} {currency}**."
            )            
        return await ctx.send(f"❌ **{match}** cannot be used directly.")

    # ---------- Rod view and upgrade ----------
    @commands.command()
    async def rod(self, ctx):
        """Show your rod level, fragments, cores and next upgrade requirements (embed + image)."""
        user_conf = self.config.user(ctx.author)
        lvl       = await user_conf.rod_level()
        items     = await user_conf.items()
        fragments = items.count("Rod Fragment")
        cores     = items.count("Rod Core")
        next_req  = self.rod_upgrade_requirements.get(lvl + 1)

        # Build the embed
        emb = discord.Embed(
            title=f"{ctx.author.display_name}'s Rod",
            colour=discord.Colour.orange()
        )
        # Big banner under the title
        emb.set_image(url=ROD_IMAGE_URL)

        # Stats fields
        emb.add_field(name="Rod Level",          value=str(lvl),           inline=True)
        emb.add_field(name="Fragments Collected",value=str(fragments),    inline=True)
        emb.add_field(name="Cores Collected",    value=str(cores),         inline=True)

        # Next upgrade requirements
        if next_req:
            req_text = f"{next_req['fragments']} fragments"
            if next_req.get("coins", 0):
                req_text += f" and {next_req['coins']} coins"
        else:
            req_text = "Max level reached"
        emb.add_field(name="Next Upgrade", value=req_text, inline=False)

        await ctx.send(embed=emb)



    @commands.command()
    async def upgraderod(self, ctx):
        """Upgrade your rod using fragments/cores and (optional) coins."""
        user_conf = self.config.user(ctx.author)
        lvl = await user_conf.rod_level()
        target = lvl + 1
        req = self.rod_upgrade_requirements.get(target)
        if not req:
            return await ctx.send("🔒 Your rod is already at max level.")

        items = await user_conf.items()
        fragments = items.count("Rod Fragment")
        cores = items.count("Rod Core")

        if cores >= 1:
            items.remove("Rod Core")
            await user_conf.items.set(items)
            await user_conf.rod_level.set(target)
            return await ctx.send(f"✨ You used a Rod Core and upgraded your rod to level **{target}**!")

        need_frag = req["fragments"]
        cost = req.get("coins", 0)
        if fragments < need_frag:
            return await ctx.send(f"❌ You need **{need_frag} Rod Fragments** (you have {fragments}).")

        if cost and not await bank.can_spend(ctx.author, cost):
            bal = await bank.get_balance(ctx.author)
            currency = await bank.get_currency_name(ctx.guild)
            return await ctx.send(f"❌ Upgrade costs **{cost} {currency}**, you only have **{bal} {currency}**.")

        removed = 0
        new_items = []
        for it in items:
            if it == "Rod Fragment" and removed < need_frag:
                removed += 1
                continue
            new_items.append(it)
        await user_conf.items.set(new_items)

        if cost:
            await bank.withdraw_credits(ctx.author, cost)

        await user_conf.rod_level.set(target)
        await ctx.send(f"🔧 Upgrade complete! Your rod is now level **{target}**.")

    # ---------- NPC and Quest Commands ----------
    @commands.command()
    async def npcs(self, ctx):
        """List known NPCs in the world (paged embed)."""
        embeds: List[discord.Embed] = []
        items_per = 6
        entries = list(self.npcs.items())
        for i in range(0, len(entries), items_per):
            chunk = entries[i:i+items_per]
            emb = discord.Embed(title="Known NPCs", colour=discord.Colour.green())
            emb.set_image(url="https://files.catbox.moe/jgohga.png")
            for key, info in chunk:
                emb.add_field(name=info.get("display", key), value=f"{info.get('greeting','')}\nQuests: {', '.join(info.get('quests',[])) or 'None'}\nCommand: `{ctx.clean_prefix}talknpc {key}`", inline=False)
            emb.set_footer(text=f"NPCs {i//items_per+1}/{(len(entries)-1)//items_per+1}")
            embeds.append(emb)
        await self._paginate_embeds(ctx, embeds)


    @commands.command()
    async def talknpc(self, ctx, npc_key: str):
        npc = self.npcs.get(npc_key.lower())
        if not npc:
            return await ctx.send("❌ Unknown NPC. Use `npcs` to see available NPCs.")

        user_conf = self.config.user(ctx.author)
        user_qstate = await user_conf.quests()
        user_completed = user_qstate.get("completed", []) if isinstance(user_qstate, dict) else []

        emb = discord.Embed(title=npc.get("display", npc_key), colour=discord.Colour.teal())
        greeting = npc.get("greeting", "")
        if greeting:
            emb.description = greeting

        img = npc.get("image")
        if isinstance(img, str) and img.startswith("http"):
            try:
                emb.set_thumbnail(url=img)
            except Exception:
                pass

        # List quests available (filter out non-repeatable completed ones)
        quest_list = []
        for qid in npc.get("quests", []):
            qdef = self.quests.get(qid)
            if not qdef:
                continue
            if not qdef.get("repeatable", False) and qid in user_completed:
                # mark as completed and unavailable
                quest_list.append((qdef.get("title", qid) + " (completed)", qid, False))
            else:
                quest_list.append((qdef.get("title", qid), qid, True))

        if quest_list:
            for title, qid, available in quest_list:
                status = "Available" if available else "Unavailable"
                emb.add_field(name=title, value=f"ID: `{qid}` — {status}\nUse `{ctx.clean_prefix}acceptquest {qid}` to accept", inline=False)
        else:
            emb.add_field(name="Quests", value="No quests available right now.", inline=False)

        # Footer with quick usage hint
        emb.set_footer(text=f"Use {ctx.clean_prefix}acceptquest <id> to accept. Use {ctx.clean_prefix}npcs to list NPCs.")

        await ctx.send(embed=emb)


    @commands.command()
    async def acceptquest(self, ctx, quest_id: str):
        """Accept a quest by id."""
        quest = self.quests.get(quest_id)
        if not quest:
            return await ctx.send("❌ Unknown quest id. Use `talknpc <npc>` to see quests.")
        user_conf = self.config.user(ctx.author)
        qstate = await user_conf.quests()
        if qstate.get("active"):
            return await ctx.send("❌ You already have an active quest. Finish or abandon it first (`abandonquest`).")
        prev_completed = qstate.get("completed", []) if isinstance(qstate, dict) else []
        qstate = {"active": quest_id, "step": 0, "progress": {}, "completed": prev_completed}
        await user_conf.quests.set(qstate)
        await ctx.send(f"✅ Quest accepted: **{quest['title']}**. Use `{ctx.clean_prefix}quest` to view progress.")
   

    @commands.command()
    async def quest(self, ctx):
        """Show your current quest and progress (embed + static image)."""
        user_conf = self.config.user(ctx.author)
        qstate    = await user_conf.quests()
        active    = qstate.get("active")
        if not active:
            return await ctx.send(
                "You have no active quest. Use `talknpc <npc>` to find quests or "
                "`acceptquest <id>` to accept one."
            )

        qdef       = self.quests.get(active)
        if not qdef:
            await user_conf.quests.set({})
            return await ctx.send(
                "Your active quest was invalid and has been cleared. Please pick a new quest."
            )

        # progress bookkeeping
        step_idx    = qstate.get("step", 0)
        total_steps = len(qdef["steps"])
        current     = min(step_idx + 1, total_steps)

        # build embed
        emb = discord.Embed(
            title=f"🗺️ {qdef['title']}",
            description=f"Step **{current}/{total_steps}**",
            colour=discord.Colour.purple()
        )
        emb.set_image(url=QUEST_BANNER_URL)

        # current step details
        if step_idx < total_steps:
            step = qdef["steps"][step_idx]
            emb.add_field(
                name="Objective",
                value=step.get("desc", "No description provided."),
                inline=False
            )

            # only add a “Progress” field for collect/deliver/sell steps
            prog = None
            if step["type"] == "collect_fish":
                needed = step["count"]
                name   = step.get("name")
                rarity = step.get("rarity")
                inv    = await user_conf.caught()
                have = (
                    inv.count(name)
                    if name
                    else sum(1 for f in inv
                             if f in self.fish_definitions
                             and self.fish_definitions[f]["rarity"] == rarity)
                )
                prog = f"{have}/{needed}"
            elif step["type"] == "deliver_item":
                needed = step["count"]
                item   = step["item"]
                inv_it = await user_conf.items()
                have   = inv_it.count(item)
                prog   = f"{have}/{needed} × {item}"
            elif step["type"] == "sell_value":
                needed = step["amount"]
                stats  = await user_conf.stats()
                have   = stats.get("sell_total", 0)
                curr   = await bank.get_currency_name(ctx.guild)
                prog   = f"{have}/{needed} {curr}"

            if prog:
                emb.add_field(name="Progress", value=prog, inline=True)

        else:
            emb.add_field(
                name="✅ All steps complete!",
                value="Use `completequest` to claim your rewards.",
                inline=False
            )

        await ctx.send(embed=emb)


    @commands.command()
    async def abandonquest(self, ctx):
        """Abandon your current active quest."""
        user_conf = self.config.user(ctx.author)
        qstate = await user_conf.quests()
        if not qstate or not qstate.get("active"):
            return await ctx.send("You have no active quest to abandon.")
        prev_completed = qstate.get("completed", [])
        await user_conf.quests.set({"completed": prev_completed})
        await ctx.send("You abandoned your active quest. Use `talknpc <npc>` to pick up new ones.")

    async def _advance_quest_on_catch(self, user, fish_name: str):
        user_conf = self.config.user(user)
        qstate = await user_conf.quests()
        active = qstate.get("active")
        if not active:
            return
        qdef = self.quests.get(active)
        if not qdef:
            return
        step_idx = qstate.get("step", 0)
        if step_idx >= len(qdef["steps"]):
            return
        step = qdef["steps"][step_idx]
        if step["type"] == "collect_fish":
            needed = step.get("count", 1)
            name = step.get("name")
            rarity = step.get("rarity")
            inv = await user_conf.caught()
            have = 0
            if name:
                have = inv.count(name)
            else:
                for f in inv:
                    if f in self.fish_definitions and self.fish_definitions[f].get("rarity") == rarity:
                        have += 1
            if have >= needed:
                qstate["step"] = step_idx + 1
                await user_conf.quests.set(qstate)

    async def _complete_quest_for_user(self, user, ctx=None):
        """Internal helper: complete and pay out the active quest for a user. Returns message string."""
        user_conf = self.config.user(user)
        qstate = await user_conf.quests()
        active = qstate.get("active")
        if not active:
            return "No active quest to complete."
        qdef = self.quests.get(active)
        if not qdef:
            await user_conf.quests.set({})
            return "Quest data invalid; cleared."
        inv = await user_conf.caught()
        items = await user_conf.items()
        stats = await user_conf.stats()
        # verify steps
        for step in qdef["steps"]:
            t = step["type"]
            if t == "collect_fish":
                needed = step.get("count", 1)
                name = step.get("name")
                rarity = step.get("rarity")
                have = 0
                if name:
                    have = inv.count(name)
                else:
                    for f in inv:
                        if f in self.fish_definitions and self.fish_definitions[f].get("rarity") == rarity:
                            have += 1
                if have < needed:
                    return "You have not yet completed the quest steps."
            elif t == "deliver_item":
                needed = step.get("count", 1)
                item = step.get("item")
                have = items.count(item)
                if have < needed:
                    return "You have not yet completed the quest steps."
            elif t == "sell_value":
                needed = step.get("amount", 0)
                if stats.get("sell_total", 0) < needed:
                    return "You have not yet completed the quest steps."
            elif t == "visit_npc":
                continue
            else:
                return "Unknown quest step type; cannot complete."

        # consume required things
        remaining_inv = list(inv)
        remaining_items = list(items)
        for step in qdef["steps"]:
            if step["type"] == "collect_fish":
                needed = step.get("count", 1)
                name = step.get("name")
                rarity = step.get("rarity")
                if name:
                    removed = 0
                    new_rem = []
                    for f in remaining_inv:
                        if f == name and removed < needed:
                            removed += 1
                            continue
                        new_rem.append(f)
                    remaining_inv = new_rem
                else:
                    to_remove = needed
                    for f in list(remaining_inv):
                        if to_remove <= 0:
                            break
                        if f in self.fish_definitions and self.fish_definitions[f].get("rarity") == rarity:
                            remaining_inv.remove(f)
                            to_remove -= 1
            elif step["type"] == "deliver_item":
                needed = step.get("count", 1)
                item = step.get("item")
                removed = 0
                new_items = []
                for it in remaining_items:
                    if it == item and removed < needed:
                        removed += 1
                        continue
                    new_items.append(it)
                remaining_items = new_items

        await user_conf.caught.set(remaining_inv)
        await user_conf.items.set(remaining_items)

        rewards = qdef.get("rewards", {})
        messages = []
        if "coins" in rewards:
            amt = int(rewards["coins"])
            new_bal, currency = await self._deposit(user, amt, ctx)
            messages.append(f"You received {amt} {currency}. New balance: {new_bal} {currency}.")
        if "items" in rewards:
            added_items = []
            items_cfg = await user_conf.items()
            for iname, cnt in rewards["items"].items():
                for _ in range(cnt):
                    items_cfg.append(iname)
                added_items.append(f"{cnt}× {iname}")
            await user_conf.items.set(items_cfg)
            messages.append("You received: " + ", ".join(added_items))

        prev = await self.config.user(user).quests()
        completed_list = prev.get("completed", [])
        if not qdef.get("repeatable", False):
            if active not in completed_list:
                completed_list.append(active)
        await user_conf.quests.set({"completed": completed_list})
        try:
            stats = await user_conf.stats()
            stats["quests_completed_total"] = stats.get("quests_completed_total", 0) + 1
            await user_conf.stats.set(stats)
            if stats["quests_completed_total"] >= 5 and not await self._has_achievement(user, "npc_friend"):
                await self._award_achievement(ctx or None, user, "npc_friend")
            if stats["quests_completed_total"] >= 25 and not await self._has_achievement(user, "quest_master"):
                await self._award_achievement(ctx or None, user, "quest_master")
        except Exception:
            pass        
        return "Quest complete! " + " ".join(messages)

    @commands.command()
    async def completequest(self, ctx):
        """Attempt to complete and claim rewards for your active quest."""
        user_conf = self.config.user(ctx.author)
        qstate = await user_conf.quests()
        active = qstate.get("active")
        if not active:
            return await ctx.send("You have no active quest.")
        msg = await self._complete_quest_for_user(ctx.author, ctx)
        await ctx.send(msg)

    @commands.command()
    async def visitnpc(self, ctx, npc_key: str):
        """Visit an NPC to advance quest steps that require visiting."""
        npc = self.npcs.get(npc_key.lower())
        if not npc:
            return await ctx.send("Unknown NPC key. Use `npcs` to list them.")
        user_conf = self.config.user(ctx.author)
        qstate = await user_conf.quests()
        active = qstate.get("active")
        if not active:
            return await ctx.send(f"You visit {npc['display']}. {npc.get('greeting','')}")
        qdef = self.quests.get(active)
        if not qdef:
            return await ctx.send(f"You visit {npc['display']}. {npc.get('greeting','')}")
        step_idx = qstate.get("step", 0)
        if step_idx >= len(qdef["steps"]):
            return await ctx.send(f"You visit {npc['display']}. It seems you've completed the steps; use `completequest`.")
        step = qdef["steps"][step_idx]
        if step["type"] == "visit_npc" and step.get("npc") == npc_key.lower():
            qstate["step"] = step_idx + 1
            await user_conf.quests.set(qstate)
            return await ctx.send(f"You spoke with {npc['display']}. Quest advanced.")
        return await ctx.send(f"You speak with {npc['display']}. {npc.get('greeting','')}")
        
    @commands.command()
    async def fishleaderboard(self, ctx, top: int = 10):
        """
        Show the top anglers on this server by total fish caught.
        """
        # gather (member, count) for everyone who has cast at least once
        entries = []
        for member in ctx.guild.members:
            stats = await self.config.user(member).stats()
            count = stats.get("fish_caught", 0)
            if count > 0:
                entries.append((member.display_name, count))

        if not entries:
            return await ctx.send("No one has caught any fish yet on this server.")

        # sort highest → lowest and take the top N
        entries.sort(key=lambda x: x[1], reverse=True)
        entries = entries[:top]

        # build embed
        emb = discord.Embed(
            title="🐟 Fishing Leaderboard",
            description="\n".join(f"**{i+1}.** {name}: {count} fish"
                                 for i, (name, count) in enumerate(entries)),
            colour=discord.Colour.blue()
        )
        # thumbnail for flavor—swap this URL for your own graphic
        emb.set_thumbnail(url="https://files.catbox.moe/awbf4w.png")

        await ctx.send(embed=emb)
    

    async def cog_unload(self):
        pass


async def setup(bot):
    await bot.add_cog(Fishing(bot))

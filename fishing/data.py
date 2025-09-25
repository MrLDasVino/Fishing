# cogs/fishing/data.py
from typing import Dict, Tuple, Any

# ——— FISH DEFINITIONS ———
fish_definitions: Dict[str, Dict[str, Any]] = {
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
    "Ember Carp":        {"weight": 20,  "price": 100, "emoji": "🔥",  "rarity": "Epic",     "biome": "Volcanic Spring"},
    "Lava Snapper":      {"weight": 10,  "price": 140, "emoji": "🌋",  "rarity": "Legendary","biome": "Volcanic Spring"},
    "Magma Eel":         {"weight": 5,   "price": 220, "emoji": "🌋",  "rarity": "Mythic",   "biome": "Volcanic Spring"},
    "Fire Goby":         {"weight": 60,  "price": 35,  "emoji": "🔥",  "rarity": "Uncommon", "biome": "Volcanic Spring"},
    "Cinder Minnow":     {"weight": 120, "price": 25,  "emoji": "🪵",  "rarity": "Common",   "biome": "Volcanic Spring"},
    "Wraith Herring":    {"weight": 60,  "price": 80,  "emoji": "👻",  "rarity": "Rare",     "biome": "Haunted Shoals"},
    "Bonefish":          {"weight": 80,  "price": 30,  "emoji": "💀",  "rarity": "Uncommon", "biome": "Haunted Shoals"},
    "Ghost Catfish":     {"weight": 30,  "price": 110, "emoji": "👻",  "rarity": "Epic",     "biome": "Haunted Shoals"},
    "Phantom Carp":      {"weight": 12,  "price": 160, "emoji": "🌑",  "rarity": "Legendary","biome": "Haunted Shoals"},
    "Specter Eel":       {"weight": 6,   "price": 200, "emoji": "👻",  "rarity": "Mythic",   "biome": "Haunted Shoals"},
    "Dream Pike":        {"weight": 50,  "price": 85,  "emoji": "💭",  "rarity": "Rare",     "biome": "Dreaming Deep"},
    "Nightmare Grouper": {"weight": 25,  "price": 130, "emoji": "🌑",  "rarity": "Epic",     "biome": "Dreaming Deep"},
    "Sleepfin":          {"weight": 75,  "price": 28,  "emoji": "😴",  "rarity": "Uncommon", "biome": "Dreaming Deep"},
    "Somnus Shrimp":     {"weight": 55,  "price": 90,  "emoji": "🦐",  "rarity": "Rare",     "biome": "Dreaming Deep"},
    "Hypnos Bass":       {"weight": 15,  "price": 150, "emoji": "💤",  "rarity": "Legendary","biome": "Dreaming Deep"},
    "Leviathan Cod":     {"weight": 4,   "price": 300, "emoji": "🐋",  "rarity": "Mythic",   "biome": "Titan's Trench"},
    "Titan Crab":        {"weight": 40,  "price": 140, "emoji": "🦀",  "rarity": "Epic",     "biome": "Titan's Trench"},
    "Abyssal Angler":    {"weight": 10,  "price": 180, "emoji": "🎣",  "rarity": "Legendary","biome": "Titan's Trench"},
    "Deepwyrm":          {"weight": 3,   "price": 350, "emoji": "🐉",  "rarity": "Mythic",   "biome": "Titan's Trench"},
    "Pressure Pike":     {"weight": 70,  "price": 45,  "emoji": "🐟",  "rarity": "Uncommon", "biome": "Titan's Trench"},
    "Neon Sprat":        {"weight": 140, "price": 18,  "emoji": "🌟",  "rarity": "Common",   "biome": "Bioluminal Cavern"},
    "Glowfin Trout":     {"weight": 50,  "price": 95,  "emoji": "✨",  "rarity": "Rare",     "biome": "Bioluminal Cavern"},
    "Radiant Ray":       {"weight": 14,  "price": 220, "emoji": "⚡",  "rarity": "Legendary","biome": "Bioluminal Cavern"},
    "Luminous Carp":     {"weight": 32,  "price": 120, "emoji": "💡",  "rarity": "Epic",     "biome": "Bioluminal Cavern"},
    "Lucent Gudgeon":    {"weight": 80,  "price": 35,  "emoji": "🔆",  "rarity": "Uncommon", "biome": "Bioluminal Cavern"},
    "Moonshadow Koi":    {"weight": 30,  "price": 125, "emoji": "🌙",  "rarity": "Epic",     "biome": "Ethereal Lagoon"},
    "Starling Minnow":   {"weight": 130, "price": 20,  "emoji": "⭐",  "rarity": "Common",   "biome": "Ethereal Lagoon"},
    "Celestial Salmon":  {"weight": 8,   "price": 180, "emoji": "🌌",  "rarity": "Legendary","biome": "Ethereal Lagoon"},
    "Nebula Nibbler":    {"weight": 5,   "price": 240, "emoji": "☄️",  "rarity": "Mythic",   "biome": "Ethereal Lagoon"},
    "Skyfin":            {"weight": 65,  "price": 40,  "emoji": "🌤️", "rarity": "Uncommon", "biome": "Ethereal Lagoon"},    
}

# Derived price lookup
fish_prices = {name: info["price"] for name, info in fish_definitions.items()}

# ——— ACHIEVEMENTS METADATA ———
achievements: Dict[str, Tuple[str, str, str]] = {
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

# ——— CRAFTING RECIPES ———
# Copy your crafting_recipes dict here:
crafting_recipes = {
    "chum": {
        "name": "Chum",
        "requirements": {"any_fish": 3},
        "result": {"item": "Chum"},
        "description": "Combine any 3 fish to craft Chum (consumable). Using Chum gives +3 luck."
    },
    "trophy": {
        "name": "Trophy",
        "requirements": {"any_fish": 5},
        "result": {
            "coins": 100,       # still gives 100 coins
            "item": "Trophy"    # now also grants a Trophy item
        },
        "description": "Combine any 5 fish to craft a Trophy, receive 100 coins and a Trophy item.",
    },
    "fragments_from_epic": {
        "name": "Epic Refinement",
        "requirements": {"rarity:Epic": 2},
        "result": {"items": {"Rod Fragment": 2}},
        "description": "Refine two Epic fish into 2 Rod Fragments (removes the fish).",
    },
    "fish_stew": {
        "name": "Hearty Fish Stew",
        "requirements": {"any_fish": 2, "rarity:Uncommon": 1},
        "result": {"item": "Stew Bowl"},
        "description": "Cook 2 fish (1 Uncommon) into a Stew Bowl. Eating it gives +2 luck on your next 5 casts.",
    },
    "elemental_lure": {
        "name": "Stormcaller Lure",
        "requirements": {"rarity:Rare": 1, "item:Storm Scale": 1},
        "result": {"item": "Stormcaller Lure"},
        "description": "Use this lure to double your chance of Rare+ fish on the next cast.",
    },
    "trophy_plaque": {
        "name": "Angler’s Plaque",
        "requirements": {"item:Trophy": 1, "rarity:Legendary": 1},
        "result": {"item": "Plaque"},
        "description": "Combine Trophy + Legendary fish into a decorative Plaque you can display or sell.",
    },
    "fish_oil": {
        "name": "Fish Oil Flask",
        "requirements": {"fish:Mackerel": 1, "fish:Tuna": 1},
        "result": {"coins": 50},
        "description": "Extract oil from Mackerel + Tuna for 50 coins. A key alchemy ingredient!",
    },
    "nutrient_pack": {
        "name": "Nutrient Pack",
        "requirements": {"rarity:Common": 1, "rarity:Uncommon": 1, "rarity:Rare": 1},
        "result": {"item": "Nutrient Pack"},
        "description": "Use to gain +1 bait each hour for the next 6 hours.",
    },
    "coil_upgrade": {
        "name": "Durability Coil",
        "requirements": {"item:Rod Core": 2, "rarity:Mythic": 1},
        "result": {"item": "Rod Coil"},
        "description": "Attach to your rod to halve break chance for 100 casts.",
    },
    "mystic_tonic": {
        "name": "Mystic Angler’s Tonic",
        "requirements": {"rarity:Mythic": 1, "rarity:Boss": 1},
        "result": {"coins": 200, "item": "Tonic Bottle"},
        "description": "Resets your streak and grants a 200-coin bonus when drunk.",
    },
    "festival_pack": {
        "name": "Festival Pack",
        "requirements": {"item:Treasure Map": 1, "item:Coral Trinket": 1, "item:Pearl": 1},
        "result": {"item": "Festival Pack"},
        "description": "Use to guarantee a Festival event on your next cast.",
    },
    "biome_journal": {
        "name": "Biome Explorer’s Journal",
        "requirements": {
            "fish:Pond": 1,
            "fish:River": 1,
            "fish:Open Ocean": 1
        },
        "result": {"coins": 100},
        "description": "Grants +10% chance of biome-specific rares for 10 casts.",
    },
    "mystery_box": {
        "name": "Mystery Box",
        "requirements": {"any_fish": 5},
        "result": {"item": "Mystery Box"},
        "description": "Open for a random reward: Rod Core / 100–300 coins / Treasure Map.",
    },    
}

# ——— NPCS & QUESTS ———
# Copy your npcs dict here:
npcs = {
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
    "vulko": {
        "display": "Vulko the Lava Shaman",
        "greeting": "'The magma sings to those who dare. Will you listen to its rhythm?'",
        "quests": [
            "volcanic_venture",   # e.g. catch Ember Carp or Magma Eel
            "ember_hunt",         # e.g. collect Fire Goby
            "inferno_artifact",   # e.g. deliver Lava Pearl
            "lava_challenge"      # e.g. survive a lava_spout event
        ],
        "image": "https://files.catbox.moe/kd6fvu.png",
    },
    "paleon": {
        "display": "Paleon the Fossil Chaser",
        "greeting": "'These ancient currents whisper of long-lost beasts. Help me unearth their bones.'",
        "quests": [
            "fossil_hunt",        # e.g. catch Trilobite or Ammonite
            "dunkle_search",      # e.g. land a Dunkleosteus
            "leviathan_probe",    # e.g. hook a Mire Leviathan
            "placoderm_delve"     # e.g. deliver a Placoderm
        ],
        "image": "https://files.catbox.moe/irhj3p.png",
    },
    "grimma": {
        "display": "Grimma the Ghost Whisperer",
        "greeting": "'Shadows stir beneath haunted shoals. Are you bold enough to answer their call?'",
        "quests": [
            "haunted_whispers",   # e.g. trigger haunted_whispers event
            "spectral_tide",      # e.g. net a Spectral Herring
            "phantom_treasure",   # e.g. find a Phantom Pearl
            "wraith_bounty"       # e.g. deliver Ghost Carp
        ],
        "image": "https://files.catbox.moe/bphqno.png",
    },
    "stellara": {
        "display": "Stellara the Starfarer",
        "greeting": "'The void beyond the waves is alive with cosmic wonders. Cast into the stars.'",
        "quests": [
            "asteroid_hunt",      # e.g. catch Asteroid Salmon
            "nebula_expedition",  # e.g. land a Nebula Eel
            "cosmic_probe",       # e.g. trigger meteor_shower or moon_phase
            "starwhale_sighting"  # e.g. net a Star Whale
        ],
        "image": "https://files.catbox.moe/ysmx5h.png",
    },
}

# Copy your quests dict here:
quests = {
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

    "volcanic_venture": {
        "title": "Volcanic Venture",
        "steps": [
            {
                "type": "collect_fish",
                "rarity": "Epic",
                "count": 2,
                "desc": "Catch 2 Epic fish in a Volcanic Spring."
            }
        ],
        "rewards": {"coins": 150, "items": {"Rod Fragment": 1}},
        "repeatable": False,
    },
    "ember_hunt": {
        "title": "Ember Hunt",
        "steps": [
            {
                "type": "collect_fish",
                "name": "Fire Goby",
                "count": 3,
                "desc": "Catch 3 Fire Goby from the smoldering pools."
            }
        ],
        "rewards": {"coins": 50, "items": {"Chum": 1}},
        "repeatable": True,
    },
    "inferno_artifact": {
        "title": "Inferno Artifact",
        "steps": [
            {
                "type": "deliver_item",
                "item": "Lava Pearl",
                "count": 1,
                "desc": "Deliver a Lava Pearl to Vulko."
            }
        ],
        "rewards": {"coins": 200, "items": {"Rod Core": 1}},
        "repeatable": False,
    },
    "lava_challenge": {
        "title": "Lava Challenge",
        "steps": [
            {
                "type": "collect_fish",
                "name": "Magma Eel",
                "count": 1,
                "desc": "Hook a Magma Eel from a sudden lava spout."
            }
        ],
        "rewards": {"coins": 300, "items": {"Storm Scale": 1}},
        "repeatable": False,
    },    
    "fossil_hunt": {
        "title": "Fossil Hunt",
        "steps": [
            {
                "type": "collect_fish",
                "rarity": "Uncommon",
                "count": 3,
                "desc": "Catch 3 Uncommon fish in the Prehistoric biome."
            }
        ],
        "rewards": {"coins": 60, "items": {"Chum": 1}},
        "repeatable": True,
    },
    "dunkle_search": {
        "title": "Dunkle Search",
        "steps": [
            {
                "type": "collect_fish",
                "name": "Dunkleosteus",
                "count": 1,
                "desc": "Catch one Dunkleosteus."
            }
        ],
        "rewards": {"coins": 150, "items": {"Rod Fragment": 1}},
        "repeatable": False,
    },
    "leviathan_probe": {
        "title": "Leviathan Probe",
        "steps": [
            {
                "type": "collect_fish",
                "name": "Mire Leviathan",
                "count": 1,
                "desc": "Secure proof of a Mire Leviathan catch."
            }
        ],
        "rewards": {"coins": 400, "items": {"Map": 1}},
        "repeatable": False,
    },
    "placoderm_delve": {
        "title": "Placoderm Delve",
        "steps": [
            {
                "type": "collect_fish",
                "name": "Placoderm",
                "count": 1,
                "desc": "Catch one Placoderm."
            }
        ],
        "rewards": {"coins": 120},
        "repeatable": True,
    },   
    "haunted_whispers": {
        "title": "Haunted Whispers",
        "steps": [
            {
                "type": "collect_fish",
                "name": "Spectral Herring",
                "count": 1,
                "desc": "Catch one Spectral Herring."
            }
        ],
        "rewards": {"coins": 80, "items": {"Pearl": 1}},
        "repeatable": True,
    },
    "spectral_tide": {
        "title": "Spectral Tide",
        "steps": [
            {
                "type": "collect_fish",
                "name": "Wraith Herring",
                "count": 2,
                "desc": "Net two Wraith Herring from the Haunted Shoals."
            }
        ],
        "rewards": {"coins": 100, "items": {"Rod Fragment": 1}},
        "repeatable": False,
    },
    "phantom_treasure": {
        "title": "Phantom Treasure",
        "steps": [
            {
                "type": "deliver_item",
                "item": "Phantom Pearl",
                "count": 1,
                "desc": "Turn in a Phantom Pearl."
            }
        ],
        "rewards": {"coins": 200, "items": {"Storm Scale": 1}},
        "repeatable": False,
    },
    "wraith_bounty": {
        "title": "Wraith Bounty",
        "steps": [
            {
                "type": "collect_fish",
                "name": "Ghost Carp",
                "count": 1,
                "desc": "Bring in one Ghost Carp."
            }
        ],
        "rewards": {"coins": 120, "items": {"Chum": 1}},
        "repeatable": True,
    },
    "asteroid_hunt": {
        "title": "Asteroid Hunt",
        "steps": [
            {
                "type": "collect_fish",
                "name": "Asteroid Salmon",
                "count": 2,
                "desc": "Catch two Asteroid Salmon."
            }
        ],
        "rewards": {"coins": 100, "items": {"Map": 1}},
        "repeatable": True,
    },
    "nebula_expedition": {
        "title": "Nebula Expedition",
        "steps": [
            {
                "type": "collect_fish",
                "name": "Nebula Eel",
                "count": 1,
                "desc": "Land one Nebula Eel."
            }
        ],
        "rewards": {"coins": 180, "items": {"Rod Fragment": 1}},
        "repeatable": False,
    },
    "cosmic_probe": {
        "title": "Cosmic Probe",
        "steps": [
            {
                "type": "collect_fish",
                "rarity": "Mythic",
                "count": 1,
                "desc": "Catch a Mythic fish under cosmic skies."
            }
        ],
        "rewards": {"coins": 200, "items": {"Coral Trinket": 1}},
        "repeatable": False,
    },
    "starwhale_sighting": {
        "title": "Starwhale Sighting",
        "steps": [
            {
                "type": "collect_fish",
                "name": "Star Whale",
                "count": 1,
                "desc": "Net a Star Whale."
            }
        ],
        "rewards": {"coins": 300, "items": {"Tonic Bottle": 1}},
        "repeatable": False,
    },    
}

# ——— ROD UPGRADE SETTINGS ———
rod_upgrade_requirements = {
    1: {"fragments": 3, "coins": 0},
    2: {"fragments": 6, "coins": 50},
    3: {"fragments": 10, "coins": 150},
}
rod_level_fish_multiplier = {0: 1.0, 1: 1.2, 2: 1.4, 3: 1.6}
rod_level_break_reduction = {0: 1.0, 1: 0.8, 2: 0.6, 3: 0.4}

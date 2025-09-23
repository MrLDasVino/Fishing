import random
import asyncio
import discord
from typing import Dict, Tuple, List, Optional, Any

from redbot.core import commands, bank, Config


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
                "quests": ["maris_fragment_hunt"],
            },
            "oldfinn": {
                "display": "Old Finn",
                "greeting": "'Hm, a keen eye for fish? I remember the river in my day…'",
                "quests": ["finn_first_catch"],
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
        }

    # ---------- Helpers ----------
    def _random_fish(self) -> str:
        names = list(self.fish_definitions.keys())
        weights = [self.fish_definitions[n]["weight"] for n in names]
        return random.choices(names, weights=weights, k=1)[0]

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
        user_conf = self.config.user(user)
        earned = await user_conf.achievements()
        if ach_id in earned:
            return None
        earned.append(ach_id)
        await user_conf.achievements.set(earned)
        name, desc, _ = self.achievements[ach_id]
        reward = 0
        if ach_id in ("first_fish", "first_cast"):
            reward = 5
        elif ach_id == "mythic_catch":
            reward = 100
        elif ach_id == "treasure_hunter":
            reward = 25
        if reward > 0:
            new_bal = await bank.deposit_credits(user, reward)
            currency = await bank.get_currency_name(ctx.guild)
            return f"🏆 Achievement unlocked: **{name}** — {desc}\nYou received **{reward} {currency}**! New balance: **{new_bal} {currency}**."
        return f"🏆 Achievement unlocked: **{name}** — {desc}"

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
        rarity = self.fish_definitions.get(fish_name, {}).get("rarity", "")
        if rarity == "Mythic" and not await self._has_achievement(user, "mythic_catch"):
            await self._award_achievement(self.bot.get_guild(0) or None, user, "mythic_catch")

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
        data = await user_conf.caught()
        data.append("Treasure Map")
        await user_conf.caught.set(data)
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
            return False, f"🛠️ You salvage rare parts, get **{coins} {currency}** and a **Rod Core**!"
        if r < 0.10:
            items = await user_conf.items()
            items.append("Rod Fragment")
            await user_conf.items.set(items)
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

    # ---------- Core fish command ----------
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command()
    async def fish(self, ctx):
        """Cast your line and see what you reel in."""
        user_conf = self.config.user(ctx.author)
        if await user_conf.rod_broken():
            return await ctx.send(
                "🎣 Your rod is broken! Use "
                f"`{ctx.clean_prefix}repairrod` to fix it for 20 coins."
            )

        waiting_msg = await ctx.send("🎣 You cast your line and wait patiently…")
        await asyncio.sleep(random.uniform(1.5, 5.5))

        keys = list(self.event_handlers.keys())
        weights = [self.event_handlers[k][1] for k in keys]

        # bait modifier
        try:
            bait_amount = await user_conf.bait()
        except Exception:
            bait_amount = 0
        if bait_amount and bait_amount > 0:
            if random.random() < 0.9:
                await user_conf.bait.set(max(0, bait_amount - 1))
            for i, k in enumerate(keys):
                if k in ("fish", "double"):
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
        if isinstance(result, tuple) and len(result) >= 2:
            message = result[1]
        elif isinstance(result, str):
            message = result

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
        """View how many fish you’ve caught, your items, and your bank balance."""
        data = await self.config.user(ctx.author).all()
        caught = data["caught"]
        if not caught:
            return await ctx.send(
                f"You haven't caught anything yet. Use `{ctx.clean_prefix}fish` to start fishing!"
            )

        counts = {}
        for fish in caught:
            counts[fish] = counts.get(fish, 0) + 1
        breakdown = "\n".join(
            f"• {self.fish_definitions.get(fish, {}).get('emoji','')} {fish}: {count}"
            for fish, count in counts.items()
        )
        bal = await bank.get_balance(ctx.author)
        currency = await bank.get_currency_name(ctx.guild)
        items = await self.config.user(ctx.author).items()
        itemline = ""
        if items:
            inv_counts = {}
            for it in items:
                inv_counts[it] = inv_counts.get(it, 0) + 1
            itemline = "\n\nItems:\n" + "\n".join(f"• {iname}: {count}" for iname, count in inv_counts.items())
        await ctx.send(
            f"**{ctx.author.display_name}'s Fishing Stats**\n\n"
            f"Balance: **{bal}** {currency}\n"
            f"{breakdown}{itemline}"
        )

    @commands.command()
    async def achievements(self, ctx):
        """Show your earned achievements and progress on a few tracked goals."""
        user_conf = self.config.user(ctx.author)
        earned = await user_conf.achievements()
        stats = await user_conf.stats()
        caught = await user_conf.caught()
        lines = []
        if earned:
            lines.append("**Earned Achievements**")
            for aid in earned:
                name, desc, _ = self.achievements.get(aid, (aid, "", ""))
                lines.append(f"🏆 **{name}** — {desc}")
        else:
            lines.append("You haven't earned any achievements yet.")
        lines.append("\n**Progress**")
        lines.append(f"• Total casts: {stats.get('casts',0)}")
        lines.append(f"• Fish caught: {stats.get('fish_caught',0)}")
        unique = len(set(x for x in caught if x and not x.lower().startswith("treasure")))
        lines.append(f"• Unique species: {unique}")
        lines.append(f"• Sell total: {stats.get('sell_total',0)}")
        msg = "\n".join(lines)
        if len(msg) <= 1900:
            return await ctx.send(msg)
        for i in range(0, len(msg), 1900):
            await ctx.send(msg[i:i+1900])

    @commands.command()
    async def achievementlist(self, ctx):
        """Show all achievements and their descriptions."""
        lines = ["**All Achievements**"]
        for aid, (name, desc, cat) in self.achievements.items():
            lines.append(f"• **{name}** ({aid}) — {desc} [{cat}]")
        msg = "\n".join(lines)
        if len(msg) <= 1900:
            return await ctx.send(msg)
        for i in range(0, len(msg), 1900):
            await ctx.send(msg[i:i+1900])

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
        """List available crafting recipes."""
        lines = ["**Crafting Recipes**"]
        for rid, info in self.crafting_recipes.items():
            lines.append(f"• **{info['name']}** (`{rid}`) — {info['description']}")
        msg = "\n".join(lines)
        if len(msg) <= 1900:
            return await ctx.send(msg)
        for i in range(0, len(msg), 1900):
            await ctx.send(msg[i:i+1900])

    def _count_inventory_by_rarity(self, inventory: List[str]) -> Dict[str, int]:
        counts = {}
        for f in inventory:
            if f in self.fish_definitions:
                rar = self.fish_definitions[f].get("rarity", "Unknown")
                counts[rar] = counts.get(rar, 0) + 1
            else:
                counts[f] = counts.get(f, 0) + 1
        return counts

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
        return await ctx.send(f"❌ **{match}** cannot be used directly.")

    # ---------- Rod view and upgrade ----------
    @commands.command()
    async def rod(self, ctx):
        """Show your rod level and fragments/cores."""
        user_conf = self.config.user(ctx.author)
        lvl = await user_conf.rod_level()
        items = await user_conf.items()
        fragments = items.count("Rod Fragment")
        cores = items.count("Rod Core")
        next_req = self.rod_upgrade_requirements.get(lvl + 1)
        if next_req:
            req_text = f"{next_req['fragments']} fragments"
            if next_req.get("coins", 0):
                req_text += f" and {next_req['coins']} coins"
        else:
            req_text = "Max level reached"
        await ctx.send(
            f"🎣 Rod Level: **{lvl}**\n"
            f"• Rod Fragments: **{fragments}**\n"
            f"• Rod Cores: **{cores}**\n"
            f"Next upgrade requires: {req_text}"
        )

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
        """List known NPCs in the world."""
        lines = ["**Known NPCs**"]
        for key, info in self.npcs.items():
            lines.append(f"• **{info['display']}** — Command: `{ctx.clean_prefix}talknpc {key}`")
        await ctx.send("\n".join(lines))

    @commands.command()
    async def talknpc(self, ctx, npc_key: str):
        """Talk to an NPC to get greeting or start quests."""
        npc = self.npcs.get(npc_key.lower())
        if not npc:
            return await ctx.send("❌ Unknown NPC. Use `npcs` to see available NPCs.")
        user_conf = self.config.user(ctx.author)
        qstate = await user_conf.quests()
        lines = [f"**{npc['display']}**", npc.get("greeting", "")]
        available = []
        for qid in npc.get("quests", []):
            qdef = self.quests.get(qid)
            if not qdef:
                continue
            prev = await self.config.user(ctx.author).quests()
            completed = prev.get("completed", [])
            if not qdef.get("repeatable", False) and qid in completed:
                continue
            available.append((qid, qdef))
        if available:
            lines.append("\nQuests available from this NPC:")
            for qid, qdef in available:
                lines.append(f"• **{qdef['title']}** — id: `{qid}` — use `{ctx.clean_prefix}acceptquest {qid}` to accept")
        else:
            lines.append("\nNo quests available right now.")
        await ctx.send("\n".join(lines))

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
        qstate = {"active": quest_id, "step": 0, "progress": {}, "completed": qstate.get("completed", []) if isinstance(qstate, dict) else []}
        await user_conf.quests.set(qstate)
        await ctx.send(f"✅ Quest accepted: **{quest['title']}**. Use `{ctx.clean_prefix}quest` to view progress.")

    @commands.command()
    async def quest(self, ctx):
        """Show your current quest and progress."""
        user_conf = self.config.user(ctx.author)
        qstate = await user_conf.quests()
        active = qstate.get("active")
        if not active:
            return await ctx.send("You have no active quest. Use `talknpc <npc>` to find quests or `acceptquest <id>` to accept one.")
        qdef = self.quests.get(active)
        if not qdef:
            await user_conf.quests.set({})
            return await ctx.send("Your active quest was invalid and has been cleared. Please pick a new quest.")
        step_idx = qstate.get("step", 0)
        lines = [f"**{qdef['title']}**", f"Step {min(step_idx+1, len(qdef['steps']))}/{len(qdef['steps'])}:"]
        if step_idx < len(qdef["steps"]):
            step = qdef["steps"][step_idx]
            lines.append(f"• {step.get('desc', 'No description')}")
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
                lines.append(f"Progress: **{have}/{needed}**")
            elif step["type"] == "deliver_item":
                needed = step.get("count", 1)
                item = step.get("item")
                items = await user_conf.items()
                have = items.count(item)
                lines.append(f"Progress: **{have}/{needed} {item}**")
            elif step["type"] == "sell_value":
                needed = step.get("amount", 0)
                stats = await user_conf.stats()
                sold = stats.get("sell_total", 0)
                lines.append(f"Progress (sell total): **{sold}/{needed}**")
        else:
            lines.append("All steps completed. Use `completequest` to claim your rewards.")
        await ctx.send("\n".join(lines))

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
        return "Quest complete! " + " ".join(messages)

    @commands.command()

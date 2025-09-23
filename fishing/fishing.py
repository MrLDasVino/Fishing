import random
import asyncio
from typing import Dict, Tuple, List, Optional

from redbot.core import commands, bank, Config


class Fishing(commands.Cog):
    """Fishing minigame with events and achievements."""

    def __init__(self, bot):
        self.bot = bot
        # Config
        self.config = Config.get_conf(self, identifier=1234567890123)
        default_user = {
            "caught": [],        # list of fish names and items (strings)
            "rod_broken": False,
            "bait": 0,
            "luck": 0,
            "achievements": [],  # list of achievement ids earned
            "stats": {           # quick stats to evaluate achievements
                "casts": 0,
                "fish_caught": 0,
                "unique_fish": 0,
                "highest_value_catch": 0,
                "sell_total": 0,
                "consecutive_catches": 0,  # for streaks
            },
        }
        self.config.register_user(**default_user)

        # ---------- Fish definitions (short sample; replace with your full list) ----------
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
        self.fish_prices = {n: i["price"] for n, i in self.fish_definitions.items()}

        # ---------- Achievement definitions ----------
        # id -> (name, description, category)
        # category is used for grouping; optional
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
            # add more as desired
        }

        # Map certain rarity strings to a ranking for checks
        self.rarity_rank = {
            "Common": 0,
            "Uncommon": 1,
            "Rare": 2,
            "Epic": 3,
            "Legendary": 4,
            "Mythic": 5,
            "Boss": 6,
        }

        # ---------- Event handlers registry (example; expand as before) ----------
        self.event_handlers = {
            "nothing": (self._event_nothing, 35),
            "junk": (self._event_junk, 6),
            "fish": (self._event_fish, 28),
            "double": (self._event_double, 4),
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

    # ---------- Achievement helpers ----------
    async def _has_achievement(self, user, ach_id: str) -> bool:
        earned = await self.config.user(user).achievements()
        return ach_id in earned

    async def _award_achievement(self, ctx, user, ach_id: str) -> Optional[str]:
        """Award an achievement if not already earned. Returns message or None."""
        if ach_id not in self.achievements:
            return None
        user_conf = self.config.user(user)
        earned = await user_conf.achievements()
        if ach_id in earned:
            return None
        earned.append(ach_id)
        await user_conf.achievements.set(earned)
        name, desc, _ = self.achievements[ach_id]
        # Optionally give a small coin reward on achievement
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

    async def _check_and_award(self, ctx, user):
        """Run through achievements checks that rely on stats or inventory."""
        user_conf = self.config.user(user)
        stats = await user_conf.stats()
        caught = await user_conf.caught()
        earned = await user_conf.achievements()

        messages = []

        # first_cast: use stats['casts'] >= 1
        if stats.get("casts", 0) >= 1 and "first_cast" not in earned:
            msg = await self._award_achievement(ctx, user, "first_cast")
            if msg:
                messages.append(msg)

        # first_fish & fish_10 & fish_100
        if stats.get("fish_caught", 0) >= 1 and "first_fish" not in earned:
            msg = await self._award_achievement(ctx, user, "first_fish")
            if msg:
                messages.append(msg)
        if stats.get("fish_caught", 0) >= 10 and "fish_10" not in earned:
            msg = await self._award_achievement(ctx, user, "fish_10")
            if msg:
                messages.append(msg)
        if stats.get("fish_caught", 0) >= 100 and "fish_100" not in earned:
            msg = await self._award_achievement(ctx, user, "fish_100")
            if msg:
                messages.append(msg)

        # unique counts
        unique = len(set(x for x in caught if x and not x.lower().startswith("treasure")))
        if unique >= 5 and "unique_5" not in earned:
            msg = await self._award_achievement(ctx, user, "unique_5")
            if msg:
                messages.append(msg)
        if unique >= 25 and "unique_25" not in earned:
            msg = await self._award_achievement(ctx, user, "unique_25")
            if msg:
                messages.append(msg)

        # sell total
        if stats.get("sell_total", 0) >= 1000 and "sell_1000" not in earned:
            msg = await self._award_achievement(ctx, user, "sell_1000")
            if msg:
                messages.append(msg)

        # bait hoarder
        # we track bait in user_conf.bait() and incrementally award in bait event handler when total crosses threshold

        # rod repaired
        # awarded in repairrod command when user repairs

        # return messages to send to ctx
        return messages

    # ---------- Small helper to update stats ----------
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
        # unique update
        stats["unique_fish"] = len(set(x for x in caught if x and not x.lower().startswith("treasure")))
        # highest value
        price = self.fish_prices.get(fish_name, 0)
        stats["highest_value_catch"] = max(stats.get("highest_value_catch", 0), price)
        # consecutive streak management: increment consecutive_catches; reset externally on failures
        stats["consecutive_catches"] = stats.get("consecutive_catches", 0) + 1
        await conf.stats.set(stats)

    # ---------- Event handlers (selected) ----------
    async def _event_nothing(self, ctx, user_conf):
        # reset consecutive streak
        stats = await user_conf.stats()
        stats["consecutive_catches"] = 0
        await user_conf.stats.set(stats)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "…No bites this time. Better luck next cast!"

    async def _event_fish(self, ctx, user_conf):
        catch = random.choice(list(self.fish_definitions.keys()))
        data = await user_conf.caught()
        data.append(catch)
        await user_conf.caught.set(data)

        # update stats
        await self._maybe_update_unique_and_highest(ctx.author, catch)
        await self._inc_stat(ctx.author, "casts", 1)

        # Award achievements that trigger on catch
        msgs = await self._check_and_award(ctx, ctx.author)

        info = self.fish_definitions[catch]
        base_msg = f"{info['emoji']} You caught a **{catch}** ({info['rarity']})!"
        # if any achievement messages, append them
        if msgs:
            return False, base_msg + "\n\n" + "\n".join(msgs)
        return False, base_msg

    async def _event_double(self, ctx, user_conf):
        catch1 = random.choice(list(self.fish_definitions.keys()))
        catch2 = random.choice(list(self.fish_definitions.keys()))
        data = await user_conf.caught()
        data.extend([catch1, catch2])
        await user_conf.caught.set(data)

        # update stats twice
        await self._maybe_update_unique_and_highest(ctx.author, catch1)
        await self._maybe_update_unique_and_highest(ctx.author, catch2)
        await self._inc_stat(ctx.author, "casts", 1)

        # award double_catch achievement
        msg_ach = None
        if not await self._has_achievement(ctx.author, "double_catch"):
            msg_ach = await self._award_achievement(ctx, ctx.author, "double_catch")

        info1 = self.fish_definitions[catch1]
        info2 = self.fish_definitions[catch2]
        base_msg = f"{info1['emoji']}{info2['emoji']} Double catch! You got **{catch1}** and **{catch2}**!"
        if msg_ach:
            return False, base_msg + "\n\n" + msg_ach
        # also check other generic achievements
        other_msgs = await self._check_and_award(ctx, ctx.author)
        if other_msgs:
            return False, base_msg + "\n\n" + "\n".join(other_msgs)
        return False, base_msg

    async def _event_treasure(self, ctx, user_conf):
        coins = random.randint(10, 60)
        new_bal = await bank.deposit_credits(ctx.author, coins)
        currency = await bank.get_currency_name(ctx.guild)
        await self._inc_stat(ctx.author, "casts", 1)
        # award treasure hunter achievement
        msg_ach = None
        if not await self._has_achievement(ctx.author, "treasure_hunter"):
            msg_ach = await self._award_achievement(ctx, ctx.author, "treasure_hunter")
        base = f"🎁 You hauled up a treasure chest and got **{coins}** {currency}! Your new balance is **{new_bal} {currency}**."
        if msg_ach:
            return False, base + "\n\n" + msg_ach
        return False, base

    async def _event_pearl(self, ctx, user_conf):
        value = random.randint(50, 150)
        new_bal = await bank.deposit_credits(ctx.author, value)
        currency = await bank.get_currency_name(ctx.guild)
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
        msg_ach = None
        if not await self._has_achievement(ctx.author, "map_collector"):
            msg_ach = await self._award_achievement(ctx, ctx.author, "map_collector")
        base = "🗺️ You found a Treasure Map! Use it later to start a treasure hunt."
        if msg_ach:
            return False, base + "\n\n" + msg_ach
        return False, base

    async def _event_shark(self, ctx, user_conf):
        data = await user_conf.caught()
        if data:
            lost = data.pop()
            await user_conf.caught.set(data)
            await self._inc_stat(ctx.author, "casts", 1)
            # break the consecutive streak on loss
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

    async def _event_bait_find(self, ctx, user_conf):
        bait_found = random.randint(1, 5)
        current_bait = await user_conf.bait()
        await user_conf.bait.set(current_bait + bait_found)
        await self._inc_stat(ctx.author, "casts", 1)
        # check bait hoarder threshold by summing total bait in stats (we'll store cumulative in stats)
        stats = await user_conf.stats()
        stats["bait_collected_total"] = stats.get("bait_collected_total", 0) + bait_found
        await user_conf.stats.set(stats)
        msg_ach = None
        if stats["bait_collected_total"] >= 20 and not await self._has_achievement(ctx.author, "bait_collector"):
            msg_ach = await self._award_achievement(ctx, ctx.author, "bait_collector")
        base = f"🪱 You found **{bait_found}** bait in the mud. You now have **{current_bait + bait_found}** bait."
        if msg_ach:
            return False, base + "\n\n" + msg_ach
        return False, base

    async def _event_sea_monster(self, ctx, user_conf):
        # chance to steal or reward
        if random.random() < 0.5:
            data = await user_conf.caught()
            lost = []
            for _ in range(min(3, len(data))):
                lost.append(data.pop(random.randrange(len(data))))
            await user_conf.caught.set(data)
            await self._inc_stat(ctx.author, "casts", 1)
            return False, f"🪸 A sea monster thrashes by and steals: {', '.join(lost)}! Escape barely."
        else:
            # reward and award achievement
            rare = random.choice(list(self.fish_definitions.keys()))
            data = await user_conf.caught()
            data.append(rare)
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, rare)
            await self._inc_stat(ctx.author, "casts", 1)
            msg_ach = None
            if not await self._has_achievement(ctx.author, "sea_monster_survivor"):
                msg_ach = await self._award_achievement(ctx, ctx.author, "sea_monster_survivor")
            base = f"🪸 You managed to hook a **{rare}** from the sea monster's grip!"
            if msg_ach:
                return False, base + "\n\n" + msg_ach
            return False, base

    # ---------- Core fish command (edits wait message) ----------
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command()
    async def fish(self, ctx):
        """Cast your line and see what you reel in (edits the waiting message with the result)."""
        user_conf = self.config.user(ctx.author)
        if await user_conf.rod_broken():
            return await ctx.send(
                "🎣 Your rod is broken! Use "
                f"`{ctx.clean_prefix}repairrod` to fix it for 20 coins."
            )

        waiting_msg = await ctx.send("🎣 You cast your line and wait patiently…")

        await asyncio.sleep(random.uniform(1.5, 4.5))

        # pick event
        keys = list(self.event_handlers.keys())
        weights = [self.event_handlers[k][1] for k in keys]
        # simple modifiers
        bait_amount = await user_conf.bait()
        if bait_amount and bait_amount > 0:
            if random.random() < 0.9:
                await user_conf.bait.set(max(0, bait_amount - 1))
            for i, k in enumerate(keys):
                if k in ("fish", "double"):
                    weights[i] = int(weights[i] * 1.6)
        luck = await user_conf.luck()
        if luck and luck > 0:
            await user_conf.luck.set(max(0, luck - 1))
            for i, k in enumerate(keys):
                if k in ("fish", "double", "treasure", "pearl"):
                    weights[i] = int(weights[i] * 2)
        weights = [max(1, w) for w in weights]
        chosen = random.choices(keys, weights=weights, k=1)[0]
        handler = self.event_handlers[chosen][0]

        result = await handler(ctx, user_conf)
        sent_directly = False
        message = None
        if isinstance(result, tuple) and len(result) >= 2:
            sent_directly, message = result[0], result[1]
        elif isinstance(result, str):
            message = result

        # Ensure edit doesn't exceed 2000 chars
        try:
            if message:
                if len(message) > 1900:
                    message = message[:1897] + "..."
                await waiting_msg.edit(content=message)
            else:
                await waiting_msg.edit(content="…An event occurred. Check the channel for details.")
        except Exception:
            if message:
                await ctx.send(message)

    # ---------- Other commands ----------
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
                name, desc, cat = self.achievements.get(aid, (aid, "", ""))
                lines.append(f"🏆 **{name}** — {desc}")
        else:
            lines.append("You haven't earned any achievements yet.")

        # Progress summaries for common milestones
        lines.append("\n**Progress**")
        lines.append(f"• Total casts: {stats.get('casts',0)}")
        lines.append(f"• Fish caught: {stats.get('fish_caught',0)}")
        unique = len(set(x for x in caught if x and not x.lower().startswith("treasure")))
        lines.append(f"• Unique species: {unique}")
        lines.append(f"• Sell total: {stats.get('sell_total',0)}")

        # Send in chunks if needed
        msg = "\n".join(lines)
        if len(msg) <= 1900:
            return await ctx.send(msg)
        # chunk
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
        # award achievement
        ach_msg = None
        if not await self._has_achievement(ctx.author, "rod_repaired"):
            ach_msg = await self._award_achievement(ctx, ctx.author, "rod_repaired")
        if ach_msg:
            await ctx.send("🔧 Your rod is repaired! " + ach_msg)
        else:
            await ctx.send("🔧 Your rod is repaired! Time to cast again.")

    @commands.command()
    async def sell(self, ctx, amount: int, *, fish_name: str):
        """Sell fish and update sell_total stat to unlock achievements."""
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

        # update sell total stat
        stats = await user_conf.stats()
        stats["sell_total"] = stats.get("sell_total", 0) + total
        await user_conf.stats.set(stats)

        # check award on sell_total
        msgs = []
        msgs += await self._check_and_award(ctx, ctx.author)

        message = f"💰 You sold {amount}× **{match}** for **{total}** {currency}!\nYour new balance is **{new_bal} {currency}**."
        if msgs:
            message += "\n\n" + "\n".join(msgs)
        await ctx.send(message)

    async def cog_unload(self):
        # placeholder if you need to cleanup
        pass


async def setup(bot):
    await bot.add_cog(Fishing(bot))



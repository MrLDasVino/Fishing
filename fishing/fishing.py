import random
import asyncio
from typing import Callable, Dict, List, Tuple, Optional

from redbot.core import commands, bank, Config


class Fishing(commands.Cog):
    """A fishing minigame with many fish types, events and bank integration."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890123)
        default_user = {
            "caught": [],        # list of fish names
            "rod_broken": False,  # whether they need a repair
            "bait": 0,            # optional bait resource
            "luck": 0,            # temporary luck modifier (minutes)
        }
        self.config.register_user(**default_user)

        # Expanded fish definitions (shortened list for brevity; keep your full list)
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

        # Derived prices for backwards compatibility
        self.fish_prices = {name: info["price"] for name, info in self.fish_definitions.items()}

        # Event registry: map event key -> (handler coroutine, weight)
        self.event_handlers: Dict[str, Tuple[Callable, int]] = {
            "nothing": (self._event_nothing, 35),
            "junk": (self._event_junk, 6),
            "fish": (self._event_fish, 28),
            "double": (self._event_double, 4),
            "shark": (self._event_shark, 3),
            "break": (self._event_break, 4),
            "treasure": (self._event_treasure, 4),
            "bottle": (self._event_bottle, 4),
            "storm": (self._event_storm, 2),
            # Extra events
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
        currency = await bank.get_currency_name(ctx.guild)
        return new_bal, currency

    # ---------- Event Handlers ----------
    # Each handler receives (ctx, user_conf) and returns a tuple (sent_directly: bool).
    # If it returns True it already sent a message; if False the caller will send the returned string.
    async def _event_nothing(self, ctx, user_conf):
        return False, "…No bites this time. Better luck next cast!"

    async def _event_junk(self, ctx, user_conf):
        junk_items = ["an old boot", "a tin can", "a broken bottle", "a soggy hat", "a rusty key"]
        return False, f"👎 You pulled up {random.choice(junk_items)}. Better luck next time!"

    async def _event_fish(self, ctx, user_conf):
        # If user has bait, slightly increase chance for better fish (handled at selection level by luck)
        catch = self._random_fish()
        data = await user_conf.caught()
        data.append(catch)
        await user_conf.caught.set(data)
        info = self.fish_definitions[catch]
        return False, f"{info['emoji']} You caught a **{catch}** ({info['rarity']})!"

    async def _event_double(self, ctx, user_conf):
        catch1 = self._random_fish()
        catch2 = self._random_fish()
        data = await user_conf.caught()
        data.extend([catch1, catch2])
        await user_conf.caught.set(data)
        info1 = self.fish_definitions[catch1]
        info2 = self.fish_definitions[catch2]
        return False, f"{info1['emoji']}{info2['emoji']} Double catch! You got **{catch1}** and **{catch2}**!"

    async def _event_shark(self, ctx, user_conf):
        data = await user_conf.caught()
        if data:
            lost = data.pop()
            await user_conf.caught.set(data)
            info = self.fish_definitions.get(lost, {})
            emoji = info.get("emoji", "🦈")
            return False, f"{emoji} A shark snatches your **{lost}**! Ouch."
        return False, "🦈 A shark swims by, but you had nothing yet to lose."

    async def _event_break(self, ctx, user_conf):
        await user_conf.rod_broken.set(True)
        return False, "Snap! Your rod just broke. You’ll need to repair it."

    async def _event_treasure(self, ctx, user_conf):
        coins = random.randint(10, 60)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        return False, f"🎁 You hauled up a treasure chest and got **{coins}** {currency}! Your new balance is **{new_bal}** {currency}."

    async def _event_bottle(self, ctx, user_conf):
        coins = random.randint(5, 30)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        return False, f"📜 You found a message in a bottle and earned **{coins}** {currency}! Your new balance is **{new_bal}** {currency}."

    async def _event_storm(self, ctx, user_conf):
        # small chance rod breaks in storm
        if random.random() < 0.2:
            await user_conf.rod_broken.set(True)
            return False, "⛈️ A sudden storm! Your line snaps back and your rod breaks."
        return False, "⛈️ A sudden storm! Your line snaps back with nothing to show."

    async def _event_net(self, ctx, user_conf):
        # You haul up a net full of small fish and some junk
        net_fish_count = random.randint(1, 5)
        caught = [self._random_fish() for _ in range(net_fish_count)]
        data = await user_conf.caught()
        data.extend(caught)
        await user_conf.caught.set(data)
        names = ", ".join(caught)
        return False, f"🕸️ You snagged an old net with {net_fish_count} things tangled inside: {names}."

    async def _event_bait_find(self, ctx, user_conf):
        # Find bait resource
        bait_found = random.randint(1, 5)
        current_bait = await user_conf.bait()
        await user_conf.bait.set(current_bait + bait_found)
        return False, f"🪱 You found **{bait_found}** bait in the mud. Use bait to increase catch quality."

    async def _event_lucky_streak(self, ctx, user_conf):
        # Grant temporary luck that increases higher-fish chance for next few minutes
        # We'll store minutes in 'luck' as an integer for simplicity.
        await user_conf.luck.set(5)  # 5-turns/minutes semantics for your design
        return False, "✨ Lucky streak! Your next few casts are more likely to find rare fish."

    async def _event_curse(self, ctx, user_conf):
        # A small bad event: lose some coins or rod breaks
        if random.random() < 0.5:
            # lose coins if possible
            loss = random.randint(5, 25)
            bal = await bank.get_balance(ctx.author)
            if bal >= loss:
                await bank.withdraw_credits(ctx.author, loss)
                currency = await bank.get_currency_name(ctx.guild)
                return False, f"🔮 An old charm curses you — you lost **{loss}** {currency}."
        await user_conf.rod_broken.set(True)
        return False, "🔮 A cursed tug! Your rod is damaged by some dark force."

    async def _event_merchant(self, ctx, user_conf):
        # A traveling merchant offers to buy one of your fish for a premium
        inventory = await user_conf.caught()
        if not inventory:
            # merchant leaves a small coin tip
            tips = random.randint(1, 10)
            new_bal, currency = await self._deposit(ctx.author, tips, ctx)
            return False, f"🧑‍🚀 A traveling merchant stops by and leaves **{tips}** {currency} as thanks."
        # pick a random fish to offer
        fish = random.choice(inventory)
        premium = int(self.fish_prices.get(fish, 10) * random.uniform(1.2, 2.0))
        # merchant buys it automatically
        inventory.remove(fish)
        await user_conf.caught.set(inventory)
        new_bal, currency = await self._deposit(ctx.author, premium, ctx)
        return False, f"🧑‍🚀 A merchant offers **{premium} {currency}** for your **{fish}** and buys it on the spot."

    async def _event_pearl(self, ctx, user_conf):
        # Find a rare pearl -> currency or special item (we'll do currency)
        value = random.randint(50, 150)
        new_bal, currency = await self._deposit(ctx.author, value, ctx)
        return False, f"💎 You pry out a lustrous pearl worth **{value} {currency}**. Your new balance is **{new_bal}** {currency}."

    async def _event_map(self, ctx, user_conf):
        # Find a treasure map (store as an "item" by adding a string to caught or just notify)
        data = await user_conf.caught()
        data.append("Treasure Map")
        await user_conf.caught.set(data)
        return False, "🗺️ You found a Treasure Map! Use it later to start a treasure hunt."

    async def _event_sea_monster(self, ctx, user_conf):
        # Very rare: a sea monster fight. Could lose rod or gain rare fish
        roll = random.random()
        if roll < 0.5:
            # monster steals a bunch
            data = await user_conf.caught()
            lost = []
            for _ in range(min(3, len(data))):
                if data:
                    lost.append(data.pop(random.randrange(len(data))))
            await user_conf.caught.set(data)
            if lost:
                return False, f"🪸 A sea monster thrashes by and steals: {', '.join(lost)}! Escape barely."
            # else fallback to terrifying nothing
            return False, "🪸 A sea monster surfaced and scared you off, nothing to show."
        else:
            # rare reward
            rare = self._random_fish()
            data = await user_conf.caught()
            data.append(rare)
            await user_conf.caught.set(data)
            return False, f"🪸 In a wild turn, you managed to hook a **{rare}** from the sea monster's grip!"

    async def _event_hook_snag(self, ctx, user_conf):
        # Hook gets snagged — lose next turn or pay to free
        # We'll just break the rod sometimes
        if random.random() < 0.6:
            await user_conf.rod_broken.set(True)
            return False, "⛓️ Your hook snagged on something sharp and your rod snapped!"
        else:
            return False, "⛓️ Your hook snagged on an old anchor but you freed it."

    async def _event_festival(self, ctx, user_conf):
        # Periodic festival event that increases prices for selling next time (store as luck-like flag).
        await user_conf.luck.set(3)  # reuse luck flag as a 'festival' boost
        return False, "🎉 Festival of Fishermen! Sold fish pay more for a short while (apply server logic)."

    async def _event_charity(self, ctx, user_conf):
        # Optionally donate coins automatically (random small amount)
        bal = await bank.get_balance(ctx.author)
        donation = min(random.randint(1, 10), bal)
        if donation > 0:
            await bank.withdraw_credits(ctx.author, donation)
            currency = await bank.get_currency_name(ctx.guild)
            return False, f"🤝 You found a stray begging fish and gave **{donation}** {currency} to a community cause."
        return False, "🤝 You feel generous but have no funds to donate."

    async def _event_salvage(self, ctx, user_conf):
        # Salvage useful parts -> small currency + chance of item (Treasure Map)
        coins = random.randint(5, 40)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        # small chance for map
        if random.random() < 0.15:
            data = await user_conf.caught()
            data.append("Treasure Map")
            await user_conf.caught.set(data)
            return False, f"🛠️ You salvage usable pieces and find **{coins} {currency}** and a Treasure Map!"
        return False, f"🛠️ You salvage metal and get **{coins} {currency}**."

    async def _event_message(self, ctx, user_conf):
        # Flavor: a mysterious message granting a bonus (small coin or bait)
        if random.random() < 0.5:
            bait = random.randint(1, 3)
            current = await user_conf.bait()
            await user_conf.bait.set(current + bait)
            return False, f"✉️ A friendly note contains **{bait}** bait. Use it to attract better fish."
        coins = random.randint(5, 20)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        return False, f"✉️ A note promises a small reward. You find **{coins} {currency}** tucked inside. New balance: **{new_bal}** {currency}."

    # ---------- Core fish command ----------
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command()
    async def fish(self, ctx):
        """Cast your line and see what you reel in (now with many events)."""
        user_conf = self.config.user(ctx.author)
        if await user_conf.rod_broken():
            return await ctx.send(
                "🎣 Your rod is broken! Use "
                f"`{ctx.clean_prefix}repairrod` to fix it for 20 coins."
            )

        await ctx.send("🎣 You cast your line and wait patiently…")
        await asyncio.sleep(random.uniform(1.5, 5.5))

        # Build event selection based on handler weights and dynamic modifiers
        keys = list(self.event_handlers.keys())
        weights = [self.event_handlers[k][1] for k in keys]

        # Apply simple modifiers: if user has bait, increase fish and double weights
        bait_amount = await user_conf.bait()
        if bait_amount > 0:
            # consume one bait on cast with some chance
            if random.random() < 0.9:
                await user_conf.bait.set(max(0, bait_amount - 1))
            # raise fish/double weights
            for i, k in enumerate(keys):
                if k in ("fish", "double"):
                    weights[i] = int(weights[i] * 1.6)

        # If user has a temporary 'luck' flag, bias towards rarer/beneficial events
        luck = await user_conf.luck()
        if luck and luck > 0:
            # reduce luck token
            await user_conf.luck.set(max(0, luck - 1))
            # boost fish and treasure/chance events
            for i, k in enumerate(keys):
                if k in ("fish", "double", "treasure", "pearl", "merchant"):
                    weights[i] = int(weights[i] * 2)

        # Ensure all weights positive
        weights = [max(1, w) for w in weights]

        # pick event
        chosen = random.choices(keys, weights=weights, k=1)[0]
        handler = self.event_handlers[chosen][0]

        # Call handler
        sent_directly_or_tuple = await handler(ctx, user_conf)
        # Handlers return either (False, message) or True if they already sent
        if isinstance(sent_directly_or_tuple, tuple):
            sent_directly, message = sent_directly_or_tuple
            if not sent_directly:
                await ctx.send(message)
        elif sent_directly_or_tuple is False:
            # fallback message unknown
            await ctx.send("…Something strange happened while reeling in.")
        # If handler already sent, nothing to do

    # ---------- Other commands (fishlist, fishstats, repairrod, sell) ----------
    @commands.command()
    async def fishlist(self, ctx, *, filter_by: str = None):
        """Show available fish with price and rarity. Optionally filter by rarity or biome."""
        lines = []
        rarity_order = {"Common": 0, "Uncommon": 1, "Rare": 2, "Epic": 3, "Legendary": 4, "Mythic": 5, "Boss": 6}
        items = list(self.fish_definitions.items())

        if filter_by:
            key = filter_by.strip().lower()
            filtered = []
            for name, info in items:
                if info.get("rarity", "").lower() == key:
                    filtered.append((name, info))
                    continue
                if key in (info.get("biome", "").lower()):
                    filtered.append((name, info))
                    continue
                if key in name.lower():
                    filtered.append((name, info))
            items = filtered

        items = sorted(items, key=lambda kv: (rarity_order.get(kv[1].get("rarity", ""), 99), -kv[1].get("price", 0)))
        for name, info in items:
            emoji = info.get("emoji", "")
            rarity = info.get("rarity", "Unknown")
            price = info.get("price", 0)
            biome = info.get("biome", "")
            lines.append(f"{emoji} **{name}** — {rarity} — Price: **{price}** — {biome}")

        if not lines:
            return await ctx.send("No fish match that filter.")

        header = "**Available Fish**\n\n"
        chunk_size = 1900
        current = header
        for line in lines:
            if len(current) + len(line) + 1 > chunk_size:
                await ctx.send(current)
                current = ""
            if current:
                current += "\n" + line
            else:
                current = line
        if current:
            await ctx.send(current)

    @commands.command()
    async def fishstats(self, ctx):
        """View how many fish you’ve caught and your bank balance."""
        data = await self.config.user(ctx.author).all()
        caught = data["caught"]
        if not caught:
            return await ctx.send(
                f"You haven't caught anything yet. Use "
                f"`{ctx.clean_prefix}fish` to start fishing!"
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

        await ctx.send(
            f"**{ctx.author.display_name}'s Fishing Stats**\n\n"
            f"Balance: **{bal}** {currency}\n"
            f"{breakdown}"
        )

    @commands.command()
    async def repairrod(self, ctx):
        """Repair your broken rod for 20 coins."""
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
        await ctx.send("🔧 Your rod is repaired! Time to cast again.")

    @commands.command()
    async def sell(self, ctx, amount: int, *, fish_name: str):
        """
        Sell a number of fish for your server currency.
        Usage: [p]sell 3 Medium Fish
        """
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

        await ctx.send(
            f"💰 You sold {amount}× **{match}** for **{total}** {currency}!\n"
            f"Your new balance is **{new_bal}** {currency}."
        )


async def setup(bot):
    await bot.add_cog(Fishing(bot))


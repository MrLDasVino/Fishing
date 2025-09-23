import random
import asyncio

from redbot.core import commands, bank, Config


class Fishing(commands.Cog):
    """A simple fishing minigame with many fish types, random events and bank integration."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890123)
        default_user = {
            "caught": [],        # list of fish names
            "rod_broken": False  # whether they need a repair
        }
        self.config.register_user(**default_user)

        # Expanded fish definitions
        # weight controls spawn probability; price is currency value
        # rarity is for display only; biome is flavour text
        self.fish_definitions = {
            "Tiny Minnow": {"weight": 200, "price": 2, "emoji": "><>", "rarity": "Common", "biome": "Pond"},
            "Mosquito Fish": {"weight": 180, "price": 3, "emoji": "🐟", "rarity": "Common", "biome": "Marsh"},
            "Bluegill": {"weight": 160, "price": 5, "emoji": "🐠", "rarity": "Common", "biome": "Pond"},
            "Silverside": {"weight": 150, "price": 6, "emoji": "🐟", "rarity": "Common", "biome": "Coastal"},
            "Shiner": {"weight": 140, "price": 6, "emoji": "🔆", "rarity": "Common", "biome": "River"},
            "Perch": {"weight": 120, "price": 8, "emoji": "🐡", "rarity": "Uncommon", "biome": "Lake"},
            "Koi": {"weight": 110, "price": 12, "emoji": "🎏", "rarity": "Uncommon", "biome": "Garden Pond"},
            "Glass Eel": {"weight": 100, "price": 10, "emoji": "🔮", "rarity": "Uncommon", "biome": "Estuary"},
            "Gudgeon": {"weight": 95, "price": 9, "emoji": "🐟", "rarity": "Common", "biome": "Stream"},
            "Carp": {"weight": 90, "price": 11, "emoji": "🐠", "rarity": "Uncommon", "biome": "Lake"},
            "Trout": {"weight": 80, "price": 14, "emoji": "🎣", "rarity": "Uncommon", "biome": "Stream"},
            "Rainbow Trout": {"weight": 75, "price": 18, "emoji": "🌈", "rarity": "Rare", "biome": "River"},
            "Salmon": {"weight": 70, "price": 20, "emoji": "🐟", "rarity": "Rare", "biome": "River"},
            "Char": {"weight": 65, "price": 18, "emoji": "❄️", "rarity": "Rare", "biome": "Cold Lake"},
            "Pike": {"weight": 60, "price": 22, "emoji": "🦈", "rarity": "Rare", "biome": "Freshwater"},
            "Largemouth Bass": {"weight": 50, "price": 26, "emoji": "🎣", "rarity": "Rare", "biome": "Lake"},
            "Smallmouth Bass": {"weight": 48, "price": 24, "emoji": "🐟", "rarity": "Rare", "biome": "River"},
            "Catfish": {"weight": 45, "price": 28, "emoji": "🐱‍🏍", "rarity": "Rare", "biome": "River"},
            "Sturgeon": {"weight": 35, "price": 45, "emoji": "🐡", "rarity": "Epic", "biome": "River"},
            "Eel": {"weight": 40, "price": 30, "emoji": "🪱", "rarity": "Rare", "biome": "Estuary"},
            "Flounder": {"weight": 38, "price": 30, "emoji": "🪸", "rarity": "Rare", "biome": "Coastal"},
            "Halibut": {"weight": 30, "price": 36, "emoji": "🐟", "rarity": "Epic", "biome": "Cold Ocean"},
            "Mackerel": {"weight": 55, "price": 16, "emoji": "🐟", "rarity": "Common", "biome": "Coastal"},
            "Herring": {"weight": 85, "price": 7, "emoji": "🐠", "rarity": "Common", "biome": "Coastal"},
            "Sardine": {"weight": 130, "price": 4, "emoji": "🐟", "rarity": "Common", "biome": "Coastal"},
            "Tuna": {"weight": 20, "price": 75, "emoji": "🐋", "rarity": "Legendary", "biome": "Open Ocean"},
            "Mahi Mahi": {"weight": 18, "price": 60, "emoji": "🐬", "rarity": "Epic", "biome": "Tropical Ocean"},
            "Swordfish": {"weight": 10, "price": 120, "emoji": "🗡️", "rarity": "Legendary", "biome": "Open Ocean"},
            "Marlin": {"weight": 8, "price": 150, "emoji": "🏹", "rarity": "Legendary", "biome": "Deep Ocean"},
            "Blue Marlin": {"weight": 6, "price": 180, "emoji": "🔱", "rarity": "Mythic", "biome": "Deep Ocean"},
            "Giant Grouper": {"weight": 12, "price": 95, "emoji": "🐋", "rarity": "Legendary", "biome": "Reef"},
            "Snapper": {"weight": 42, "price": 32, "emoji": "🐠", "rarity": "Rare", "biome": "Reef"},
            "Amberjack": {"weight": 28, "price": 48, "emoji": "🪝", "rarity": "Epic", "biome": "Offshore"},
            "Yellowtail": {"weight": 32, "price": 38, "emoji": "🟡", "rarity": "Rare", "biome": "Coastal"},
            "Rockfish": {"weight": 46, "price": 20, "emoji": "🪨", "rarity": "Uncommon", "biome": "Reef"},
            "Lionfish": {"weight": 22, "price": 55, "emoji": "🦁", "rarity": "Epic", "biome": "Reef"},
            "Pufferfish": {"weight": 16, "price": 48, "emoji": "🎈", "rarity": "Epic", "biome": "Reef"},
            "Electric Ray": {"weight": 14, "price": 80, "emoji": "⚡", "rarity": "Legendary", "biome": "Ocean Floor"},
            "Hammerhead": {"weight": 5, "price": 140, "emoji": "🔨", "rarity": "Mythic", "biome": "Open Ocean"},
            "Great White": {"weight": 2, "price": 0, "emoji": "🦈", "rarity": "Boss", "biome": "Deep Ocean"},
            "Dragonfish": {"weight": 1, "price": 300, "emoji": "🐉", "rarity": "Mythic", "biome": "Abyssal"},
            "Anglerfish": {"weight": 3, "price": 200, "emoji": "🎣", "rarity": "Mythic", "biome": "Abyssal"},
            "Ghost Carp": {"weight": 6, "price": 90, "emoji": "👻", "rarity": "Legendary", "biome": "Murky Lake"},
            "Harlequin Shrimp": {"weight": 26, "price": 44, "emoji": "🦐", "rarity": "Epic", "biome": "Reef"},
            "Mudskipper": {"weight": 115, "price": 7, "emoji": "🐸", "rarity": "Common", "biome": "Mangrove"},
            "Butterfish": {"weight": 88, "price": 9, "emoji": "🧈", "rarity": "Common", "biome": "Coastal"},
            "Octopus": {"weight": 24, "price": 70, "emoji": "🐙", "rarity": "Epic", "biome": "Reef"},
            "Cuttlefish": {"weight": 34, "price": 34, "emoji": "🦑", "rarity": "Rare", "biome": "Coastal"},
            "Sea Urchin": {"weight": 60, "price": 18, "emoji": "🟣", "rarity": "Uncommon", "biome": "Rocky Shore"},
            "Seahorse": {"weight": 40, "price": 25, "emoji": "🐴", "rarity": "Rare", "biome": "Seagrass"},
        }


        # Derive fish_prices automatically
        self.fish_prices = {name: info["price"] for name, info in self.fish_definitions.items()}

    # Helper: pick a fish name using weights
    def _random_fish(self):
        names = list(self.fish_definitions.keys())
        weights = [self.fish_definitions[n]["weight"] for n in names]
        return random.choices(names, weights=weights, k=1)[0]

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

        await ctx.send("🎣 You cast your line and wait patiently…")
        await asyncio.sleep(random.uniform(2, 6))

        event, = random.choices(
            [
                "nothing",
                "junk",
                "fish",
                "double",
                "shark",
                "break",
                "treasure",
                "bottle",
                "storm",
            ],
            weights=[40, 5, 30, 5, 3, 5, 5, 5, 2],
            k=1,
        )

        if event == "nothing":
            return await ctx.send("…No bites this time. Better luck next cast!")

        if event == "junk":
            junk_items = ["an old boot", "a tin can", "a broken bottle", "a soggy hat"]
            return await ctx.send(f"👎 You pulled up {random.choice(junk_items)}. Better luck next time!")

        if event == "fish":
            catch = self._random_fish()
            data = await user_conf.caught()
            data.append(catch)
            await user_conf.caught.set(data)
            info = self.fish_definitions[catch]
            return await ctx.send(f"{info['emoji']} You caught a **{catch}** ({info['rarity']})!")

        if event == "double":
            catch1 = self._random_fish()
            catch2 = self._random_fish()
            data = await user_conf.caught()
            data.extend([catch1, catch2])
            await user_conf.caught.set(data)
            info1 = self.fish_definitions[catch1]
            info2 = self.fish_definitions[catch2]
            return await ctx.send(
                f"{info1['emoji']}{info2['emoji']} Double catch! You got **{catch1}** ({info1['rarity']}) "
                f"and **{catch2}** ({info2['rarity']})!"
            )

        if event == "shark":
            data = await user_conf.caught()
            if data:
                lost = data.pop()
                await user_conf.caught.set(data)
                info = self.fish_definitions.get(lost, {})
                emoji = info.get("emoji", "🦈")
                return await ctx.send(f"{emoji} A shark snatches your **{lost}**! Ouch.")
            return await ctx.send("🦈 A shark swims by, but you had nothing yet to lose.")

        if event == "break":
            await user_conf.rod_broken.set(True)
            return await ctx.send("Snap! Your rod just broke. You’ll need to repair it.")

        if event == "treasure":
            coins = random.randint(10, 50)
            new_bal = await bank.deposit_credits(ctx.author, coins)
            currency = await bank.get_currency_name(ctx.guild)
            return await ctx.send(
                f"🎁 You hauled up a treasure chest and got **{coins}** {currency}!\n"
                f"Your new balance is **{new_bal}** {currency}."
            )

        if event == "bottle":
            coins = random.randint(5, 25)
            new_bal = await bank.deposit_credits(ctx.author, coins)
            currency = await bank.get_currency_name(ctx.guild)
            return await ctx.send(
                f"📜 You found a message in a bottle and earned **{coins}** {currency}!\n"
                f"Your new balance is **{new_bal}** {currency}."
            )

        if event == "storm":
            return await ctx.send("⛈️ A sudden storm! Your line snaps back with nothing to show.")

    @commands.command()
    async def fishlist(self, ctx):
        """Show available fish with price and rarity."""
        lines = []
        # Sort by rarity then price descending as an example
        rarity_order = {"Common": 0, "Uncommon": 1, "Rare": 2, "Epic": 3, "Legendary": 4, "Mythic": 5}
        items = sorted(
            self.fish_definitions.items(),
            key=lambda kv: (rarity_order.get(kv[1]["rarity"], 99), -kv[1]["price"])
        )
        for name, info in items:
            lines.append(f"{info['emoji']} **{name}** — {info['rarity']} — Price: **{info['price']}**")
        # Send in chunks if long
        chunk = "\n".join(lines)
        await ctx.send(f"**Available Fish**\n\n{chunk}")

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

        # Build catch counts
        counts = {}
        for fish in caught:
            counts[fish] = counts.get(fish, 0) + 1
        breakdown = "\n".join(
            f"• {self.fish_definitions.get(fish, {}).get('emoji','')} {fish}: {count}"
            for fish, count in counts.items()
        )

        # Get bank balance
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

        # Case-insensitive match
        match = next(
            (fish for fish in self.fish_definitions if fish.lower() == fish_name.lower()),
            None,
        )
        if not match:
            valid = ", ".join(self.fish_definitions.keys())
            return await ctx.send(f"❌ Unknown fish `{fish_name}`. You can sell: {valid}")

        have = inventory.count(match)
        if have < amount:
            return await ctx.send(f"❌ You only have {have}× **{match}** to sell.")

        # Remove sold fish
        for _ in range(amount):
            inventory.remove(match)
        await user_conf.caught.set(inventory)

        # Deposit to bank
        total = self.fish_definitions[match]["price"] * amount
        new_bal = await bank.deposit_credits(ctx.author, total)
        currency = await bank.get_currency_name(ctx.guild)

        await ctx.send(
            f"💰 You sold {amount}× **{match}** for **{total}** {currency}!\n"
            f"Your new balance is **{new_bal}** {currency}."
        )


async def setup(bot):
    """Entry point for Red to load this cog."""
    await bot.add_cog(Fishing(bot))

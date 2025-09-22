import random
import asyncio
from redbot.core import commands, bank, Config


class Fishing(commands.Cog):
    """A simple fishing minigame with random events."""

    def __init__(self, bot):
        self.bot = bot
        # Unique identifier for our config store
        self.config = Config.get_conf(self, identifier=1234567890123)
        default_user = {
            "caught": [],       # list of fish names
            "coins": 0,         # currency
            "rod_broken": False # whether they need a repair
        }
        self.config.register_user(**default_user)
        
                # Sale prices for each fish
        self.fish_prices = {
            "Tiny Fish": 5,
            "Small Fish": 10,
            "Medium Fish": 20,
            "Large Fish": 40,
            "Legendary Fish": 100,
        }

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command()
    async def fish(self, ctx):
        """Cast your line and see what you reel in."""
        user_conf = self.config.user(ctx.author)
        if await user_conf.rod_broken():
            return await ctx.send(
                "🎣 Your rod is broken! Use `{}repairrod` (20 coins) to fix it.".format(ctx.prefix)
            )

        await ctx.send("🎣 You cast your line and wait patiently...")
        await asyncio.sleep(random.uniform(2, 6))

        # Decide event
        event = random.choices(
            ["nothing", "fish", "break", "treasure"],
            weights=[50, 40, 5, 5],
            k=1,
        )[0]

        if event == "nothing":
            return await ctx.send("…No bites this time. Better luck next cast!")

        if event == "break":
            await user_conf.rod_broken.set(True)
            return await ctx.send("Snap! Your rod just broke. You’ll need to repair it.")

        if event == "treasure":
            coins = random.randint(10, 50)
            old = await user_conf.coins()
            await user_conf.coins.set(old + coins)
            return await ctx.send(
                f"🎁 You hauled up an old treasure chest and found **{coins}** coins!"
            )

        # else: fish
        fishes = [
            ("Tiny Fish", 60),
            ("Small Fish", 25),
            ("Medium Fish", 10),
            ("Large Fish", 4),
            ("Legendary Fish", 1),
        ]
        names, weights = zip(*fishes)
        catch = random.choices(names, weights=weights, k=1)[0]
        data = await user_conf.caught()
        data.append(catch)
        await user_conf.caught.set(data)
        await ctx.send(f"🐟 You caught a **{catch}**!")

    @commands.command()
    async def fishstats(self, ctx):
        """View how many fish you’ve caught and your coin balance."""
        data = await self.config.user(ctx.author).all()
        caught = data["caught"]
        coins = data["coins"]

        if not caught:
            return await ctx.send(
                f"You haven't caught anything yet. Use `{ctx.prefix}fish` to start fishing!"
            )

        counts = {}
        for fish in caught:
            counts[fish] = counts.get(fish, 0) + 1
        breakdown = "\n".join(f"• {fish}: {count}" for fish, count in counts.items())
        await ctx.send(
            f"**{ctx.author.display_name}'s Fishing Stats**\n\n"
            f"Coins: **{coins}**\n"
            f"{breakdown}"
        )

    @commands.command()
    async def repairrod(self, ctx):
        """Repair your broken rod for 20 coins."""
        user_conf = self.config.user(ctx.author)
        broken = await user_conf.rod_broken()
        coins = await user_conf.coins()

        if not broken:
            return await ctx.send("Your rod is already in good shape!")

        cost = 20
        if coins < cost:
            return await ctx.send(
                f"You need **{cost}** coins to repair your rod, but you only have **{coins}**."
            )

        await user_conf.rod_broken.set(False)
        await user_conf.coins.set(coins - cost)
        await ctx.send("🔧 Your rod is repaired! Time to cast again.")
        
    @commands.command()
    async def sell(self, ctx, amount: int, *, fish_name: str):
        """
        Sell a number of fish for Red credits.
        Usage: [p]sell 3 Medium Fish
        """
        user_conf = self.config.user(ctx.author)
        inventory = await user_conf.caught()

        # Case-insensitive lookup
        match = next(
            (fish for fish in self.fish_prices if fish.lower() == fish_name.lower()),
            None
        )
        if not match:
            valid = ", ".join(self.fish_prices.keys())
            return await ctx.send(f"❌ Unknown fish `{fish_name}`. You can sell: {valid}")

        have = inventory.count(match)
        if have < amount:
            return await ctx.send(f"❌ You only have {have}× **{match}** to sell.")

        # Remove sold fish from inventory
        for _ in range(amount):
            inventory.remove(match)
        await user_conf.caught.set(inventory)

        # Deposit to bank
        total = self.fish_prices[match] * amount
        new_balance = await deposit_credits(ctx.author, total)
        currency    = await get_currency_name(ctx.guild)

        await ctx.send(
            f"💰 You sold {amount}× **{match}** for **{total}** {currency}.\n"
            f"Your new balance is **{new_balance}** {currency}."
        )
    

async def setup(bot):
    await bot.add_cog(Fishing(bot))

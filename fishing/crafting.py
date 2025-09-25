# cogs/fishing/crafting.py

from redbot.core import commands
from .data import crafting_recipes
from .helpers import deposit, paginate

class Crafting(commands.Cog):
    def __init__(self, config):
        self.config = config

    @commands.command()
    async def craftlist(self, ctx):
        """Show all crafting recipes."""
        embeds = []
        image_url = "https://files.catbox.moe/dt1sh1.png"
        items = list(crafting_recipes.items())
        per_page = 6
        for i in range(0, len(items), per_page):
            chunk = items[i:i+per_page]
            emb = discord.Embed(title="Crafting Recipes", colour=discord.Colour.teal())
            emb.set_thumbnail(url=image_url)
            for rid, info in chunk:
                reqs = info["requirements"]
                req_text = ", ".join(f"{k}:{v}" for k, v in reqs.items()) or "None"
                result = info["result"]
                emb.add_field(
                    name=f"{info['name']} — Usage: `!craft {rid}`",
                    value=(f"{info['description']}\n"
                           f"**Requires:** {req_text}\n"
                           f"**Result:** {result}"),
                    inline=False,
                )
            emb.set_footer(text=f"Page {i//per_page+1}/{(len(items)-1)//per_page+1}")
            embeds.append(emb)
        await paginate(ctx, embeds)

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
            elif key.startswith("item:"):
                item_name = key.split(":", 1)[1]
                # pull inventory once
                items_list = await user_conf.items()
                have = items_list.count(item_name)
                if have < needed:
                    ok = False
                    break
                # consume exactly `needed` copies
                new_items = []
                removed = 0
                for it in items_list:
                    if it == item_name and removed < needed:
                        removed += 1
                        continue
                    new_items.append(it)
                await user_conf.items.set(new_items)                
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
            await self._inc_stat(ctx.author, "crafts_done", 1)
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
                msg = await self._award_achievement(ctx, ctx.author, "first_chum")
                if msg:
                    messages.append(msg)
                
            if recipe_id == "trophy" and not await self._has_achievement(ctx.author, "trophy_maker"):
                msg = await self._award_achievement(ctx, ctx.author, "trophy_maker")
                if msg:
                    messages.append(msg)
                
        except Exception:
            pass        
        await ctx.send("\n".join(messages))
        pass

    @commands.command()
    async def useitem(self, ctx, *, item_name: str):
        """Use a consumable item from your items list (e.g., Chum, Stew Bowl, Mystery Box)."""
        user_conf = self.config.user(ctx.author)
        items = await user_conf.items()
        # find exact item
        match = next((it for it in items if it.lower() == item_name.lower()), None)
        if not match:
            return await ctx.send(f"❌ You don’t have **{item_name}** in your items.")
        
        # remove it once
        items.remove(match)
        await user_conf.items.set(items)

        # handle each new recipe output
        if match == "Trophy":
            new_bal, currency = await self._deposit(ctx.author, 100, ctx)
            return await ctx.send(
                f"🏆 You used a **Trophy** and received **100 {currency}**! "
                f"New balance: **{new_bal} {currency}**."
            )
            
        if match == "Stew Bowl":
            # +2 luck for next 5 casts
            cur = await user_conf.luck()
            await user_conf.luck.set(cur + 2)
            return await ctx.send(
                "🥣 You eat the **Hearty Fish Stew**. Your luck increases by **2** for the next casts!"
            )

        if match == "Stormcaller Lure":
            cur = await user_conf.luck()
            await user_conf.luck.set(cur + 3)
            return await ctx.send(
                "🌀 You attach the **Stormcaller Lure**. Next cast chance of Rare+ fish is doubled!"
            )

        if match == "Plaque":
            # sellable trophy plaque
            new_bal, currency = await self._deposit(ctx.author, 200, ctx)
            return await ctx.send(
                f"🏆 You display the **Angler’s Plaque** and gain **200 {currency}**! "
                f"New balance: **{new_bal} {currency}**."
            )

        if match == "Fish Oil Flask":
            # instant coins
            new_bal, currency = await self._deposit(ctx.author, 50, ctx)
            return await ctx.send(
                f"🛢️ You extract the **Fish Oil Flask** for **50 {currency}**. "
                f"New balance: **{new_bal} {currency}**."
            )

        if match == "Nutrient Pack":
            # gain 3 bait immediately
            cur = await user_conf.bait()
            await user_conf.bait.set(cur + 3)
            return await ctx.send(
                f"🌱 You use the **Nutrient Pack**. You gain **3** bait (now {cur+3})."
            )

        if match == "Rod Coil":
            # temporary rod durability buff
            await ctx.send(
                "⚙️ You install the **Durability Coil**. Your rod break chance is halved for your next 100 casts!"
            )
            # optionally you could track a counter in config to expire this buff after 100 casts

        if match == "Tonic Bottle":
            # reset streak + coin bonus
            stats = await user_conf.stats()
            stats["consecutive_catches"] = 0
            await user_conf.stats.set(stats)
            new_bal, currency = await self._deposit(ctx.author, 200, ctx)
            return await ctx.send(
                f"🧪 You drink the **Mystic Angler’s Tonic**. Your catch streak resets and you gain **200 {currency}**!"
            )

        if match == "Festival Pack":
            cur = await user_conf.luck()
            await user_conf.luck.set(cur + 5)
            return await ctx.send(
                "🎊 You open the **Festival Pack**! Next cast triggers a Festival event for bonus rewards."
            )

        if match == "Biome Explorer’s Journal":
            new_bal, currency = await self._deposit(ctx.author, 100, ctx)
            return await ctx.send(
                f"📖 You study the **Biome Explorer’s Journal**. Rare biome fish chance +10% for 10 casts, "
                f"and you gain **100 {currency}**! New balance: **{new_bal} {currency}**."
            )

        if match == "Mystery Box":
            # randomize one of three rewards
            choice = random.choice(["Rod Core", "coins", "Treasure Map"])
            if choice == "Rod Core":
                items = await user_conf.items()
                items.append("Rod Core")
                await user_conf.items.set(items)
                return await ctx.send("📦 Mystery Box! You found a **Rod Core** inside!")
            elif choice == "Treasure Map":
                items = await user_conf.items()
                items.append("Treasure Map")
                await user_conf.items.set(items)
                return await ctx.send("📦 Mystery Box! You found a **Treasure Map** inside!")
            else:
                amt = random.randint(100, 300)
                new_bal, currency = await self._deposit(ctx.author, amt, ctx)
                return await ctx.send(f"📦 Mystery Box! You got **{amt} {currency}**!")

        # fallback for older items
        if match == "Chum":
            cur = await user_conf.luck()
            await user_conf.luck.set(cur + 3)
            return await ctx.send("🪼 You used **Chum**. Your luck increased by **3** for the next casts.")

        if match == "Treasure Map":
            coins = random.randint(20, 100)
            new_bal, currency = await self._deposit(ctx.author, coins, ctx)
            return await ctx.send(
                f"🗺️ You follow the map and dig up **{coins} {currency}**! New balance: **{new_bal} {currency}**."
            )

        # anything else isn’t usable
        return await ctx.send(f"❌ **{match}** cannot be used directly.")
        pass

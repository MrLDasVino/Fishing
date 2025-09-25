# cogs/fishing/commands.py

import random
import asyncio
from redbot.core import commands
from .helpers import deposit, choose_random, paginate
from .achievements import award_achievements

class FishingCommands(commands.Cog):
    def __init__(self, config, event_mgr, ach_mgr):
        self.config    = config
        self.event_mgr = event_mgr
        self.ach_mgr   = ach_mgr

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command()
    @award_achievements
    async def fish(self, ctx):
        """Core fishing command."""
        user_conf = self.config.user(ctx.author)
        if await user_conf.rod_broken():
            return await ctx.send("🔧 Your rod is broken. Repair with `!repairrod` first.")
        m = await ctx.send("🎣 Casting your line…")
        await asyncio.sleep(random.uniform(1.5, 5.5))
        result = await self.event_mgr.pick_and_run(ctx, user_conf)
        # result might be (False, text) or str
        text = result[1] if isinstance(result, tuple) else result
        await m.edit(content=text)

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
        pass

    @commands.command()
    async def fishstats(self, ctx):
        """View how many fish you’ve caught, your items, and your bank balance (embed, paged)."""
        data = await self.config.user(ctx.author).all()
        bait = data["bait"]
        caught = data["caught"]
        if not caught:
            return await ctx.send(
                f"You haven't caught anything yet. Use `{ctx.clean_prefix}fish` to start fishing!"
            )

        # 1) tally up each species into lines
        counts: Dict[str, int] = {}
        for f in caught:
            counts[f] = counts.get(f, 0) + 1

        lines: List[str] = []
        for fish, cnt in counts.items():
            info = self.fish_definitions.get(fish, {})
            emoji = info.get("emoji", "")
            rarity = info.get("rarity", "Unknown")
            biome = info.get("biome", "Unknown")
            lines.append(f"• {emoji} {fish} ({rarity}, {biome}): {cnt}")

        # 2) split lines into pages
        per_page = 8
        pages = [lines[i : i + per_page] for i in range(0, len(lines), per_page)]

        # 3) build an embed for each page
        embeds: List[discord.Embed] = []
        image_url = "https://files.catbox.moe/w2zsia.png"
        bal = await bank.get_balance(ctx.author)
        currency = await bank.get_currency_name(ctx.guild)

        for idx, page_lines in enumerate(pages):
            emb = discord.Embed(
                title=f"{ctx.author.display_name}'s Fishing Stats",
                colour=discord.Colour.blue(),
            )
            emb.set_thumbnail(url=image_url)

            # always show balance & bait
            emb.add_field(name="Balance", value=f"**{bal}** {currency}", inline=False)
            emb.add_field(name="Bait", value=str(bait), inline=True)

            # caught chunk
            emb.add_field(
                name="Caught",
                value="\n".join(page_lines),
                inline=False,
            )

            # only on the last page, show items
            if idx == len(pages) - 1:
                items = data["items"]
                if items:
                    inv_counts: Dict[str, int] = {}
                    for it in items:
                        inv_counts[it] = inv_counts.get(it, 0) + 1
                    item_lines = "\n".join(f"• {iname}: {cnt}"
                                           for iname, cnt in inv_counts.items())
                    emb.add_field(name="Items", value=item_lines, inline=False)

            emb.set_footer(text=f"Page {idx+1}/{len(pages)}")
            embeds.append(emb)

        # 4) hand off to your paginator
        await self._paginate_embeds(ctx, embeds)
        pass

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
        pass

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
        pass

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
        pass

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
        pass

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
        pass

    @commands.command()
    async def givefish(self, ctx, recipient: commands.MemberConverter, amount: int, *, name: str):
        """
        Give away your fish or items to another user.
        Usage: !givefish @Bob 2 Salmon
               !givefish @Bob 1 "Treasure Map"
        """
        giver_conf = self.config.user(ctx.author)
        rec_conf   = self.config.user(recipient)

        # Normalize lookup
        # Try fish first, then items
        is_fish = name in self.fish_definitions
        if is_fish:
            src_list = await giver_conf.caught()
        else:
            src_list = await giver_conf.items()

        have = src_list.count(name)
        if have < amount:
            return await ctx.send(
                f"❌ You only have {have}× **{name}** to give, but tried to give {amount}."
            )

        # remove from giver
        for _ in range(amount):
            src_list.remove(name)
        if is_fish:
            await giver_conf.caught.set(src_list)
        else:
            await giver_conf.items.set(src_list)

        # add to recipient
        if is_fish:
            dst_list = await rec_conf.caught()
            dst_list.extend([name] * amount)
            await rec_conf.caught.set(dst_list)
        else:
            dst_list = await rec_conf.items()
            dst_list.extend([name] * amount)
            await rec_conf.items.set(dst_list)

        await ctx.send(
            f"🤝 {ctx.author.mention} gave {amount}× **{name}** to {recipient.mention}!"
        )
        pass

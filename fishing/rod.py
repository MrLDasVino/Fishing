# cogs/fishing/rod.py

from redbot.core import commands
from .data import rod_upgrade_requirements
from .helpers import deposit

class Rod(commands.Cog):
    def __init__(self, config):
        self.config = config

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
        pass

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
            ach_id = f"rod_master_{target}"
            if ach_id in self.achievements and not await self._has_achievement(ctx.author, ach_id):
                msg = await self._award_achievement(ctx, ctx.author, ach_id)
                if msg:
                    await ctx.send(msg)            
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
        pass

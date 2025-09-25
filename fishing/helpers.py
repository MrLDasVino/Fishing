# cogs/fishing/helpers.py

import random
import asyncio
import discord
from redbot.core import bank

async def deposit(ctx, member, amount: int):
    """Deposit amount into member’s account; return (new_balance, currency_name)."""
    new_bal = await bank.deposit_credits(member, amount)
    currency = await bank.get_currency_name(ctx.guild) if ctx.guild else "credits"
    return new_bal, currency

def choose_random(names, weights):
    """Pick one element from names with given weights."""
    return random.choices(names, weights=weights, k=1)[0]

async def paginate(ctx, embeds: list, timeout: float = 120.0):
    """Send a list of embeds with reaction pagination."""
    if not embeds:
        return await ctx.send("Nothing to show.")
    message = await ctx.send(embed=embeds[0])
    if len(embeds) == 1:
        return

    controls = ["⏮️", "⬅️", "⏹️", "➡️", "⏭️"]
    for r in controls:
        await message.add_reaction(r)

    idx = 0

    def check(reaction, user):
        return (
            reaction.message.id == message.id
            and user == ctx.author
            and str(reaction.emoji) in controls
        )

    while True:
        try:
            reaction, user = await ctx.bot.wait_for("reaction_add", timeout=timeout, check=check)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break

        emoji = str(reaction.emoji)
        await message.remove_reaction(reaction.emoji, user)

        if emoji == "⏹️":
            await message.clear_reactions()
            break
        if emoji == "⬅️":
            idx = (idx - 1) % len(embeds)
        if emoji == "➡️":
            idx = (idx + 1) % len(embeds)
        if emoji == "⏮️":
            idx = 0
        if emoji == "⏭️":
            idx = len(embeds) - 1

        await message.edit(embed=embeds[idx])

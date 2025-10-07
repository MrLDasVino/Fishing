import aiohttp
from redbot.core import commands
import discord


class RadioBrowser(commands.Cog):
    """
    Search and fetch radio stations from Radio Browser.
    Commands:
      • radio search [name|country|tag|language] <query>
      • radio pick <number>
      • radio random
    """

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self._search_cache: dict[int, list[dict]] = {}

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group(name="radio", invoke_without_command=True)
    async def radio(self, ctx: commands.Context):
        await ctx.send(
            "Usage:\n"
            "`[p]radio search [name|country|tag|language] <query>`\n"
            "`[p]radio pick <number>`\n"
            "`[p]radio random`"
        )

    @radio.command(name="search")
    async def radio_search(self, ctx: commands.Context, *args):
        """
        Search stations by name (default), country, tag or language.
        Examples:
          • [p]radio search Beatles
          • [p]radio search country Germany
          • [p]radio search tag rock
        """
        if not args:
            return await ctx.send("Please provide something to search for.")

        key = args[0].lower()
        if key in ("name", "country", "tag", "language") and len(args) > 1:
            field = key
            query = " ".join(args[1:])
        else:
            field = "name"
            query = " ".join(args)

        params = {field: query, "limit": 10}
        url = "http://api.radio-browser.info/json/stations/search"
        async with self.session.get(url, params=params) as resp:
            if resp.status != 200:
                return await ctx.send("❌ Error fetching stations. Try again later.")
            data = await resp.json()

        if not data:
            return await ctx.send(f"No stations found for **{field}: {query}**.")

        self._search_cache[ctx.author.id] = data

        embed = discord.Embed(
            title=f"Results — {field.title()}: {query}",
            color=discord.Color.green(),
        )
        for idx, station in enumerate(data, start=1):
            name = station.get("name", "Unknown")
            country = station.get("country", "Unknown")
            language = station.get("language", "Unknown")
            embed.add_field(
                name=f"{idx}. {name}",
                value=f"Country: {country} | Language: {language}",
                inline=False,
            )
        embed.set_footer(text="Type [p]radio pick <number> to get the stream URL")
        await ctx.send(embed=embed)

    @radio.command(name="pick")
    async def radio_pick(self, ctx: commands.Context, number: int):
        """
        Pick one station from your last search results by its index.
        """
        cache = self._search_cache.get(ctx.author.id)
        if not cache:
            return await ctx.send("You have no recent search. Use `[p]radio search <query>` first.")

        if number < 1 or number > len(cache):
            return await ctx.send(f"Pick a number between 1 and {len(cache)}.")

        station = cache[number - 1]
        title = station.get("name", "Unknown station")
        stream_url = station.get("url_resolved") or station.get("url") or "No URL available"
        country = station.get("country", "Unknown")
        language = station.get("language", "Unknown")

        embed = discord.Embed(title=title, color=discord.Color.blue())
        embed.add_field(name="🔗 Stream URL", value=stream_url, inline=False)
        embed.add_field(name="🌍 Country", value=country, inline=True)
        embed.add_field(name="🗣️ Language", value=language, inline=True)
        await ctx.send(embed=embed)

    @radio.command(name="random")
    async def radio_random(self, ctx: commands.Context):
        """
        Fetch a completely random radio station.
        """
        url = "http://api.radio-browser.info/json/stations/random"
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send("❌ Error fetching a random station.")
            station = await resp.json()

        title = station.get("name", "Random station")
        stream_url = station.get("url_resolved") or station.get("url") or "No URL available"
        country = station.get("country", "Unknown")
        language = station.get("language", "Unknown")

        embed = discord.Embed(title="🎲 Random Radio Station", color=discord.Color.purple())
        embed.add_field(name=title, value=f"[Listen here]({stream_url})", inline=False)
        embed.add_field(name="🌍 Country", value=country, inline=True)
        embed.add_field(name="🗣️ Language", value=language, inline=True)
        await ctx.send(embed=embed)

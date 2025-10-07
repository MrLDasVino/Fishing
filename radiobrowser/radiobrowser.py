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
        self.session: aiohttp.ClientSession | None = None
        self._search_cache: dict[int, list[dict]] = {}

    async def cog_load(self):
        """Called when the cog is loaded; initialize the HTTP session here."""
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        """Called when the cog is unloaded; close the HTTP session."""
        if self.session:
            await self.session.close()

    @commands.group(name="radio", invoke_without_command=True)
    async def radio(self, ctx: commands.Context):
        """Group command for Radio Browser.

        Search internet radio stations by name, country, tag or language,
        pick from your last search, or get a random station.
        """
        await ctx.send_help()

    @radio.command(name="search")
    async def radio_search(self, ctx: commands.Context, *args):
        if not args:
            return await ctx.send("Please provide something to search for.")

        key = args[0].lower()
        if key in ("name", "country", "tag", "language") and len(args) > 1:
            field, query = key, " ".join(args[1:])
        else:
            field, query = "name", " ".join(args)

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
            embed.add_field(
                name=f"{idx}. {station.get('name', 'Unknown')}",
                value=(
                    f"Country: {station.get('country', 'Unknown')} | "
                    f"Language: {station.get('language', 'Unknown')}"
                ),
                inline=False,
            )
        embed.set_footer(text="Type [p]radio pick <number> to get the stream URL")
        await ctx.send(embed=embed)

    @radio.command(name="pick")
    async def radio_pick(self, ctx: commands.Context, number: int):
        cache = self._search_cache.get(ctx.author.id)
        if not cache:
            return await ctx.send("You have no recent search. Use `[p]radio search <query>` first.")

        if not 1 <= number <= len(cache):
            return await ctx.send(f"Pick a number between 1 and {len(cache)}.")

        station = cache[number - 1]
        stream_url = station.get("url_resolved") or station.get("url") or "No URL available"

        embed = discord.Embed(
            title=station.get("name", "Unknown station"),
            color=discord.Color.blue(),
        )
        embed.add_field(name="🔗 Stream URL", value=stream_url, inline=False)
        embed.add_field(name="🌍 Country", value=station.get("country", "Unknown"), inline=True)
        embed.add_field(name="🗣️ Language", value=station.get("language", "Unknown"), inline=True)
        await ctx.send(embed=embed)

    @radio.command(name="random")
    async def radio_random(self, ctx: commands.Context):
        url = "http://api.radio-browser.info/json/stations/random"
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send("❌ Error fetching a random station.")
            station = await resp.json()

        stream_url = station.get("url_resolved") or station.get("url") or "No URL available"
        embed = discord.Embed(title="🎲 Random Radio Station", color=discord.Color.purple())
        embed.add_field(name=station.get("name", "Random station"), value=f"[Listen here]({stream_url})", inline=False)
        embed.add_field(name="🌍 Country", value=station.get("country", "Unknown"), inline=True)
        embed.add_field(name="🗣️ Language", value=station.get("language", "Unknown"), inline=True)
        await ctx.send(embed=embed)

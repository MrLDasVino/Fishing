import aiohttp
import logging

from redbot.core import commands
import discord

logger = logging.getLogger(__name__)


class RadioBrowser(commands.Cog):
    """
    Search and fetch radio stations from Radio Browser.
    Commands:
      • radio search [name|country|tag|language] <query>
      • radio pick <number>
      • radio random
    """

    # Primary JSON API and fallback Webservice API
    API_BASE = "https://api.radio-browser.info/json"
    WS_BASE = "https://www.radio-browser.info/webservice"

    def __init__(self, bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None
        self._search_cache: dict[int, list[dict]] = {}

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    @commands.group(name="radio", invoke_without_command=True)
    async def radio(self, ctx: commands.Context):
        """Group command for Radio Browser integration."""
        await ctx.send_help()

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
            field, query = key, " ".join(args[1:])
        else:
            field, query = "name", " ".join(args)

        params = {field: query, "limit": 10}
        data = None

        # try primary JSON host then fallback Webservice
        for base, path_prefix in (
            (self.API_BASE, "/stations/search"),
            (self.WS_BASE, "/json/stations/search"),
        ):
            url = f"{base}{path_prefix}"
            try:
                async with self.session.get(url, params=params, timeout=8) as resp:
                    text = await resp.text()
                    ctype = resp.headers.get("Content-Type", "")
                    if resp.status != 200 or "application/json" not in ctype:
                        logger.error(f"Search HTTP {resp.status} @ {url}: {text[:200]}")
                        continue
                    data = await resp.json()
                    break
            except Exception:
                logger.exception(f"Network error during search at {url}")
                continue

        if data is None:
            return await ctx.send("❌ Could not reach Radio Browser. Try again later.")
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
        """
        Pick one station from your last search results by its index.
        """
        cache = self._search_cache.get(ctx.author.id)
        if not cache:
            return await ctx.send("You have no recent search. Use `[p]radio search <query>` first.")
        if not 1 <= number <= len(cache):
            return await ctx.send(f"Pick a number between 1 and {len(cache)}.")

        station = cache[number - 1]
        stream = station.get("url_resolved") or station.get("url") or "No URL available"
        embed = discord.Embed(
            title=station.get("name", "Unknown station"),
            color=discord.Color.blue(),
        )
        embed.add_field(name="🔗 Stream URL", value=stream, inline=False)
        embed.add_field(name="🌍 Country", value=station.get("country", "Unknown"), inline=True)
        embed.add_field(name="🗣️ Language", value=station.get("language", "Unknown"), inline=True)
        await ctx.send(embed=embed)

    @radio.command(name="random")
    async def radio_random(self, ctx: commands.Context):
        """Fetch a completely random radio station."""
        station = None

        for base, path_prefix in (
            (self.API_BASE, "/stations/random"),
            (self.WS_BASE, "/json/stations/random"),
        ):
            url = f"{base}{path_prefix}"
            try:
                async with self.session.get(url, timeout=8) as resp:
                    text = await resp.text()
                    ctype = resp.headers.get("Content-Type", "")
                    if resp.status != 200 or "application/json" not in ctype:
                        logger.error(f"Random HTTP {resp.status} @ {url}: {text[:200]}")
                        continue
                    station = await resp.json()
                    break
            except Exception:
                logger.exception(f"Network error during random fetch at {url}")
                continue

        if not station:
            return await ctx.send("❌ Could not fetch a random station. Try again later.")

        title = station.get("name", "Random station")
        stream = station.get("url_resolved") or station.get("url") or "No URL available"
        country = station.get("country", "Unknown")
        language = station.get("language", "Unknown")

        embed = discord.Embed(title="🎲 Random Radio Station", color=discord.Color.purple())
        embed.add_field(name=title, value=f"[Listen here]({stream})", inline=False)
        embed.add_field(name="🌍 Country", value=country, inline=True)
        embed.add_field(name="🗣️ Language", value=language, inline=True)
        await ctx.send(embed=embed)

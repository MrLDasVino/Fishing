import aiohttp
import asyncio
import logging

from redbot.core import commands
import discord

logger = logging.getLogger(__name__)


class RadioBrowser(commands.Cog):
    """
    Search and fetch radio stations from Radio Browser.
    Commands:
      • [p]radio search [name|country|tag|language] <query>
      • [p]radio pick <number>
      • [p]radio random
    """

    # Use the DNS-balanced JSON endpoint
    API_BASE = "https://all.api.radio-browser.info/json"

    def __init__(self, bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None
        self._search_cache: dict[int, list[dict]] = {}

    async def cog_load(self):
        """Initialize HTTP session when the cog loads."""
        headers = {"User-Agent": "RedbotRadioCog/1.0 (+https://github.com/YourRepo)"}
        self.session = aiohttp.ClientSession(headers=headers)

    async def cog_unload(self):
        """Close HTTP session when the cog unloads."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _api_get(self, endpoint: str, params: dict):
        """
        Fetch JSON from API_BASE/<endpoint> with up to 3 retries on 502 or network errors.
        Returns (data, error_message).
        """
        assert self.session, "HTTP session not initialized"
        url = f"{self.API_BASE.rstrip('/')}/{endpoint.lstrip('/')}"

        last_err: str | None = None
        for attempt in range(1, 4):
            try:
                async with self.session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json(), None

                    text = await resp.text()
                    if resp.status == 502:
                        logger.warning("Attempt %s: 502 from %s", attempt, url)
                        last_err = "502 Bad Gateway"
                    else:
                        logger.error("HTTP %s from %s: %s", resp.status, url, text[:200])
                        return None, f"HTTP {resp.status} from Radio Browser"
            except Exception as e:
                last_err = str(e)
                logger.warning("Attempt %s: network error fetching %s → %s", attempt, url, e)

            if attempt < 3:
                await asyncio.sleep(1)

        return None, last_err or "Unknown error fetching from Radio Browser"

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

        params = {field: query, "limit": 10, "hidebroken": True}
        data, error = await self._api_get("stations/search", params)

        if error:
            return await ctx.send(f"❌ {error}. Try again later.")
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
        if not (1 <= number <= len(cache)):
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
        """
        Fetch a completely random station using the dedicated endpoint.
        """
        data, error = await self._api_get("stations/random", {"limit": 1})
        if error:
            return await ctx.send(f"❌ {error}. Try again later.")
        if not data:
            return await ctx.send("❌ No station returned. Try again later.")

        station = data[0]
        title = station.get("name", "Random station")
        stream = station.get("url_resolved") or station.get("url") or "No URL available"
        country = station.get("country", "Unknown")
        language = station.get("language", "Unknown")

        embed = discord.Embed(
            title="🎲 Random Radio Station",
            color=discord.Color.purple(),
        )
        embed.add_field(name=title, value=f"[Listen here]({stream})", inline=False)
        embed.add_field(name="🌍 Country", value=country, inline=True)
        embed.add_field(name="🗣️ Language", value=language, inline=True)
        await ctx.send(embed=embed)

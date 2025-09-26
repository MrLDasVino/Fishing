import io
import logging

from redbot.core import commands, Config
import aiohttp
import discord

# logger for this cog
logger = logging.getLogger("red.cogs.imagefilter")

BaseCog = getattr(commands, "Cog", object)

class ImageFilter(BaseCog):
    """Apply image effects using the Jeyy Image API."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_user = {"api_key": None}
        self.config.register_user(**default_user)

    @commands.group(name="imgmanip", invoke_without_command=True)
    async def imgmanip(self, ctx):
        """Group for Jeyy Image manipulation commands."""
        await ctx.send_help(ctx.command)

    @imgmanip.command(name="setkey")
    async def setkey(self, ctx, api_key: str):
        """Store your Jeyy API key."""
        await self.config.user(ctx.author).api_key.set(api_key)
        await ctx.send("✅ Your Jeyy API key has been saved.")

    async def _fetch(self, endpoint: str, img_url: str, api_key: str) -> bytes:
        """Internal helper: call Jeyy API and return raw image bytes."""
        url = f"https://api.jeyy.xyz/{endpoint}"
        headers = {"Authorization": api_key}
        payload = {"image": img_url}  # if API wants {"url": img_url}, swap the key here
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                text = await resp.text()
                if resp.status != 200:
                    logger.warning(f"Jeyy `{endpoint}` failed: {resp.status} {text}")
                    raise RuntimeError(f"HTTP {resp.status}")
                return await resp.read()

    @imgmanip.command(name="blur")
    async def blur(self, ctx, intensity: int = 5):
        """Blur the attached image. Intensity 1–20."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key with `[p]imgmanip setkey YOUR_KEY`.")
        if not ctx.message.attachments:
            return await ctx.send("❌ Please attach an image.")
        if not 1 <= intensity <= 20:
            return await ctx.send("❌ Intensity must be between 1 and 20.")

        img_url = ctx.message.attachments[0].url
        await ctx.send(f"🔄 Blurring (intensity={intensity})…")
        try:
            data = await self._fetch(f"blur/{intensity}", img_url, api_key)
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        await ctx.send(file=discord.File(fp, "blur.png"))

    @imgmanip.command(name="grayscale")
    async def grayscale(self, ctx):
        """Convert the attached image to grayscale."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key with `[p]imgmanip setkey YOUR_KEY`.")
        if not ctx.message.attachments:
            return await ctx.send("❌ Please attach an image.")
        img_url = ctx.message.attachments[0].url

        await ctx.send("🔄 Converting to grayscale…")
        headers = {"Authorization": api_key}
        params = {"image": img_url}
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.jeyy.xyz/grayscale", params=params, headers=headers) as resp:
                text = await resp.text()
                if resp.status != 200:
                    logger.warning(f"Jeyy GET /grayscale failed: {resp.status} {text}")
                    return await ctx.send(f"❌ API error {resp.status}: see console for details.")
                data = await resp.read()

        fp = io.BytesIO(data)
        await ctx.send(file=discord.File(fp, "grayscale.png"))


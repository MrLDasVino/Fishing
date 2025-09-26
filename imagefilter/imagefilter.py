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
        self.config.register_user(api_key=None)

    @commands.group(name="imgmanip", invoke_without_command=True)
    async def imgmanip(self, ctx):
        """Group for Jeyy Image manipulation commands."""
        await ctx.send_help(ctx.command)

    @imgmanip.command(name="setkey")
    async def setkey(self, ctx, api_key: str):
        """Store your Jeyy API key."""
        await self.config.user(ctx.author).api_key.set(api_key)
        await ctx.send("✅ Your Jeyy API key has been saved.")

    async def _fetch(self, endpoint: str, img_url: str, api_key: str, method: str = "POST") -> bytes:
        """Internal: call Jeyy API and return raw image bytes."""
        url = f"https://api.jeyy.xyz/{endpoint}"
        headers = {"Authorization": f"Bearer {api_key}"}

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                params = {"image_url": img_url}
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status != 200:
                        # only read text on errors
                        err = await resp.text()
                        logger.warning(f"Jeyy GET /{endpoint} failed: {resp.status} {err}")
                        raise RuntimeError(f"HTTP {resp.status}")
                    return await resp.read()
            else:  # POST
                payload = {"image": img_url}
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        err = await resp.text()
                        logger.warning(f"Jeyy POST /{endpoint} failed: {resp.status} {err}")
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

        url = "https://api.jeyy.xyz/v2/image/blur"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"image_url": img_url, "value": intensity}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    logger.warning(f"Jeyy GET /v2/image/blur failed: {resp.status} {err}")
                    return await ctx.send(f"❌ API error {resp.status}: see console for details.")
                data = await resp.read()

        fp = io.BytesIO(data)
        await ctx.send(file=discord.File(fp, "blur.png"))

    @imgmanip.command(name="abstract")
    async def abstract(self, ctx):
        """Apply the Abstract v2 filter to the attached image."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key with `[p]imgmanip setkey YOUR_KEY`.")
        if not ctx.message.attachments:
            return await ctx.send("❌ Please attach an image.")

        img_url = ctx.message.attachments[0].url
        await ctx.send("🔄 Applying Abstract v2 filter…")
        try:
            data = await self._fetch("v2/image/abstract", img_url, api_key, method="GET")
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        await ctx.send(file=discord.File(fp, "abstract.png"))

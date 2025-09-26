import io
import logging

from redbot.core import commands, Config
import aiohttp
import discord

# logger for this cog
logger = logging.getLogger("red.cogs.imagefilter")

BaseCog = getattr(commands, "Cog", object)

class ImageFilter(BaseCog):
    """Apply image effects using the Jeyy Image API: blur, balls, and abstract filters."""

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

    async def _fetch(self, endpoint: str, img_url: str, api_key: str, method: str = "GET", params=None, payload=None) -> bytes:
        """Internal: call Jeyy API and return raw image bytes."""
        url = f"https://api.jeyy.xyz/{endpoint}"
        headers = {"Authorization": f"Bearer {api_key}"}

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status != 200:
                        err = await resp.text()
                        logger.warning(f"Jeyy GET /{endpoint} failed: {resp.status} {err}")
                        raise RuntimeError(f"HTTP {resp.status}")
                    return await resp.read()
            else:  # POST
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        err = await resp.text()
                        logger.warning(f"Jeyy POST /{endpoint} failed: {resp.status} {err}")
                        raise RuntimeError(f"HTTP {resp.status}")
                    return await resp.read()

    @imgmanip.command(name="blur")
    async def blur(self, ctx):
        """Blur the attached image using the API’s default intensity."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key with `[p]imgmanip setkey YOUR_KEY`.")
        if not ctx.message.attachments:
            return await ctx.send("❌ Please attach an image.")

        img_url = ctx.message.attachments[0].url
        await ctx.send("🔄 Blurring image…")

        try:
            data = await self._fetch(
                endpoint="v2/image/blur",
                img_url=img_url,
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "blur.gif"))

    @imgmanip.command(name="balls")
    async def balls(self, ctx):
        """Apply the Balls v2 filter using the API’s default intensity."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key with `[p]imgmanip setkey YOUR_KEY`.")
        if not ctx.message.attachments:
            return await ctx.send("❌ Please attach an image.")

        img_url = ctx.message.attachments[0].url
        await ctx.send("🔄 Applying Balls filter…")

        try:
            data = await self._fetch(
                endpoint="v2/image/balls",
                img_url=img_url,
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "balls.gif"))

    @imgmanip.command(name="abstract")
    async def abstract(self, ctx):
        """Apply the Abstract v2 filter to the attached image."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key with `[p]imgmanip setkey YOUR_KEY`.")
        if not ctx.message.attachments:
            return await ctx.send("❌ Please attach an image.")

        img_url = ctx.message.attachments[0].url
        await ctx.send("🔄 Applying Abstract filter…")

        try:
            data = await self._fetch(
                endpoint="v2/image/abstract",
                img_url=img_url,
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "abstract.gif"))

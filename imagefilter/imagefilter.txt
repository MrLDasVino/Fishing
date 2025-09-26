import io
from redbot.core import commands, Config
import aiohttp
import discord

BaseCog = getattr(commands, "Cog", object)

class JeyyImage(BaseCog):
    """Apply image effects using the Jeyy Image API."""

    def __init__(self, bot):
        self.bot = bot
        # per-user storage for API keys
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

    async def _fetch_processed_image(self, endpoint: str, image_url: str, api_key: str):
        """Internal: Call Jeyy API, return bytes."""
        url = f"https://api.jeyy.xyz/{endpoint}"
        payload = {"image": image_url}
        headers = {"Authorization": api_key}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"API error: {resp.status} {text}")
                data = await resp.read()
        return data

    async def _get_attachment_url(self, ctx) -> str:
        """Fetch URL from first attachment or last message."""
        if ctx.message.attachments:
            return ctx.message.attachments[0].url
        raise commands.BadArgument("Please attach an image.")

    @imgmanip.command(name="blur")
    async def blur(
        self, ctx, intensity: int = 5
    ):
        """Blur the attached image. Intensity 1–20."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ You need to set your API key with `[p]imgmanip setkey`.")
        if not 1 <= intensity <= 20:
            return await ctx.send("❌ Intensity must be between 1 and 20.")

        try:
            img_url = await self._get_attachment_url(ctx)
            # Jeyy API might expect a path like blur/5
            endpoint = f"blur/{intensity}"
            data = await self._fetch_processed_image(endpoint, img_url, api_key)
        except Exception as e:
            return await ctx.send(f"❌ Failed to process image: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        file = discord.File(fp, filename="blur.png")
        await ctx.send("Here’s your blurred image:", file=file)

    @imgmanip.command(name="grayscale")
    async def grayscale(self, ctx):
        """Convert the attached image to grayscale."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ You need to set your API key with `[p]imgmanip setkey`.")

        try:
            img_url = await self._get_attachment_url(ctx)
            data = await self._fetch_processed_image("grayscale", img_url, api_key)
        except Exception as e:
            return await ctx.send(f"❌ Failed to process image: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        file = discord.File(fp, filename="grayscale.png")
        await ctx.send("Here’s your grayscale image:", file=file)

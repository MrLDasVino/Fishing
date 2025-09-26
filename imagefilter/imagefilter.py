import io
from redbot.core import commands, Config
import aiohttp
import discord

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
                return await resp.read()

    async def _get_attachment_url(self, ctx) -> str:
        """Fetch URL from first attachment."""
        if ctx.message.attachments:
            return ctx.message.attachments[0].url
        raise commands.BadArgument("Please attach an image.")

    @imgmanip.command(name="blur")
    async def blur(self, ctx, intensity: int = 5):
        """Blur the attached image. Intensity 1–20."""
        # 1) Key check
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ You need to set your API key: `[p]imgmanip setkey YOUR_KEY`")

        # 2) Attachment check
        if not ctx.message.attachments:
            return await ctx.send("❌ Please attach an image to blur.")
        img_url = ctx.message.attachments[0].url

        # 3) Intensity bounds
        if not 1 <= intensity <= 20:
            return await ctx.send("❌ Intensity must be between 1 and 20.")

        await ctx.send(f"🔄 Blurring at intensity {intensity}…")  # Feedback

        # 4) Call API
        endpoint = f"blur/{intensity}"
        # If the API expects a different key name, swap "image" → "url" here.
        payload = {"image": img_url}

        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.jeyy.xyz/{endpoint}", json=payload, headers={"Authorization": api_key}) as resp:
                body = await resp.text()
                if resp.status != 200:
                    # Log for you
                    self.bot.log.warning(f"Jeyy blur failed {resp.status} {body}")
                    return await ctx.send(f"❌ API error {resp.status}: see console log for details.")
                data = await resp.read()

        # 5) Send the result
        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send("✅ Here’s your blurred image:", file=discord.File(fp, "blur.png"))


    @imgmanip.command(name="grayscale")
    async def grayscale(self, ctx):
        """Convert the attached image to grayscale."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ You need to set your API key: `[p]imgmanip setkey YOUR_KEY`")

        if not ctx.message.attachments:
            return await ctx.send("❌ Please attach an image to convert.")
        img_url = ctx.message.attachments[0].url

        await ctx.send("🔄 Converting to grayscale…")

        payload = {"image": img_url}
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.jeyy.xyz/grayscale", json=payload, headers={"Authorization": api_key}) as resp:
                body = await resp.text()
                if resp.status != 200:
                    self.bot.log.warning(f"Jeyy grayscale failed {resp.status} {body}")
                    return await ctx.send(f"❌ API error {resp.status}: see console log for details.")
                data = await resp.read()

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send("✅ Here’s your grayscale image:", file=discord.File(fp, "grayscale.png"))


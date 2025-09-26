import io
import logging
import random
from typing import Optional, Union

from redbot.core import commands, Config
import aiohttp
import discord

logger = logging.getLogger("red.cogs.imagefilter")
BaseCog = getattr(commands, "Cog", object)

class ImageFilter(BaseCog):
    """Apply image effects using the Jeyy Image API: blur, balls, and abstract."""

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

    async def _fetch(
        self,
        endpoint: str,
        api_key: str,
        method: str = "GET",
        params: dict = None,
        payload: dict = None,
    ) -> bytes:
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
            else:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        err = await resp.text()
                        logger.warning(f"Jeyy POST /{endpoint} failed: {resp.status} {err}")
                        raise RuntimeError(f"HTTP {resp.status}")
                    return await resp.read()

    def _resolve_image_url(
        self, 
        ctx: commands.Context, 
        target: Optional[Union[discord.Member, str]]
    ) -> str:
        """
        Determine which image to process:
        1) If target is Member → avatar
        2) If target is str and starts with http → use that URL
        3) If there's an attachment → use it
        4) Otherwise → use ctx.author's avatar
        """
        if isinstance(target, discord.Member):
            return target.avatar.url
        if isinstance(target, str) and target.lower().startswith("http"):
            return target
        if ctx.message.attachments:
            return ctx.message.attachments[0].url
        return ctx.author.avatar.url

    @imgmanip.command(name="blur")
    async def blur(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Blur an image (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Blurring image…")
        try:
            data = await self._fetch(
                endpoint="v2/image/blur",
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
    async def balls(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Balls filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Balls filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/balls",
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
    async def abstract(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Abstract v2 filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Abstract v2 filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/abstract",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "abstract.gif"))
        
    @imgmanip.command(name="3d")
    async def three_d(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply 3D filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying 3D filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/3d",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "3d.gif"))
        

    @imgmanip.command(name="ace")
    async def ace(self, ctx, *, text: str):
        """
        Generate an 'Ace' courtroom GIF.
        
        text        The line of dialogue to show in the speech bubble.
        """
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        name = ctx.author.display_name
        attorneys = ["Jordan Blake", "Alexis Reed", "Taylor Quinn", "Morgan Flynn"]
        prosecutors = ["Casey Vaughn", "Riley Carter", "Jamie Lee", "Dakota Shore"]
        # pick random roles
        attorney = random.choice(attorneys)
        prosecutor = random.choice(prosecutors)
        # side tells the API who’s speaking: 'attorney' or 'prosecutor'
        side = random.choice(["attorney", "prosecutor"])

        await ctx.send("🔄 Building Ace GIF…")
        try:
            data = await self._fetch(
                endpoint="v2/image/ace",
                api_key=api_key,
                method="GET",
                params={
                    "name": name,
                    "attorney": attorney,
                    "prosecutor": prosecutor,
                    "side": side,
                    "text": text,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "ace.gif"))
        
    @imgmanip.command(name="ads")
    async def ads(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Ads filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Ads filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/ads",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "ads.gif"))
        
    @imgmanip.command(name="bayer")
    async def bayer(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Bayer filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Bayer filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/bayer",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "bayer.gif"))

    @imgmanip.command(name="bevel")
    async def bevel(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Bevel filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Bevel filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/bevel",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "bevel.gif"))

    @imgmanip.command(name="billboard")
    async def billboard(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Billboard filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Billboard filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/billboard",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "billboard.gif"))

    @imgmanip.command(name="blocks")
    async def blocks(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Blocks filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Blocks filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/blocks",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "blocks.gif"))

    @imgmanip.command(name="boil")
    async def boil(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Boil filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Boil filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/boil",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "boil.gif"))

    @imgmanip.command(name="bomb")
    async def bomb(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Bomb filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Bomb filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/bomb",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "bomb.gif"))

    @imgmanip.command(name="bonks")
    async def bonks(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Bonks filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Bonks filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/bonks",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "bonks.gif"))

    @imgmanip.command(name="bubble")
    async def bubble(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Bubble filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Bubble filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/bubble",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "bubble.gif"))

    @imgmanip.command(name="burn")
    async def burn(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Burn filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Burn filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/burn",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "burn.gif"))

    @imgmanip.command(name="canny")
    async def canny(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Canny edge-detection filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Canny filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/canny",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "canny.gif"))

        
        

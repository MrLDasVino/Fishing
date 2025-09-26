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

    @imgmanip.command(name="cartoon")
    async def cartoon(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Cartoon filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Cartoon filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/cartoon",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "cartoon.gif"))
        
    @imgmanip.command(name="cinema")
    async def cinema(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Cinema filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Cinema filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/cinema",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "cinema.gif"))

    @imgmanip.command(name="clock")
    async def clock(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Clock filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Clock filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/clock",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "clock.gif"))

    @imgmanip.command(name="cloth")
    async def cloth(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Cloth filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Cloth filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/cloth",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "cloth.gif"))

    @imgmanip.command(name="console")
    async def console(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Console filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Console filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/console",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "console.gif"))

    @imgmanip.command(name="contour")
    async def contour(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Contour filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Contour filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/contour",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "contour.gif"))

    @imgmanip.command(name="cow")
    async def cow(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Cow filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Cow filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/cow",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "cow.gif"))

    @imgmanip.command(name="cracks")
    async def cracks(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Cracks filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Cracks filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/cracks",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "cracks.gif"))

    @imgmanip.command(name="cube")
    async def cube(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Cube filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Cube filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/cube",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "cube.gif"))

    @imgmanip.command(name="dilate")
    async def dilate(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Dilate filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Dilate filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/dilate",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "dilate.gif"))

    @imgmanip.command(name="dither")
    async def dither(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Dither filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Dither filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/dither",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "dither.gif"))

    @imgmanip.command(name="dizzy")
    async def dizzy(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Dizzy filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Dizzy filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/dizzy",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "dizzy.gif"))

    @imgmanip.command(name="dots")
    async def dots(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Dots filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Dots filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/dots",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "dots.gif"))

    @imgmanip.command(name="earthquake")
    async def earthquake(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Earthquake filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Earthquake filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/earthquake",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "earthquake.gif"))

    @imgmanip.command(name="emojify")
    async def emojify(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Emojify filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Emojify filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/emojify",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "emojify.gif"))

    @imgmanip.command(name="endless")
    async def endless(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Endless filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Endless filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/endless",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "endless.gif"))

    @imgmanip.command(name="equations")
    async def equations(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Equations filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Equations filter…")

        try:
            data = await self._fetch(
                endpoint="v2/image/equations",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        # Check Discord’s upload cap for this channel/guild
        max_size = getattr(ctx.guild, "filesize_limit", 8 * 1024 * 1024)  # default 8MB

        # If the payload is too big, try to downscale the GIF
        if len(data) > max_size:
            try:
                from PIL import Image, ImageSequence

                orig = Image.open(io.BytesIO(data))
                frames = [frame.copy().convert("RGBA") for frame in ImageSequence.Iterator(orig)]
                w, h = frames[0].size

                # Compute a simple scale factor based on size ratio
                scale = (max_size / len(data)) ** 0.5
                new_size = (max(1, int(w * scale)), max(1, int(h * scale)))

                out = io.BytesIO()
                frames[0].save(
                    out,
                    format="GIF",
                    save_all=True,
                    append_images=frames[1:],
                    loop=0,
                    optimize=True,
                    duration=orig.info.get("duration", 100),
                )
                data = out.getvalue()
            except Exception:
                pass  # if resizing fails, we'll catch on send

        # Final send (may still error if resizing didn’t shrink enough)
        fp = io.BytesIO(data)
        fp.seek(0)
        try:
            await ctx.send(file=discord.File(fp, "equations.gif"))
        except discord.HTTPException as exc:
            if exc.code == 40005:  # Payload Too Large
                return await ctx.send(
                    "❌ The resulting GIF is too large to upload. "
                    "Try with a smaller image or lower resolution."
                )
            raise


    @imgmanip.command(name="explicit")
    async def explicit(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Explicit filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Explicit filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/explicit",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "explicit.gif"))

    @imgmanip.command(name="fall")
    async def fall(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Fall filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Fall filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/fall",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "fall.gif"))

    @imgmanip.command(name="fan")
    async def fan(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Fan filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Fan filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/fan",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "fan.gif"))

    @imgmanip.command(name="fire")
    async def fire(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Fire filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Fire filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/fire",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "fire.gif"))

    @imgmanip.command(name="flag")
    async def flag(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Flag filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Flag filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/flag",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "flag.gif"))

    @imgmanip.command(name="flush")
    async def flush(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Flush filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Flush filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/flush",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "flush.gif"))

    @imgmanip.command(name="gallery")
    async def gallery(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Gallery filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Gallery filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/gallery",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "gallery.gif"))



        

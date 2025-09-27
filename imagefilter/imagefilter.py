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

    async def _resolve_image_url(
        self,
        ctx: commands.Context,
        target: Optional[Union[discord.Member, str]]
    ) -> Optional[str]:
        """
        Resolve an image URL from:
        - Member or User object -> avatar
        - pasted numeric user id or mention -> avatar
        - http(s) URL string -> the URL itself
        - message attachments -> first attachment
        - fallback -> ctx.author avatar
        Returns None only if no avatar or attachment can be resolved.
        """
        # Direct Member/User
        if isinstance(target, (discord.Member, discord.User)):
            user = target
            try:
                return user.display_avatar.url
            except Exception:
                return None

        # If target is a string, try URL, mention, or user id
        if isinstance(target, str):
            s = target.strip()

            # direct http(s) url
            if s.lower().startswith("http"):
                return s

            # mention like <@123...> or <@!123...>
            if s.startswith("<@") and s.endswith(">"):
                s = s.strip("<@!>")

            # numeric id: try to resolve user
            if s.isdigit():
                user_id = int(s)
                member = None
                # try guild member first
                if ctx.guild:
                    member = ctx.guild.get_member(user_id)
                # try cache
                if not member:
                    member = self.bot.get_user(user_id)
                # fetch from API as last resort
                if not member:
                    try:
                        member = await self.bot.fetch_user(user_id)
                    except Exception:
                        member = None
                if member:
                    try:
                        return member.display_avatar.url
                    except Exception:
                        return None

        # attachments present
        if ctx.message and ctx.message.attachments:
            return ctx.message.attachments[0].url

        # fallback to invoking user avatar
        try:
            return ctx.author.display_avatar.url
        except Exception:
            return None


    @imgmanip.command(name="blur")
    async def blur(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Blur an image (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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
        """Apply Bevel filter with a random level (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        # Choose a random level between 10 and 30 inclusive
        level = random.randint(10, 30)

        await ctx.send(f"🔄 Applying Bevel filter… (level={level})")
        try:
            data = await self._fetch(
                endpoint="v2/image/bevel",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img_url,
                    "level": level,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "bevel.gif"))


    @imgmanip.command(name="billboard")
    async def billboard(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Billboard filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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
        """Apply Boil filter with a random level (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        # Choose a random level between 1 and 5 inclusive
        level = random.randint(1, 5)

        await ctx.send(f"🔄 Applying Boil filter… (level={level})")
        try:
            data = await self._fetch(
                endpoint="v2/image/boil",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img_url,
                    "level": level,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "boil.gif"))


    @imgmanip.command(name="bomb")
    async def bomb(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Bomb filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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
        """Apply Earthquake filter with a random level (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        # Choose a random level between 1 and 10 inclusive
        level = random.randint(1, 10)

        await ctx.send(f"🔄 Applying Earthquake filter… (level={level})")
        try:
            data = await self._fetch(
                endpoint="v2/image/earthquake",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img_url,
                    "level": level,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "earthquake.gif"))


    @imgmanip.command(name="emojify")
    async def emojify(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Emojify filter with a random size (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        # Choose a random size between 16 and 64 inclusive
        size = random.randint(16, 64)

        await ctx.send(f"🔄 Applying Emojify filter… (size={size})")
        try:
            data = await self._fetch(
                endpoint="v2/image/emojify",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img_url,
                    "size": size,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "emojify.gif"))


    @imgmanip.command(name="endless")
    async def endless(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Endless filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

        img_url = await self._resolve_image_url(ctx, target)
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

    @imgmanip.command(name="gameboy_camera")
    async def gameboy_camera(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Gameboy Camera filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Gameboy Camera filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/gameboy_camera",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "gameboy_camera.gif"))

    @imgmanip.command(name="glitch")
    async def glitch(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Glitch filter with a random level (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        # Choose a random level between 1 and 10 inclusive
        level = random.randint(1, 10)

        await ctx.send(f"🔄 Applying Glitch filter… (level={level})")
        try:
            data = await self._fetch(
                endpoint="v2/image/glitch",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img_url,
                    "level": level,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "glitch.gif"))


    @imgmanip.command(name="globe")
    async def globe(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Globe filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Globe filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/globe",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "globe.gif"))
        
    @imgmanip.command(name="half_invert")
    async def half_invert(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Half Invert filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Half Invert filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/half_invert",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "half_invert.gif"))

    @imgmanip.command(name="heart_diffraction")
    async def heart_diffraction(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Heart Diffraction filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        await ctx.send("🔄 Applying Heart Diffraction filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/heart_diffraction",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "heart_diffraction.gif"))

    @imgmanip.command(name="heart_locket")
    async def heart_locket(
        self,
        ctx,
        first: Optional[Union[discord.Member, str]] = None,
        second: Optional[Union[discord.Member, str]] = None,
    ):
        """Apply Heart Locket filter with two images (attachments, mentions, URLs, or avatars)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        # 1) Gather attachments if no explicit args
        attachment_urls = [att.url for att in ctx.message.attachments]
        if not first and not second and len(attachment_urls) >= 2:
            img1, img2 = attachment_urls[:2]
        else:
            img1 = await self._resolve_image_url(ctx, first)
            img2 = await self._resolve_image_url(ctx, second)

        # 2) Ensure both images are provided
        if not img1 or not img2:
            return await ctx.send("❌ Please provide two images (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Heart Locket filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/heart_locket",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img1,
                    "image_url_2": img2,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "heart_locket.gif"))

    @imgmanip.command(name="hearts")
    async def hearts(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Hearts filter with random Rainbow value (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        # Pick a random rainbow value
        rainbow = random.choice(['true', 'false'])

        await ctx.send(f"🔄 Applying Hearts filter… (rainbow={rainbow})")
        try:
            data = await self._fetch(
                endpoint="v2/image/hearts",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img_url,
                    "rainbow": rainbow,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "hearts.gif"))


    @imgmanip.command(name="infinity")
    async def infinity(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Infinity filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Infinity filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/infinity",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "infinity.gif"))

    @imgmanip.command(name="ipcam")
    async def ipcam(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Ipcam filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Ipcam filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/ipcam",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "ipcam.gif"))

    @imgmanip.command(name="kanye")
    async def kanye(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Kanye filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Kanye filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/kanye",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "kanye.gif"))

    @imgmanip.command(name="knit")
    async def knit(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Knit filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Knit filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/knit",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "knit.gif"))

    @imgmanip.command(name="lamp")
    async def lamp(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Lamp filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Lamp filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/lamp",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "lamp.gif"))

    @imgmanip.command(name="laundry")
    async def laundry(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Laundry filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Laundry filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/laundry",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "laundry.gif"))

    @imgmanip.command(name="layers")
    async def layers(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Layers filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Layers filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/layers",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "layers.gif"))

    @imgmanip.command(name="letters")
    async def letters(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Letters filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Letters filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/letters",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "letters.gif"))

    @imgmanip.command(name="lines")
    async def lines(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Lines filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Lines filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/lines",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "lines.gif"))

    @imgmanip.command(name="liquefy")
    async def liquefy(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Liquefy filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Liquefy filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/liquefy",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "liquefy.gif"))

    @imgmanip.command(name="logoff")
    async def logoff(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Logoff filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Logoff filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/logoff",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "logoff.gif"))

    @imgmanip.command(name="lsd")
    async def lsd(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply LSD filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying LSD filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/lsd",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "lsd.gif"))

    @imgmanip.command(name="magnify")
    async def magnify(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Magnify filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Magnify filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/magnify",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "magnify.gif"))

    @imgmanip.command(name="matrix")
    async def matrix(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Matrix filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Matrix filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/matrix",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "matrix.gif"))

    @imgmanip.command(name="melt")
    async def melt(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Melt filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Melt filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/melt",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "melt.gif"))

    @imgmanip.command(name="minecraft")
    async def minecraft(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Minecraft filter with a random size (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        # Choose a random size between 10 and 100 inclusive
        size = random.randint(10, 100)

        await ctx.send(f"🔄 Applying Minecraft filter… (size={size})")
        try:
            data = await self._fetch(
                endpoint="v2/image/minecraft",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img_url,
                    "size": size,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "minecraft.gif"))


    @imgmanip.command(name="neon")
    async def neon(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Neon filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Neon filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/neon",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "neon.gif"))

    @imgmanip.command(name="optics")
    async def optics(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Optics filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Optics filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/optics",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "optics.gif"))

    @imgmanip.command(name="painting")
    async def painting(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Painting filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Painting filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/painting",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "painting.gif"))

    @imgmanip.command(name="paparazzi")
    async def paparazzi(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Paparazzi filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Paparazzi filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/paparazzi",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "paparazzi.gif"))

    @imgmanip.command(name="patpat")
    async def patpat(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Patpat filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Patpat filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/patpat",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "patpat.gif"))

    @imgmanip.command(name="pattern")
    async def pattern(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Pattern filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Pattern filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/pattern",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "pattern.gif"))

    @imgmanip.command(name="phase")
    async def phase(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Phase filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Phase filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/phase",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "phase.gif"))

    @imgmanip.command(name="phone")
    async def phone(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Phone filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Phone filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/phone",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "phone.gif"))

    @imgmanip.command(name="pizza")
    async def pizza(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Pizza filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Pizza filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/pizza",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "pizza.gif"))

    @imgmanip.command(name="plank")
    async def plank(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Plank filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Plank filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/plank",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "plank.gif"))

    @imgmanip.command(name="plates")
    async def plates(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Plates filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Plates filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/plates",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "plates.gif"))

    @imgmanip.command(name="poly")
    async def poly(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Poly filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Poly filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/poly",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "poly.gif"))

    @imgmanip.command(name="print")
    async def print(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Print filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Print filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/print",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "print.gif"))

    @imgmanip.command(name="pyramid")
    async def pyramid(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Pyramid filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Pyramid filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/pyramid",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "pyramid.gif"))

    @imgmanip.command(name="quarter")
    async def quarter(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Quarter filter using the API default size (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Quarter filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/quarter",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "quarter.gif"))




    @imgmanip.command(name="radiate")
    async def radiate(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Radiate filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Radiate filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/radiate",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "radiate.gif"))

    @imgmanip.command(name="rain")
    async def rain(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Rain filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Rain filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/rain",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "rain.gif"))

    @imgmanip.command(name="reflection")
    async def reflection(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Reflection filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Reflection filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/reflection",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "reflection.gif"))

    @imgmanip.command(name="ripped")
    async def ripped(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Ripped filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Ripped filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/ripped",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "ripped.gif"))

    @imgmanip.command(name="ripple")
    async def ripple(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Ripple filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Ripple filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/ripple",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "ripple.gif"))

    @imgmanip.command(name="roll")
    async def roll(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Roll filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Roll filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/roll",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "roll.gif"))

    @imgmanip.command(name="scrapbook")
    async def scrapbook(self, ctx, *, text: str):
        """Generate a scrapbook-style image from your text."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        if not text:
            return await ctx.send("❌ Please provide some text to generate the scrapbook image.")

        await ctx.send("🔄 Generating Scrapbook image…")
        try:
            data = await self._fetch(
                endpoint="v2/image/scrapbook",
                api_key=api_key,
                method="GET",
                params={"text": text},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error generating scrapbook: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "scrapbook.gif"))

    @imgmanip.command(name="sensitive")
    async def sensitive(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Sensitive filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Sensitive filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/sensitive",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "sensitive.gif"))

    @imgmanip.command(name="shear")
    async def shear(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Shear filter with random axis and offsets (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        # Pick a random axis and offsets
        axis = random.choice(['x', 'X', 'y', 'Y'])
        x_offset = round(random.uniform(-1.0, 1.0), 2)
        y_offset = round(random.uniform(-1.0, 1.0), 2)

        await ctx.send(f"🔄 Applying Shear filter… (axis={axis}, x={x_offset}, y={y_offset})")
        try:
            data = await self._fetch(
                endpoint="v2/image/shear",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img_url,
                    "axis": axis,
                    "x": x_offset,
                    "y": y_offset,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "shear.gif"))

    @imgmanip.command(name="shine")
    async def shine(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Shine filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Shine filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/shine",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "shine.gif"))

    @imgmanip.command(name="shock")
    async def shock(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Shock filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Shock filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/shock",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "shock.gif"))

    @imgmanip.command(name="shoot")
    async def shoot(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Shoot filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Shoot filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/shoot",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "shoot.gif"))

    @imgmanip.command(name="shred")
    async def shred(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Shred filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Shred filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/shred",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "shred.gif"))

    @imgmanip.command(name="slice")
    async def slice(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Slice filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Slice filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/slice",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "slice.gif"))

    @imgmanip.command(name="soap")
    async def soap(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Soap filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Soap filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/soap",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "soap.gif"))

    @imgmanip.command(name="spikes")
    async def spikes(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Spikes filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Spikes filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/spikes",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "spikes.gif"))

    @imgmanip.command(name="spin")
    async def spin(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Spin filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Spin filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/spin",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "spin.gif"))

    @imgmanip.command(name="stereo")
    async def stereo(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Stereo filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Stereo filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/stereo",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "stereo.gif"))

    @imgmanip.command(name="stretch")
    async def stretch(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Stretch filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Stretch filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/stretch",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "stretch.gif"))

    @imgmanip.command(name="tiles")
    async def tiles(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Tiles filter with a random n_edges (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        # Pick a random n_edges from the allowed values
        n_edges = random.choice(['3', '4', '5', '6', '7', '8'])

        await ctx.send(f"🔄 Applying Tiles filter… (n_edges={n_edges})")
        try:
            data = await self._fetch(
                endpoint="v2/image/tiles",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img_url,
                    "n_edges": n_edges,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "tiles.gif"))

    @imgmanip.command(name="tunnel")
    async def tunnel(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Tunnel filter with a random direction (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        # Pick a random direction from the allowed values
        direction = random.choice(['h', 'v', 'c', 'r'])

        await ctx.send(f"🔄 Applying Tunnel filter… (direction={direction})")
        try:
            data = await self._fetch(
                endpoint="v2/image/tunnel",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img_url,
                    "direction": direction,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "tunnel.gif"))

    @imgmanip.command(name="tv")
    async def tv(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Tv filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Tv filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/tv",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "tv.gif"))

    @imgmanip.command(name="wall")
    async def wall(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Wall filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Wall filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/wall",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "wall.gif"))

    @imgmanip.command(name="warp")
    async def warp(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Warp filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Warp filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/warp",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "warp.gif"))

    @imgmanip.command(name="wave")
    async def wave(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Wave filter with random frequency and amplitude (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        # Pick random values
        frequency = round(random.uniform(0.01, 0.20), 3)
        amplitude = random.choice(['1', '2', '3', '4', '5'])

        await ctx.send(f"🔄 Applying Wave filter… (frequency={frequency}, amplitude={amplitude})")
        try:
            data = await self._fetch(
                endpoint="v2/image/wave",
                api_key=api_key,
                method="GET",
                params={
                    "image_url": img_url,
                    "frequency": frequency,
                    "amplitude": amplitude,
                },
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "wave.gif"))

    @imgmanip.command(name="wiggle")
    async def wiggle(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Wiggle filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Wiggle filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/wiggle",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "wiggle.gif"))

    @imgmanip.command(name="zonk")
    async def zonk(self, ctx, target: Optional[Union[discord.Member, str]] = None):
        """Apply Zonk filter (attachment, @mention, URL or your avatar)."""
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        img_url = await self._resolve_image_url(ctx, target)
        if not img_url:
            return await ctx.send("❌ Please provide an image (mention, URL, or attachment).")

        await ctx.send("🔄 Applying Zonk filter…")
        try:
            data = await self._fetch(
                endpoint="v2/image/zonk",
                api_key=api_key,
                method="GET",
                params={"image_url": img_url},
            )
        except Exception as e:
            return await ctx.send(f"❌ Error fetching filter: {e}")

        fp = io.BytesIO(data)
        fp.seek(0)
        await ctx.send(file=discord.File(fp, "zonk.gif"))

    @imgmanip.command(name="wheel")
    async def wheel(self, ctx, *words: str):
        api_key = await self.config.user(ctx.author).api_key()
        if not api_key:
            return await ctx.send("❌ Set your API key: `[p]imgmanip setkey YOUR_KEY`.")

        words = [w.strip() for w in words if w and w.strip()]
        n = len(words)
        if n not in (2, 3, 4, 6):
            return await ctx.send("❌ Wheel requires exactly 2, 3, 4 or 6 words. Provide them space-separated.")

        await ctx.send("🔄 Spinning the wheel…")

        params = {f"w{i+1}": words[i] for i in range(n)}
        params["words"] = ",".join(words)
        params["count"] = n

        # Try GET first
        try:
            data = await self._fetch(
                endpoint="v2/discord/wheel",
                api_key=api_key,
                method="GET",
                params=params,
            )
        except Exception as e:
            err = str(e)
            # If API explicitly sent a 400 with a helpful message, try POST fallback
            if err.startswith("HTTP 400"):
                try:
                    payload = {f"w{i+1}": words[i] for i in range(n)}
                    payload["words"] = ",".join(words)
                    payload["count"] = n
                    data = await self._fetch(
                        endpoint="v2/discord/wheel",
                        api_key=api_key,
                        method="POST",
                        payload=payload,
                    )
                except Exception as e2:
                    # Return the detailed API error (POST attempt) back to user
                    text = str(e2)
                    # Show trimmed API message
                    return await ctx.send(f"❌ Wheel failed: {text}")
            else:
                return await ctx.send(f"❌ Wheel failed: {err}")

        # Try to send image bytes, if not binary image show returned text
        try:
            fp = io.BytesIO(data)
            fp.seek(0)
            await ctx.send(file=discord.File(fp, "wheel.gif"))
        except Exception:
            text = data.decode("utf-8", errors="replace")
            await ctx.send(f"❌ Wheel returned text: {text}")


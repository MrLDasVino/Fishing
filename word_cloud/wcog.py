import asyncio
import random
import io
import aiosqlite
import regex as re
from datetime import datetime

import discord
from PIL import Image, ImageDraw
import os
import aiohttp
from wordcloud import WordCloud

from redbot.core import commands, checks
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

# pick up the system’s emoji font
_EMOJI_CANDIDATES = [
    "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf",   
    "/usr/share/fonts/truetype/ancient-fonts/Symbola.ttf",          
    "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
]
for p in _EMOJI_CANDIDATES:
    if os.path.isfile(p):
        EMOJI_FONT = p
        break
else:
    EMOJI_FONT = None

DB_PATH = "wordcloud_data.sqlite3"

# Basic stopwords (can be extended or made per-guild later)
STOPWORDS = {
    "the", "and", "for", "that", "with", "you", "this", "have", "are",
    "but", "not", "was", "from", "they", "she", "he", "it", "in", "on",
    "a", "an", "of", "to", "is", "i", "we", "me", "my", "our", "be",
    "as", "at", "by", "or", "if", "so", "do", "did", "does", "got",
}

# Unicode emoji capture using regex module (broad)
UNICODE_EMOJI_RE = re.compile(r'(\p{Emoji_Presentation}|\p{Emoji}\uFE0F)', re.IGNORECASE)
# Discord custom emoji like <:name:123456789012345678> or <a:name:123456789012345678>
CUSTOM_EMOJI_RE = re.compile(r"<a?:([a-zA-Z0-9_]+):([0-9]{17,22})>")

# Words: letters only, length >=2
WORD_REGEX = re.compile(r"\b[^\W\d_]{2,}\b", flags=re.UNICODE)

def random_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return "rgb({}, {}, {})".format(random.randint(0,255), random.randint(0,255), random.randint(0,255))

class WordCloudCog(commands.Cog):
    """Track words and emojis per-user and per-guild, render transparent PNG word-clouds."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.db_ready = False
        self._autogen_task = self.bot.loop.create_task(self._ensure_db_and_task())

    async def _ensure_db_and_task(self):
        await self.init_db()
        self.autogen = False
        self.autogen_interval = 3600
        self.autogen_channel = None

    async def init_db(self):
        if self.db_ready:
            return
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS counts (
                    guild_id INTEGER,
                    user_id INTEGER,
                    token TEXT,
                    count INTEGER,
                    PRIMARY KEY (guild_id, user_id, token)
                )"""
            )
            await db.execute(
                """CREATE TABLE IF NOT EXISTS config (
                    guild_id INTEGER PRIMARY KEY,
                    autogen INTEGER DEFAULT 0,
                    autogen_interval INTEGER DEFAULT 3600,
                    autogen_channel INTEGER
                )"""
            )
            await db.commit()
        self.db_ready = True

    async def cog_unload(self):
        if self._autogen_task:
            self._autogen_task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return

        content = message.content or ""
        tokens = []

        # Extract custom Discord emojis first and normalize them
        for m in CUSTOM_EMOJI_RE.finditer(content):
            name, eid = m.groups()
            tokens.append(f"custom_{name}:{eid}")

        # Extract unicode emojis
        tokens.extend(UNICODE_EMOJI_RE.findall(content))

        # Extract words
        for m in WORD_REGEX.finditer(content.lower()):
            w = m.group(0)
            if w in STOPWORDS:
                continue
            tokens.append(w)

        if not tokens:
            return

        await self._increment_tokens(message.guild.id, message.author.id, tokens)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.abc.User):
        # Count reaction as an emoji usage (who reacted counts)
        if user.bot:
            return
        message = reaction.message
        if not message.guild:
            return
        e = reaction.emoji
        if isinstance(e, str):
            token = e  # unicode emoji
        else:
            # PartialEmoji or Emoji object
            # Some objects may have no id (unlikely), guard accordingly
            token = f"custom_{e.name}:{e.id}" if getattr(e, "id", None) else f"custom_{e.name}:none"
        await self._increment_tokens(message.guild.id, user.id, [token])

    async def _increment_tokens(self, guild_id: int, user_id: int, tokens: list):
        await self.init_db()
        # Normalize tokens to str and limit token length to avoid huge keys
        norm_tokens = [str(t)[:200] for t in tokens if t]
        if not norm_tokens:
            return
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.cursor()
            for t in norm_tokens:
                await cur.execute(
                    "INSERT INTO counts(guild_id, user_id, token, count) VALUES(?, ?, ?, 1) "
                    "ON CONFLICT(guild_id, user_id, token) DO UPDATE SET count = count + 1",
                    (guild_id, user_id, t)
                )
            await db.commit()

    async def _get_frequencies_for_guild(self, guild_id: int):
        await self.init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "SELECT token, SUM(count) as count FROM counts WHERE guild_id = ? GROUP BY token ORDER BY count DESC",
                (guild_id,)
            )
            rows = await cur.fetchall()
        return {r[0]: r[1] for r in rows}

    async def _get_frequencies_for_user(self, guild_id: int, user_id: int):
        await self.init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "SELECT token, count FROM counts WHERE guild_id = ? AND user_id = ? ORDER BY count DESC",
                (guild_id, user_id)
            )
            rows = await cur.fetchall()
        return {r[0]: r[1] for r in rows}

    async def _get_frequencies_for_users(self, guild_id: int, user_ids: list):
        if not user_ids:
            return {}
        await self.init_db()
        placeholders = ",".join("?" for _ in user_ids)
        query = f"SELECT token, SUM(count) as count FROM counts WHERE guild_id = ? AND user_id IN ({placeholders}) GROUP BY token ORDER BY count DESC"
        params = [guild_id] + user_ids
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(query, params)
            rows = await cur.fetchall()
        return {r[0]: r[1] for r in rows}

    async def _render_wordcloud_image(self, frequencies: dict, width=1200, height=675):
        """
        Render a wordcloud PNG with:
        - transparent background
        - real Unicode emojis via EMOJI_FONT
        - custom Discord emojis pasted over
        """
        buf = io.BytesIO()

        # 1) Empty case
        if not frequencies:
            img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            img.save(buf, format="PNG")
            buf.seek(0)
            return buf

        # 2) Build WordCloud with emoji-capable font if available
        wc_kwargs = {
            "width": width,
            "height": height,
            "mode": "RGBA",
            "background_color": None,
            "prefer_horizontal": 0.9,
            "collocations": False,
        }
        if EMOJI_FONT:
            wc_kwargs["font_path"] = EMOJI_FONT
            wc_kwargs["min_font_size"] = 10

        wc = WordCloud(**wc_kwargs)
        wc.generate_from_frequencies(frequencies)
        wc.recolor(color_func=random_color_func, random_state=random.Random(42))

        # 3) Convert to PIL image and grab layout
        img = wc.to_image().convert("RGBA")
        layout = wc.layout_  # list of tuples

        # 4) Overlay custom emojis
        async with aiohttp.ClientSession() as session:
            for entry in layout:
                # entry[0] is always the word string
                word = entry[0]
                if not word.startswith("custom_"):
                    continue

                # unpack font_size & position by tuple length
                if len(entry) == 6:
                    _, _, font_size, position, orientation, color = entry
                else:
                    _, font_size, position, orientation, color = entry

                # extract emoji ID
                _, rest = word.split("custom_", 1)
                _, eid = rest.split(":", 1)

                # fetch & paste emoji
                url = f"https://cdn.discordapp.com/emojis/{eid}.png?size=64"
                try:
                    async with session.get(url) as resp:
                        data = await resp.read()
                        em = Image.open(io.BytesIO(data)).convert("RGBA")
                except Exception:
                    continue

                em = em.resize((font_size, font_size), Image.ANTIALIAS)
                x, y = position
                img.paste(em, (x, y), em)

        # 5) Save & return
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf


    async def _maybe_autogen_loop(self):
        await self.bot.wait_until_ready()
        while True:
            await asyncio.sleep(60)
            await self.init_db()
            async with aiosqlite.connect(DB_PATH) as db:
                cur = await db.execute("SELECT guild_id, autogen_interval, autogen_channel FROM config WHERE autogen = 1")
                rows = await cur.fetchall()
                for guild_id, interval, channel_id in rows:
                    key = f"autogen_last_{guild_id}"
                    last = getattr(self, key, None)
                    now = datetime.utcnow()
                    if last is None or (now - last).total_seconds() >= interval:
                        guild = self.bot.get_guild(guild_id)
                        if guild is None:
                            continue
                        ch = guild.get_channel(channel_id) if channel_id else None
                        if ch is None:
                            for c in guild.text_channels:
                                if c.permissions_for(guild.me).send_messages:
                                    ch = c
                                    break
                        if ch is None:
                            continue
                        freqs = await self._get_frequencies_for_guild(guild_id)
                        buf = await self._render_wordcloud_image(freqs)
                        try:
                            await ch.send(file=discord.File(fp=buf, filename="wordcloud.png"))
                        except Exception:
                            pass
                        setattr(self, key, now)

    @commands.group()
    @checks.admin()
    async def wordcloud(self, ctx: commands.Context):
        """Wordcloud management commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @wordcloud.command()
    async def generate(self, ctx: commands.Context, *members: discord.Member):
        """Generate and post the wordcloud.

        No args = aggregated guild cloud.
        Mention users = per-user or merged user cloud.
        Examples:
        [p]wordcloud generate
        [p]wordcloud generate @user
        [p]wordcloud generate @user1 @user2
        """
        if not members:
            freqs = await self._get_frequencies_for_guild(ctx.guild.id)
            title = f"Wordcloud for guild: {ctx.guild.name}"
        elif len(members) == 1:
            target = members[0]
            freqs = await self._get_frequencies_for_user(ctx.guild.id, target.id)
            title = f"Wordcloud for user: {target.display_name}"
        else:
            user_ids = [m.id for m in members]
            freqs = await self._get_frequencies_for_users(ctx.guild.id, user_ids)
            names = ", ".join(m.display_name for m in members)
            title = f"Wordcloud for users: {names}"

        if not freqs:
            await ctx.send("No data to generate a wordcloud.")
            return

        buf = await self._render_wordcloud_image(freqs)
        try:
            await ctx.send(content=title, file=discord.File(fp=buf, filename="wordcloud.png"))
        except Exception:
            await ctx.send("Failed to send image; check my permissions.")

    @wordcloud.command()
    async def stats(self, ctx: commands.Context, limit: int = 20):
        """Show top words/emojis for guild."""
        await self.init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("SELECT token, SUM(count) as count FROM counts WHERE guild_id = ? GROUP BY token ORDER BY count DESC LIMIT ?", (ctx.guild.id, limit))
            rows = await cur.fetchall()
        if not rows:
            await ctx.send("No data yet.")
            return
        lines = [f"{r[0]}: {r[1]}" for r in rows]
        await ctx.send(box("\n".join(lines)))

    @wordcloud.command()
    async def reset(self, ctx: commands.Context):
        """Reset stored counts for this guild."""
        await self.init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM counts WHERE guild_id = ?", (ctx.guild.id,))
            await db.execute("DELETE FROM config WHERE guild_id = ?", (ctx.guild.id,))
            await db.commit()
        await ctx.send("Word counts reset for this guild.")

    @wordcloud.command()
    async def set_autogen(self, ctx: commands.Context, enabled: bool):
        """Enable or disable periodic generation."""
        await self.init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO config(guild_id, autogen) VALUES(?, ?) ON CONFLICT(guild_id) DO UPDATE SET autogen = ?",
                (ctx.guild.id, 1 if enabled else 0, 1 if enabled else 0)
            )
            await db.commit()
        await ctx.send(f"Autogen set to {enabled}.")

    @wordcloud.command()
    async def set_autogen_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set channel where autogen will post. If omitted sets current channel."""
        ch = channel or ctx.channel
        await self.init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO config(guild_id, autogen_channel) VALUES(?, ?) ON CONFLICT(guild_id) DO UPDATE SET autogen_channel = ?",
                (ctx.guild.id, ch.id, ch.id)
            )
            await db.commit()
        await ctx.send(f"Autogen channel set to {ch.mention}")

    @wordcloud.command()
    async def set_autogen_interval(self, ctx: commands.Context, seconds: int):
        """Set autogen interval in seconds (minimum 60)."""
        if seconds < 60:
            await ctx.send("Interval must be at least 60 seconds.")
            return
        await self.init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO config(guild_id, autogen_interval) VALUES(?, ?) ON CONFLICT(guild_id) DO UPDATE SET autogen_interval = ?",
                (ctx.guild.id, seconds, seconds)
            )
            await db.commit()
        await ctx.send(f"Autogen interval set to {seconds} seconds.")

async def setup(bot):
    cog = WordCloudCog(bot)
    await bot.add_cog(cog)
    bot.loop.create_task(cog._maybe_autogen_loop())

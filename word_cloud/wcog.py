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
from collections import OrderedDict
from wordcloud import WordCloud

from pathlib import Path
from redbot.core.data_manager import cog_data_path
from redbot.core import commands, checks
from discord.ext import tasks 
from redbot.core.bot import Red



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
    def __init__(self, bot: Red):
        self.bot = bot
        self.db_ready = False

        # persistent HTTP session & LRU cache
        self._session = aiohttp.ClientSession()
        self._emoji_cache: OrderedDict[str, Image.Image] = OrderedDict()
        self._cache_max = 200

        data_folder: Path = Path(cog_data_path(self))
        data_folder.mkdir(parents=True, exist_ok=True)
        self.db_path: str = str(data_folder / "wordcloud_data.sqlite3")

        # one-time DB/config setup
        self.bot.loop.create_task(self._ensure_db_and_task())

    async def cog_load(self):
        """Start the periodic autogen loop when the cog goes live."""
        self.autogen_loop.start()

    async def cog_unload(self):
        """Stop the loop and close our session on unload."""
        if self.autogen_loop.is_running():
            self.autogen_loop.cancel()
        await self._session.close()

    async def _ensure_db_and_task(self):
        await self.init_db()
        self.autogen = False
        self.autogen_interval = 3600
        self.autogen_channel = None

    async def init_db(self):
        if self.db_ready:
            return
        async with aiosqlite.connect(self.db_path) as db:
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
            await db.execute(
                """CREATE TABLE IF NOT EXISTS ignored_channels (
                       guild_id   INTEGER,
                       channel_id INTEGER,
                       PRIMARY KEY (guild_id, channel_id)
                   )"""
            )            
            await db.commit()
        self.db_ready = True

    async def cog_load(self):
        """Called when the cog is loaded; start the autogen loop."""
        self.autogen_loop.start()

    async def cog_unload(self):
        """Cleanly stop the loop and close resources."""
        if self.autogen_loop.is_running():
            self.autogen_loop.cancel()
        await self._session.close()            

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        # ─── skip if channel is ignored ───────────────────────────
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT 1 FROM ignored_channels WHERE guild_id = ? AND channel_id = ?",
                (message.guild.id, message.channel.id),
            )
            if await cur.fetchone():
                return            

        raw = message.content or ""
        tokens = []

        # 1) Pull out custom emojis, record them, and strip them from the text
        def _repl_custom(m):
            name, eid = m.groups()
            tokens.append(f"custom_{name}:{eid}")
            return ""
        text = CUSTOM_EMOJI_RE.sub(_repl_custom, raw)

        # 2) Pull out unicode emojis, record them, and strip them
        def _repl_unicode(m):
            tokens.append(m.group(0))
            return ""
        text = UNICODE_EMOJI_RE.sub(_repl_unicode, text)

        # 3) Now extract only real words from the cleaned‐up text
        for m in WORD_REGEX.finditer(text.lower()):
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
        # skip ignored channel
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT 1 FROM ignored_channels WHERE guild_id = ? AND channel_id = ?",
                (message.guild.id, message.channel.id),
            )
            if await cur.fetchone():
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
        async with aiosqlite.connect(self.db_path) as db:
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
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT token, SUM(count) as count FROM counts WHERE guild_id = ? GROUP BY token ORDER BY count DESC",
                (guild_id,)
            )
            rows = await cur.fetchall()
        return {r[0]: r[1] for r in rows}

    async def _get_frequencies_for_user(self, guild_id: int, user_id: int):
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
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
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(query, params)
            rows = await cur.fetchall()
        return {r[0]: r[1] for r in rows}

    async def _render_wordcloud_image(self, frequencies: dict, width=1200, height=675):
        import io
        from PIL import Image
        from wordcloud import WordCloud

        buf = io.BytesIO()
        if not frequencies:
            img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            img.save(buf, format="PNG")
            buf.seek(0)
            return buf

        # build and generate full layout
        wc_kwargs = {
            "width": width,
            "height": height,
            "mode": "RGBA",
            "background_color": None,
            "prefer_horizontal": 0.9,
            "collocations": False,
        }


        wc = WordCloud(**wc_kwargs)
        wc.generate_from_frequencies(frequencies)
        wc.recolor(
            color_func=lambda word, font_size, position, orientation, random_state=None, **kwargs: (
                "rgba(0,0,0,0)"
                if str(word).startswith("custom_")
                else random_color_func(word, font_size, position, orientation, random_state=random_state)
            ),
            random_state=random.Random(42),
        )

        # split layout
        full_layout = wc.layout_
        word_entries, emoji_entries = [], []
        for entry in full_layout:
            raw = entry[0]
            token = raw[0] if isinstance(raw, tuple) else raw
            # detect ANY emoji token: custom_<name>:<id> OR unicode-char
            is_custom = isinstance(token, str) and token.startswith("custom_")
            is_unicode = isinstance(token, str) and UNICODE_EMOJI_RE.fullmatch(token)
            if is_custom or is_unicode:
                emoji_entries.append(entry)
            else:
                word_entries.append(entry)

        # render words only
        wc.layout_ = word_entries
        base_img = wc.to_image().convert("RGBA")

        # overlay emojis with persistent session & LRU cache
        session = self._session
        for entry in emoji_entries:
            raw = entry[0]
            token = raw[0] if isinstance(raw, tuple) else raw

            # unpack size & position
            if len(entry) == 6:
                _, _, font_size, position, orientation, color = entry
            else:
                _, font_size, position, orientation, color = entry

            if token.startswith("custom_"):
                # custom_<name>:<id>
                _, rest = token.split("custom_", 1)
                _, eid = rest.split(":", 1)
                url = f"https://cdn.discordapp.com/emojis/{eid}.png?size=64"
                cache_key = f"custom:{eid}"
            else:
                # unicode emoji: build codepoint path for Twemoji
                cps = "-".join(f"{ord(c):x}" for c in token)
                url = f"https://twemoji.maxcdn.com/v/latest/72x72/{cps}.png"
                cache_key = f"unic:{cps}"

            # cache lookup by cache_key
            if cache_key in self._emoji_cache:
                em = self._emoji_cache[cache_key]
                self._emoji_cache.move_to_end(cache_key)
            else:
                try:
                    async with session.get(url) as resp:
                        data = await resp.read()
                        em = Image.open(io.BytesIO(data)).convert("RGBA")
                except Exception:
                    continue
                # resize to font_size × font_size
                try:
                    resample = Image.Resampling.LANCZOS
                except AttributeError:
                    resample = Image.LANCZOS
                em = em.resize((font_size, font_size), resample)
                # insert into LRU cache
                self._emoji_cache[cache_key] = em
                if len(self._emoji_cache) > self._cache_max:
                    self._emoji_cache.popitem(last=False)

            # paste emoji on top
            x, y = position
            base_img.paste(em, (x, y), em)

        # save and return
        base_img.save(buf, format="PNG")
        buf.seek(0)
        return buf
        
    @tasks.loop(minutes=1)
    async def autogen_loop(self):
        """Periodic wordcloud generation for all guilds with autogen=1."""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT guild_id, autogen_interval, autogen_channel FROM config WHERE autogen = 1"
            )
            rows = await cur.fetchall()
        for guild_id, interval, channel_id in rows:
            key = f"autogen_last_{guild_id}"
            last = getattr(self, key, None)
            now = datetime.utcnow()
            if last is None or (now - last).total_seconds() >= interval:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                ch = guild.get_channel(channel_id) if channel_id else None
                if not ch:
                    for c in guild.text_channels:
                        if c.permissions_for(guild.me).send_messages:
                            ch = c
                            break
                if not ch:
                    continue
                freqs = await self._get_frequencies_for_guild(guild_id)
                buf = await self._render_wordcloud_image(freqs)
                try:
                    await ch.send(file=discord.File(fp=buf, filename="wordcloud.png"))
                except Exception:
                    pass
                setattr(self, key, now)

    @autogen_loop.before_loop
    async def before_autogen(self):
        await self.bot.wait_until_ready()


    @commands.group()
    async def wordcloud(self, ctx: commands.Context):
        """Wordcloud management commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()
            
    @wordcloud.command(name="ignore")
    @checks.admin()
    async def ignore(self, ctx, channel: discord.TextChannel):
        """Ignore data collection in a channel."""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO ignored_channels (guild_id, channel_id) VALUES (?, ?)",
                (ctx.guild.id, channel.id),
            )
            await db.commit()
        await ctx.send(f"Ignoring data in {channel.mention}.")

    @wordcloud.command(name="unignore")
    @checks.admin()
    async def unignore(self, ctx, channel: discord.TextChannel):
        """Stop ignoring a channel."""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM ignored_channels WHERE guild_id = ? AND channel_id = ?",
                (ctx.guild.id, channel.id),
            )
            await db.commit()
        await ctx.send(f"Resumed data collection in {channel.mention}.")

    @wordcloud.command(name="ignored")
    @checks.admin()
    async def ignored(self, ctx):
        """List all ignored channels."""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT channel_id FROM ignored_channels WHERE guild_id = ?",
                (ctx.guild.id,),
            )
            rows = await cur.fetchall()
        if not rows:
            return await ctx.send("No ignored channels.")
        mentions = []
        for (cid,) in rows:
            ch = ctx.guild.get_channel(cid)
            mentions.append(ch.mention if ch else f"<#{cid}>")
        await ctx.send("Ignored channels: " + ", ".join(mentions))

    @wordcloud.command(name="me")
    async def me(self, ctx):
        """Generate your personal wordcloud."""
        freqs = await self._get_frequencies_for_user(ctx.guild.id, ctx.author.id)
        if not freqs:
            return await ctx.send("No data collected for you yet.")
        buf = await self._render_wordcloud_image(freqs)
        await ctx.send(
            content=f"Wordcloud for {ctx.author.display_name}",
            file=discord.File(fp=buf, filename="wordcloud.png"),
        )
            

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

    @wordcloud.command(name="stats")
    async def stats(self, ctx: commands.Context, limit: int = 20):
        """Show top emojis and words for guild, paginated by reactions."""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT token, SUM(count) AS count "
                "FROM counts WHERE guild_id = ? "
                "GROUP BY token ORDER BY count DESC LIMIT ?",
                (ctx.guild.id, limit * 2),  # fetch extra to split pages
            )
            rows = await cur.fetchall()

        if not rows:
            return await ctx.send("No data yet.")

        # Helpers
        def display_token(token: str) -> str:
            if token.startswith("custom_"):
                name, eid = token.split("custom_", 1)[1].split(":", 1)
                return f"<:{name}:{eid}>"
            return token

        # Split rows into emojis vs words
        emojis = [(display_token(tok), cnt) for tok, cnt in rows if tok.startswith("custom_")]
        words  = [(tok, cnt)            for tok, cnt in rows if not tok.startswith("custom_")]

        # Build two pages
        embed_emoji = discord.Embed(
            title="📊 Top Emojis",
            description="\n".join(f"{t}: {c}" for t, c in emojis[:limit]) or "None",
            color=discord.Color.random(),
        )
        embed_words = discord.Embed(
            title="📊 Top Words",
            description="\n".join(f"{t}: {c}" for t, c in words[:limit]) or "None",
            color=discord.Color.random(),
        )
        pages = [embed_emoji, embed_words]

        # Send first page and add reactions
        message = await ctx.send(embed=pages[0])
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")

        # Reaction check: only the invoker can flip pages
        def check(reaction, user):
            return (
                user == ctx.author
                and reaction.message.id == message.id
                and str(reaction.emoji) in ("◀️", "▶️")
            )

        page = 0
        # Listen for reactions
        try:
            while True:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                # Flip page
                if str(reaction.emoji) == "▶️":
                    page = (page + 1) % len(pages)
                else:
                    page = (page - 1) % len(pages)
                await message.edit(embed=pages[page])
                # Remove the user's reaction for cleanliness
                await message.remove_reaction(reaction.emoji, user)
        except asyncio.TimeoutError:
            # Timeout: remove controls (optional)
            try:
                await message.clear_reactions()
            except Exception:
                pass



    @wordcloud.command()
    @checks.admin()
    async def reset(self, ctx: commands.Context):
        """Reset stored counts for this guild."""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM counts WHERE guild_id = ?", (ctx.guild.id,))
            await db.execute("DELETE FROM config WHERE guild_id = ?", (ctx.guild.id,))
            await db.commit()
        await ctx.send("Word counts reset for this guild.")

    @wordcloud.command()
    @checks.admin()
    async def set_autogen(self, ctx: commands.Context, enabled: bool):
        """Enable or disable periodic generation."""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO config(guild_id, autogen) VALUES(?, ?) ON CONFLICT(guild_id) DO UPDATE SET autogen = ?",
                (ctx.guild.id, 1 if enabled else 0, 1 if enabled else 0)
            )
            await db.commit()
        await ctx.send(f"Autogen set to {enabled}.")

    @wordcloud.command()
    @checks.admin()
    async def set_autogen_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set channel where autogen will post. If omitted sets current channel."""
        ch = channel or ctx.channel
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO config(guild_id, autogen_channel) VALUES(?, ?) ON CONFLICT(guild_id) DO UPDATE SET autogen_channel = ?",
                (ctx.guild.id, ch.id, ch.id)
            )
            await db.commit()
        await ctx.send(f"Autogen channel set to {ch.mention}")

    @wordcloud.command()
    @checks.admin()
    async def set_autogen_interval(self, ctx: commands.Context, seconds: int):
        """Set autogen interval in seconds (minimum 60)."""
        if seconds < 60:
            await ctx.send("Interval must be at least 60 seconds.")
            return
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO config(guild_id, autogen_interval) VALUES(?, ?) ON CONFLICT(guild_id) DO UPDATE SET autogen_interval = ?",
                (ctx.guild.id, seconds, seconds)
            )
            await db.commit()
        await ctx.send(f"Autogen interval set to {seconds} seconds.")

async def setup(bot):
    cog = WordCloudCog(bot)
    await bot.add_cog(cog)
    

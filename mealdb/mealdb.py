import aiohttp
import discord

from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify

class MealDB(commands.Cog):
    """Fetch recipes via TheMealDB API."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def fetch_json(self, url: str) -> dict:
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    @commands.command(name="meal")
    async def meal(self, ctx, *, query: str = None):
        """
        Fetch a random meal or search by name.
        Usage:
          [p]meal random
          [p]meal <search term>
        """
        if not query or query.lower() == "random":
            data = await self.fetch_json(
                "https://www.themealdb.com/api/json/v1/1/random.php"
            )
            meals = data.get("meals") or []
        else:
            data = await self.fetch_json(
                f"https://www.themealdb.com/api/json/v1/1/search.php?s={query}"
            )
            meals = data.get("meals") or []

        if not meals:
            return await ctx.send(f"No meals found for `{query}`.")

        meal = meals[0]
        embed = await self.build_embed(meal)
        await ctx.send(embed=embed)

    async def build_embed(self, meal: dict) -> discord.Embed:
        title = meal["strMeal"]
        source = meal.get("strSource") or meal.get("strYoutube") or None
        embed = discord.Embed(
            title=title,
            url=source,
            description=meal.get("strCategory", ""),
            color=0xE67E22
        )
        embed.set_thumbnail(url=meal["strMealThumb"])

        # List ingredients with clickable links
        ingredients = []
        for i in range(1, 21):
            ing = meal.get(f"strIngredient{i}")
            meas = meal.get(f"strMeasure{i}")
            if ing and ing.strip():
                link = f"https://www.themealdb.com/search.php?i={ing.replace(' ', '%20')}"
                ingredients.append(f"[{ing} →]({link}) • {meas}")

        embed.add_field(name="Ingredients", value="\n".join(ingredients), inline=False)

        # Paginate instructions
        instructions = meal.get("strInstructions", "No instructions provided.").strip()
        for page in pagify(instructions, page_length=1024):
            embed.add_field(name="Instructions", value=page, inline=False)

        return 
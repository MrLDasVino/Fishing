# cogs/fishing/achievements.py

from functools import wraps
from typing import List
from redbot.core import bank
from .data import achievements as _ACH  # your metadata

def award_achievements(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        result = await func(self, ctx, *args, **kwargs)
        try:
            msgs = await self.ach_mgr.check_and_award(ctx, ctx.author)
            if msgs:
                await ctx.send("\n".join(msgs))
        except:
            pass
        return result
    return wrapper

class AchievementManager:
    def __init__(self, config):
        self.config = config
        self.meta   = _ACH

    async def has(self, user, aid: str) -> bool:
        earned = await self.config.user(user).achievements()
        return aid in earned

    async def award(self, ctx, user, aid: str) -> str:
        """
        1) mark earned in config
        2) compute and deposit coin reward
        3) grant any item rewards
        4) return announcement string
        """
    async def _award_achievement(self, ctx, user, ach_id: str) -> Optional[str]:
        if ach_id not in self.achievements:
            return None
        
        # 1) Mark it earned
        user_conf = self.config.user(user)
        earned = await user_conf.achievements()
        if ach_id in earned:
            return None
        earned.append(ach_id)
        await user_conf.achievements.set(earned)
        
        # 2) Figure out name/description
        name, desc, _ = self.achievements[ach_id]
        
        # 3) Compute rewards
        reward = 0
        add_items: Dict[str, int] = {}
        
        # legacy small rewards
        if ach_id in ("first_cast", "first_fish"):
            reward = 5
        
        # existing larger rewards
        if ach_id == "mythic_catch":
            reward = 100
        if ach_id == "treasure_hunter":
            reward = 25
        
        # new achievement rewards
        if ach_id == "first_chum":
            reward = 10
        if ach_id == "trophy_maker":
            reward = 25
        if ach_id == "fragment_collector":
            reward = 50
        if ach_id == "core_seeker":
            reward = 150
        if ach_id == "rod_master_1":
            reward = 20
        if ach_id == "rod_master_2":
            reward = 60
        if ach_id == "rod_master_3":
            reward = 180
        if ach_id == "npc_friend":
            add_items = {"Chum": 1}
        if ach_id == "quest_master":
            reward = 300
        if ach_id == "oceanographer":
            reward = 200
        if ach_id == "collector_100":
            reward = 150
        if ach_id == "seasoned_angler":
            reward = 100
        
        # 4) Build announcement text
        currency = await bank.get_currency_name(ctx.guild) if ctx and ctx.guild else "credits"
        parts: List[str] = [f"🏆 Achievement unlocked: **{name}** — {desc}"]
        
        # 5) Deposit coins if any
        if reward > 0:
            new_bal = await bank.deposit_credits(user, reward)
            parts.append(f"You received **{reward} {currency}**! New balance: **{new_bal} {currency}**.")
        
        # 6) Grant any item-only rewards
        if add_items:
            items_cfg = await user_conf.items()
            for iname, cnt in add_items.items():
                for _ in range(cnt):
                    items_cfg.append(iname)
            await user_conf.items.set(items_cfg)
            added = ", ".join(f"{c}× {n}" for n, c in add_items.items())
            parts.append(f"You also received {added}.")
        
        text = "\n".join(parts)

        return text
        …

    async def _check_and_award(self, ctx, user) -> List[str]:
        user_conf = self.config.user(user)
        stats = await user_conf.stats()
        caught = await user_conf.caught()
        earned = await user_conf.achievements()
        messages: List[str] = []

        if stats.get("casts", 0) >= 1 and "first_cast" not in earned:
            m = await self._award_achievement(ctx, user, "first_cast")
            if m:
                messages.append(m)

        # Mythic‐catch: did they ever catch a Mythic?
        if any(self.fish_definitions.get(f,{}).get("rarity") == "Mythic" for f in caught) \
           and "mythic_catch" not in earned:
            m = await self._award_achievement(ctx, user, "mythic_catch")
            if m:
                messages.append(m)

        # Oceanographer: caught every biome?
        try:
            caught_biomes = {self.fish_definitions[f]["biome"]
                             for f in set(caught) if f in self.fish_definitions}
            all_biomes = {info["biome"] for info in self.fish_definitions.values()}
            if all_biomes and caught_biomes >= all_biomes and "oceanographer" not in earned:
                m = await self._award_achievement(ctx, user, "oceanographer")
                if m:
                    messages.append(m)
        except Exception:
            pass                

        if stats.get("fish_caught", 0) >= 1 and "first_fish" not in earned:
            m = await self._award_achievement(ctx, user, "first_fish")
            if m:
                messages.append(m)

        if stats.get("fish_caught", 0) >= 10 and "fish_10" not in earned:
            m = await self._award_achievement(ctx, user, "fish_10")
            if m:
                messages.append(m)

        if stats.get("fish_caught", 0) >= 100 and "fish_100" not in earned:
            m = await self._award_achievement(ctx, user, "fish_100")
            if m:
                messages.append(m)

        unique = len(set(x for x in caught if x and not x.lower().startswith("treasure")))
        if unique >= 5 and "unique_5" not in earned:
            m = await self._award_achievement(ctx, user, "unique_5")
            if m:
                messages.append(m)
        if unique >= 25 and "unique_25" not in earned:
            m = await self._award_achievement(ctx, user, "unique_25")
            if m:
                messages.append(m)

        if stats.get("sell_total", 0) >= 1000 and "sell_1000" not in earned:
            m = await self._award_achievement(ctx, user, "sell_1000")
            if m:
                messages.append(m)

        if stats.get("bait_collected_total", 0) >= 20 and "bait_collector" not in earned:
            m = await self._award_achievement(ctx, user, "bait_collector")
            if m:
                messages.append(m)

                # Epic streak: 3 epics in a row
        if stats.get("consecutive_catches", 0) >= 3 and "epic_streak_3" not in earned:
            m = await self._award_achievement(ctx, user, "epic_streak_3")
            if m: messages.append(m)

        # Double Trouble: 5 double‐catch events
        if stats.get("double_events", 0) >= 5 and "double_trouble" not in earned:
            m = await self._award_achievement(ctx, user, "double_trouble")
            if m: messages.append(m)

        # Treasure Collector: 5 chests found
        if stats.get("treasure_found", 0) >= 5 and "treasure_collect" not in earned:
            m = await self._award_achievement(ctx, user, "treasure_collect")
            if m: messages.append(m)

        # Pearl Hoarder: 3 pearls
        if stats.get("pearl_found", 0) >= 3 and "pearl_hoarder" not in earned:
            m = await self._award_achievement(ctx, user, "pearl_hoarder")
            if m: messages.append(m)

        # Map Explorer: 3 maps
        if stats.get("map_found", 0) >= 3 and "map_explorer" not in earned:
            m = await self._award_achievement(ctx, user, "map_explorer")
            if m: messages.append(m)

        # Festival Fan: 3 festival events
        if stats.get("festival_events", 0) >= 3 and "festival_fan" not in earned:
            m = await self._award_achievement(ctx, user, "festival_fan")
            if m: messages.append(m)

        # Salvage Expert: 20 salvage events
        if stats.get("salvage_events", 0) >= 20 and "salvage_expert" not in earned:
            m = await self._award_achievement(ctx, user, "salvage_expert")
            if m: messages.append(m)

        # Sea Legend: caught a boss fish
        if stats.get("boss_catches", 0) >= 1 and "sea_legend" not in earned:
            m = await self._award_achievement(ctx, user, "sea_legend")
            if m: messages.append(m)

        # Abyssal Finder: caught an Abyssal or Mythic
        if stats.get("abyssal_catches", 0) >= 1 and "abyssal_finder" not in earned:
            m = await self._award_achievement(ctx, user, "abyssal_finder")
            if m: messages.append(m)

        # Mythic Hunter: 3 mythic catches
        if stats.get("mythic_catches", 0) >= 3 and "mythic_hunter" not in earned:
            m = await self._award_achievement(ctx, user, "mythic_hunter")
            if m: messages.append(m)

        # Legend Chaser: 5 legendary catches
        if stats.get("legendary_catches", 0) >= 5 and "legend_chaser" not in earned:
            m = await self._award_achievement(ctx, user, "legend_chaser")
            if m: messages.append(m)

        # Collector: 100 unique fish
        if stats.get("unique_fish", 0) >= 100 and "collector_100" not in earned:
            m = await self._award_achievement(ctx, user, "collector_100")
            if m: messages.append(m)

        # Merchant of Mean: sell 500 total
        if stats.get("sell_total", 0) >= 500 and "merchant_of_mean" not in earned:
            m = await self._award_achievement(ctx, user, "merchant_of_mean")
            if m: messages.append(m)

        # Seasoned Angler: cast 1000 times
        if stats.get("casts", 0) >= 1000 and "seasoned_angler" not in earned:
            m = await self._award_achievement(ctx, user, "seasoned_angler")
            if m: messages.append(m)

        # Bait Baron: collect 100 bait
        if stats.get("bait_collected_total", 0) >= 100 and "bait_hoarder_plus" not in earned:
            m = await self._award_achievement(ctx, user, "bait_hoarder_plus")
            if m: messages.append(m)

        # Crafting Ace: craft every recipe (use crafts_done >= len recipes)
        total_recipes = len(self.crafting_recipes)
        if stats.get("crafts_done", 0) >= total_recipes and "crafting_ace" not in earned:
            m = await self._award_achievement(ctx, user, "crafting_ace")
            if m: messages.append(m)
              

        return messages
        …

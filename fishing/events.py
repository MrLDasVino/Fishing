# cogs/fishing/events.py

import random
from .helpers import deposit, choose_random
from .data import fish_definitions

class EventManager:
    def __init__(self, config, fish_names: list, fish_weights: list):
        self.config = config
        self.fish_names   = fish_names
        self.fish_weights = fish_weights

        # build registry
        self.handlers = {
            "nothing":         (self._event_nothing,          35),
            "fish":            (self._event_fish,             28),
            "double":          (self._event_double,            5),
            "shark":           (self._event_shark,       3),
            "break":           (self._event_break,       4),
            "treasure":        (self._event_treasure,    4),
            "bottle":          (self._event_bottle,      4),
            "storm":           (self._event_storm,       2),
            "net":             (self._event_net,         3),
            "bait_find":       (self._event_bait_find,   5),
            "lucky_streak":    (self._event_lucky_streak, 1),
            "curse":           (self._event_curse,       1),
            "merchant":        (self._event_merchant,    2),
            "pearl":           (self._event_pearl,       2),
            "map":             (self._event_map,         1),
            "sea_monster":     (self._event_sea_monster, 1),
            "hook_snag":       (self._event_hook_snag,   3),
            "festival":        (self._event_festival,    1),
            "charity":         (self._event_charity,     1),
            "salvage":         (self._event_salvage,     2),
            "message":         (self._event_message,     2),
            "bubble_burst":    (self._event_bubble_burst,4),
            "kelp_tangle":     (self._event_kelp_tangle, 3),
            "whale_song":      (self._event_whale_song,  1),
            "siren_call":      (self._event_siren_call,  1),
            "tide_pool":       (self._event_tide_pool,   3),
            "meteor_shower":   (self._event_meteor_shower,1),
            "coral_gift":      (self._event_coral_gift,  2),
            "water_sprite":    (self._event_water_sprite,3),
            "whirlpool":       (self._event_whirlpool,   2),
            "fisherman_friend":(self._event_fisherman_friend,2),
            "barnacle_pearl":  (self._event_barnacle_pearl,2),
            "crystal_wash":    (self._event_crystal_wash,1),
            "echo_call":       (self._event_echo_call,   1),
            "drifting_crate":  (self._event_drifting_crate,2),
            "phantom_net":     (self._event_phantom_net, 2),
            "lazy_sun":        (self._event_lazy_sun,    2),
            "thunder_clap":    (self._event_thunder_clap,1),
            "sponge_cache":    (self._event_sponge_cache,3),
            "tide_change":     (self._event_tide_change, 1),
            "moon_phase":      (self._event_moon_phase,  1),
            "rift_glimpse":    (self._event_rift_glimpse,1),
            "luminous_cavern": (self._event_luminous_cavern, 2),
            "prehistoric_trench": (self._event_prehistoric_trench, 2),
            "smoldering_pool":   (self._event_smoldering_pool,  2),
            "lava_spout":        (self._event_lava_spout,       2),
            "phantom_tide":      (self._event_phantom_tide,     2),
            "haunted_whispers":  (self._event_haunted_whispers, 2),
            "dream_reverie":     (self._event_dream_reverie,    2),
            "nightmare_bloom":   (self._event_nightmare_bloom,  2),
            "titan_quake":       (self._event_titan_quake,      2),
            "deepwyrm_raise":    (self._event_deepwyrm_raise,   2),
            "cavern_glow":       (self._event_cavern_glow,      2),
            "ethereal_gust":     (self._event_ethereal_gust,    2),
            "volcanic_spring": (self._event_volcanic_spring,    2),
            "haunted_shoal":   (self._event_haunted_shoal,      2),            
        }
        self.keys    = list(self.handlers)
        self.base_w  = [self.handlers[k][1] for k in self.keys]

    async def pick_and_run(self, ctx, user_conf):
        """
        1) Clone base weights
        2) apply bait / luck / rod modifiers (copy your code)
        3) random.choices → pick a key
        4) call its handler, return its result
        """
        weights = self.base_w.copy()
        # 2) Bait modifier
        bait_amt = await user_conf.bait()
        if bait_amt > 0:
            if random.random() < 0.9:
                await user_conf.bait.set(bait_amt - 1)
            for i, key in enumerate(self.keys):
                if key in ("fish", "double"):
                    weights[i] = int(weights[i] * 1.6)

        # 3) Luck modifier
        luck = await user_conf.luck()
        if luck > 0:
            await user_conf.luck.set(max(0, luck - 1))
            for i, key in enumerate(self.keys):
                if key in ("fish", "double", "treasure", "pearl", "merchant"):
                    weights[i] = int(weights[i] * 2)

        # 4) Rod‐level modifier
        rod_lvl = await user_conf.rod_level()
        fish_mult  = rod_level_fish_multiplier.get(rod_lvl, 1.0)
        break_mult = rod_level_break_reduction.get(rod_lvl, 1.0)
        for i, key in enumerate(self.keys):
            if key in ("fish", "double", "treasure", "pearl", "merchant"):
                weights[i] = int(weights[i] * fish_mult)
            if key in ("break", "hook_snag"):
                weights[i] = max(1, int(weights[i] * break_mult))

        # 5) Ensure no zero‐weight
        weights = [max(1, w) for w in weights]
        choice = random.choices(self.keys, weights=weights, k=1)[0]
        handler = self.handlers[choice][0]
        return await handler(ctx, user_conf)

    # ——— event handlers: copy your original methods below ———

    async def _event_nothing(self, ctx, user_conf):
        stats = await user_conf.stats()
        stats["consecutive_catches"] = 0
        await user_conf.stats.set(stats)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "…No bites this time. Better luck next cast!"
        pass

    async def _event_junk(self, ctx, user_conf):
        junk_items = [
            "an old boot",
            "a tin can",
            "a broken bottle",
            "a soggy hat",
            "a rusty key",
            "a tangle of seaweed",
            "a fish skeleton",
        ]
        item = random.choice(junk_items)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, f"👎 You pulled up {item}. Better luck next time!"
        pass

    async def _event_fish(self, ctx, user_conf):
        catch = choose_random(self.fish_names, self.fish_weights)
        data = await user_conf.caught()
        data.append(catch)
        await user_conf.caught.set(data)

        info = fish_definitions[catch]
        rarity = info["rarity"]
        if rarity == "Boss":
            await self._inc_stat(ctx.author, "boss_catches", 1)
        if rarity in ("Abyssal", "Mythic"):
            await self._inc_stat(ctx.author, "abyssal_catches", 1)
        if rarity == "Mythic":
            await self._inc_stat(ctx.author, "mythic_catches", 1)
        if rarity == "Legendary":
            await self._inc_stat(ctx.author, "legendary_catches", 1)

        await self._maybe_update_unique_and_highest(ctx.author, catch)
        await self._inc_stat(ctx.author, "casts", 1)
        await self._advance_quest_on_catch(ctx.author, catch)

        return False, f"{info['emoji']} You caught a **{catch}** ({rarity})!"
        pass

    async def _event_double(self, ctx, user_conf):
        catch1 = self._random_fish()
        catch2 = self._random_fish()
        data = await user_conf.caught()
        data.extend([catch1, catch2])
        await user_conf.caught.set(data)
        await self._maybe_update_unique_and_highest(ctx.author, catch1)
        await self._maybe_update_unique_and_highest(ctx.author, catch2)
        await self._inc_stat(ctx.author, "casts", 1)
        await self._inc_stat(ctx.author, "double_events", 1)
        await self._advance_quest_on_catch(ctx.author, catch1)
        await self._advance_quest_on_catch(ctx.author, catch2)
        msg_ach = None
        if not await self._has_achievement(ctx.author, "double_catch"):
            msg_ach = await self._award_achievement(ctx, ctx.author, "double_catch")
        info1 = self.fish_definitions[catch1]
        info2 = self.fish_definitions[catch2]
        base = f"{info1['emoji']}{info2['emoji']} Double catch! You got **{catch1}** and **{catch2}**!"
        other_msgs = await self._check_and_award(ctx, ctx.author)
        parts = [base]
        if msg_ach:
            parts.append(msg_ach)
        if other_msgs:
            parts.extend(other_msgs)
        return False, "\n\n".join(parts)

    async def _event_shark(self, ctx, user_conf):
        data = await user_conf.caught()
        if data:
            lost = data.pop()
            await user_conf.caught.set(data)
            await self._inc_stat(ctx.author, "casts", 1)
            stats = await user_conf.stats()
            stats["consecutive_catches"] = 0
            await user_conf.stats.set(stats)
            return False, f"🦈 A shark snatches your **{lost}**! Ouch."
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "🦈 A shark swims by, but you had nothing yet to lose."

    async def _event_break(self, ctx, user_conf):
        await user_conf.rod_broken.set(True)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "Snap! Your rod just broke. You’ll need to repair it."

    async def _event_treasure(self, ctx, user_conf):
        coins = random.randint(10, 60)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        await self._inc_stat(ctx.author, "casts", 1)
        await self._inc_stat(ctx.author, "treasure_found", 1)
        # small chance for rod fragment
        if random.random() < 0.06:
            items = await user_conf.items()
            items.append("Rod Fragment")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "fragment_collector"):
                items_now = await user_conf.items()
                if items_now.count("Rod Fragment") >= 10:
                    await self._award_achievement(ctx, ctx.author, "fragment_collector")
        except Exception:
            pass
            fragmsg = " You also find a **Rod Fragment** among the loot!"
        else:
            fragmsg = ""
        msg_ach = None
        if not await self._has_achievement(ctx.author, "treasure_hunter"):
            msg_ach = await self._award_achievement(ctx, ctx.author, "treasure_hunter")
        base = f"🎁 You hauled up a treasure chest and got **{coins} {currency}**! Your new balance is **{new_bal} {currency}**.{fragmsg}"
        if msg_ach:
            return False, base + "\n\n" + msg_ach
        return False, base

    async def _event_bottle(self, ctx, user_conf):
        coins = random.randint(5, 30)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, f"📜 You found a message in a bottle and earned **{coins} {currency}**! Your new balance is **{new_bal} {currency}**."

    async def _event_storm(self, ctx, user_conf):
        if random.random() < 0.2:
            await user_conf.rod_broken.set(True)
            await self._inc_stat(ctx.author, "casts", 1)
            return False, "⛈️ A sudden storm! Your line snaps back and your rod breaks."
        await self._inc_stat(ctx.author, "casts", 1)
        # 10% chance to salvage a Storm Scale from the storm
        scale_msg = ""
        if random.random() < 0.10:
            items = await user_conf.items()
            items.append("Storm Scale")
            await user_conf.items.set(items)
            scale_msg = " Amid the thunder you retrieve a **Storm Scale**!"

        return False, f"⛈️ A sudden storm! Your line snaps back with nothing to show.{scale_msg}"

    async def _event_net(self, ctx, user_conf):
        net_fish_count = random.randint(1, 5)
        caught = [self._random_fish() for _ in range(net_fish_count)]
        data = await user_conf.caught()
        data.extend(caught)
        await user_conf.caught.set(data)
        await self._inc_stat(ctx.author, "casts", 1)
        await self._inc_stat(ctx.author, "net_events", 1)
        if net_fish_count >= 5 and not await self._has_achievement(ctx.author, "net_haul"):
            net_msg = await self._award_achievement(ctx, ctx.author, "net_haul")
            if net_msg:
                base = f"🕸️ You snagged an old net with {net_fish_count} things tangled inside: {', '.join(caught)}."
                return False, f"{base}\n\n{net_msg}"
        if random.random() < 0.08:
            items = await user_conf.items()
            items.append("Rod Fragment")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "fragment_collector"):
                items_now = await user_conf.items()
                if items_now.count("Rod Fragment") >= 10:
                    await self._award_achievement(ctx, ctx.author, "fragment_collector")
        except Exception:
            pass            
            found = " You also find a **Rod Fragment** tangled in the net."
        else:
            found = ""
        names = ", ".join(caught)
        for f in caught:
            await self._advance_quest_on_catch(ctx.author, f)
        return False, f"🕸️ You snagged an old net with {net_fish_count} things tangled inside: {names}.{found}"

    async def _event_bait_find(self, ctx, user_conf):
        bait_found = random.randint(1, 5)
        current_bait = await user_conf.bait()
        await user_conf.bait.set(current_bait + bait_found)
        await self._inc_stat(ctx.author, "casts", 1)
        stats = await user_conf.stats()
        stats["bait_collected_total"] = stats.get("bait_collected_total", 0) + bait_found
        await user_conf.stats.set(stats)
        msgs = []
        if stats["bait_collected_total"] >= 20 and not await self._has_achievement(ctx.author, "bait_collector"):
            m = await self._award_achievement(ctx, ctx.author, "bait_collector")
            if m:
                msgs.append(m)
        base = f"🪱 You found **{bait_found}** bait in the mud. You now have **{current_bait + bait_found}** bait."
        if msgs:
            return False, base + "\n\n" + "\n".join(msgs)
        return False, base

    async def _event_lucky_streak(self, ctx, user_conf):
        await user_conf.luck.set(5)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "✨ Lucky streak! Your next few casts are more likely to find rare fish."

    async def _event_curse(self, ctx, user_conf):
        if random.random() < 0.5:
            loss = random.randint(5, 25)
            bal = await bank.get_balance(ctx.author)
            if bal >= loss:
                await bank.withdraw_credits(ctx.author, loss)
                currency = await bank.get_currency_name(ctx.guild)
                await self._inc_stat(ctx.author, "casts", 1)
                return False, f"🔮 An old charm curses you — you lost **{loss} {currency}**."
        await user_conf.rod_broken.set(True)
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "🔮 A cursed tug! Your rod is damaged by some dark force."

    async def _event_merchant(self, ctx, user_conf):
        inventory = await user_conf.caught()
        await self._inc_stat(ctx.author, "casts", 1)
        if not inventory:
            tips = random.randint(1, 10)
            new_bal, currency = await self._deposit(ctx.author, tips, ctx)
            return False, f"🧑‍🚀 A traveling merchant stops by and leaves **{tips} {currency}** as thanks."
        fish = random.choice(inventory)
        premium = int(self.fish_prices.get(fish, 10) * random.uniform(1.2, 2.0))
        inventory.remove(fish)
        await user_conf.caught.set(inventory)
        new_bal, currency = await self._deposit(ctx.author, premium, ctx)
        return False, f"🧑‍🚀 A merchant offers **{premium} {currency}** for your **{fish}** and buys it on the spot. New balance: **{new_bal} {currency}**."

    async def _event_pearl(self, ctx, user_conf):
        value = random.randint(50, 150)
        new_bal, currency = await self._deposit(ctx.author, value, ctx)
        await self._inc_stat(ctx.author, "casts", 1)
        await self._inc_stat(ctx.author, "pearl_found", 1)
        
        # give the player a Pearl item
        items = await user_conf.items()
        items.append("Pearl")
        await user_conf.items.set(items)
        
        msg_ach = None
        if not await self._has_achievement(ctx.author, "pearl_finder"):
            msg_ach = await self._award_achievement(ctx, ctx.author, "pearl_finder")
        
        base = (
            f"💎 You found a lustrous pearl worth **{value} {currency}**, "
            f"and received a **Pearl** item. Your new balance is **{new_bal} {currency}**."
        )
        if msg_ach:
            return False, base + "\n\n" + msg_ach
        return False, base

    async def _event_map(self, ctx, user_conf):
        items = await user_conf.items()
        items.append("Treasure Map")
        await user_conf.items.set(items)
        await self._inc_stat(ctx.author, "casts", 1)
        await self._inc_stat(ctx.author, "map_found", 1)
        if not await self._has_achievement(ctx.author, "map_collector"):
            msg = await self._award_achievement(ctx, ctx.author, "map_collector")
            if msg:
                return False, "🗺️ You found a Treasure Map! Use it later to start a treasure hunt.\n\n" + msg
        return False, "🗺️ You found a Treasure Map! Use it later to start a treasure hunt."

    async def _event_sea_monster(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.5:
            data = await user_conf.caught()
            lost = []
            for _ in range(min(3, len(data))):
                lost.append(data.pop(random.randrange(len(data))))
            await user_conf.caught.set(data)
            return False, f"🪸 A sea monster thrashes by and steals: {', '.join(lost)}! Escape barely."
        else:
            rare = self._random_fish()
            data = await user_conf.caught()
            data.append(rare)
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, rare)
            if not await self._has_achievement(ctx.author, "sea_monster_survivor"):
                msg = await self._award_achievement(ctx, ctx.author, "sea_monster_survivor")
                if msg:
                    return False, f"🪸 You managed to hook a **{rare}** from the sea monster's grip!\n\n{msg}"
            return False, f"🪸 You managed to hook a **{rare}** from the sea monster's grip!"

    async def _event_hook_snag(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.6:
            await user_conf.rod_broken.set(True)
            return False, "⛓️ Your hook snagged on something sharp and your rod snapped!"
        return False, "⛓️ Your hook snagged on an old anchor but you freed it."

    async def _event_festival(self, ctx, user_conf):
        await user_conf.luck.set(3)
        await self._inc_stat(ctx.author, "casts", 1)
        await self._inc_stat(ctx.author, "festival_events", 1)
        return False, "🎉 Festival of Fishermen! Sold fish pay more for a short while."

    async def _event_charity(self, ctx, user_conf):
        bal = await bank.get_balance(ctx.author)
        donation = min(random.randint(1, 10), bal)
        if donation > 0:
            await bank.withdraw_credits(ctx.author, donation)
            currency = await bank.get_currency_name(ctx.guild)
            await self._inc_stat(ctx.author, "casts", 1)
            return False, f"🤝 You gave **{donation} {currency}** to a community cause."
        await self._inc_stat(ctx.author, "casts", 1)
        return False, "🤝 You feel generous but have no funds to donate."

    async def _event_salvage(self, ctx, user_conf):
        coins = random.randint(5, 40)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        await self._inc_stat(ctx.author, "casts", 1)
        await self._inc_stat(ctx.author, "salvage_events", 1)
        r = random.random()
        if r < 0.03:
            items = await user_conf.items()
            items.append("Rod Core")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "core_seeker"):
                await self._award_achievement(ctx, ctx.author, "core_seeker")
        except Exception:
            pass            
            return False, f"🛠️ You salvage rare parts, get **{coins} {currency}** and a **Rod Core**!"
        if r < 0.10:
            items = await user_conf.items()
            items.append("Rod Fragment")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "fragment_collector"):
                items_now = await user_conf.items()
                if items_now.count("Rod Fragment") >= 10:
                    await self._award_achievement(ctx, ctx.author, "fragment_collector")
        except Exception:
            pass            
            return False, f"🛠️ You salvage pieces, get **{coins} {currency}** and a **Rod Fragment**!"
        if random.random() < 0.15:
            items = await user_conf.items()
            items.append("Treasure Map")
            await user_conf.items.set(items)
            await self._inc_stat(ctx.author, "map_found", 1)
            return False, f"🛠️ You salvage usable pieces and find **{coins} {currency}** and a **Treasure Map**!"
        return False, f"🛠️ You salvage metal and get **{coins} {currency}**."

    async def _event_message(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.5:
            bait = random.randint(1, 3)
            current = await user_conf.bait()
            await user_conf.bait.set(current + bait)
            return False, f"✉️ A friendly note contains **{bait}** bait. You now have **{current + bait}** bait."
        else:
            coins = random.randint(5, 20)
            new_bal, currency = await self._deposit(ctx.author, coins, ctx)
            return False, f"✉️ You find **{coins} {currency}** tucked in a note. New balance: **{new_bal} {currency}**."
            
    async def _event_bubble_burst(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.25:
            # small fish
            catch = self._random_fish()
            data = await user_conf.caught()
            data.append(catch)
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, catch)
            return False, f" bubbles! You spot a small fish and catch a **{catch}**!"
        else:
            bait = random.randint(1, 2)
            current = await user_conf.bait()
            await user_conf.bait.set(current + bait)
            return False, f" Bubbles reveal some bait. You found **{bait}** bait."

    async def _event_kelp_tangle(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.15:
            data = await user_conf.caught()
            data.append("Seagrass Fish")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Seagrass Fish")
            return False, "🪴 Your line tangles in kelp but you free a **Seagrass Fish**!"
        return False, "🪴 Your line gets tangled in kelp — nothing worth keeping this time."

    async def _event_whale_song(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        await user_conf.luck.set((await user_conf.luck()) + 3)
        return False, "🐋 A whale sings — your luck rises for a few casts."

    async def _event_siren_call(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        r = random.random()
        if r < 0.12:
            # mythic reward
            catch = self._random_fish()
            data = await user_conf.caught()
            data.append(catch)
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, catch)
            return False, f"🧜 A siren lures something incredible — you catch a **{catch}**!"
        if r < 0.35:
            # lose an item
            items = await user_conf.items()
            if items:
                lost = items.pop(random.randrange(len(items)))
                await user_conf.items.set(items)
                return False, f"🧜 A siren's song steals **{lost}** from you!"
        return False, "🧜 A haunting song passes by. You steady the line and move on."

    async def _event_tide_pool(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        count = random.randint(2, 5)
        caught = [self._random_fish() for _ in range(count)]
        data = await user_conf.caught()
        data.extend(caught)
        await user_conf.caught.set(data)
        for c in caught:
            await self._maybe_update_unique_and_highest(ctx.author, c)
        return False, f"🌊 You explore a tide pool and net {len(caught)} fish: {', '.join(caught)}."

    async def _event_meteor_shower(self, ctx, user_conf):
      await self._inc_stat(ctx.author, "cosmic_events", 1)

      # try awarding the achievement and capture its message
      ach_msg = None
      if not await self._has_achievement(ctx.author, "cosmic_watcher"):
          ach_msg = await self._award_achievement(ctx, ctx.author, "cosmic_watcher")

      if random.random() < 0.10:
          # celestial fish
          catch = "Star Pike"
          data = await user_conf.caught()
          data.append(catch)
          await user_conf.caught.set(data)
          await self._maybe_update_unique_and_highest(ctx.author, catch)
          base = "☄️ Meteor light guides you to a **Star Pike**!"
      else:
          coins = random.randint(10, 50)
          new_bal, currency = await self._deposit(ctx.author, coins, ctx)
          base = f"☄️ Falling sparks wash ashore coins — you get **{coins} {currency}**."

      # append achievement announcement if any
      if ach_msg:
          return False, f"{base}\n\n{ach_msg}"
      return False, base

    async def _event_coral_gift(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.25:
            items = await user_conf.items()
            items.append("Coral Trinket")
            await user_conf.items.set(items)
            return False, "🪸 The coral cradles a **Coral Trinket** and gives it to you."
        coins = random.randint(5, 25)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        return False, f"🪸 Tiny coral pieces yield **{coins} {currency}**."

    async def _event_water_sprite(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.5:
            bait = random.randint(1, 3)
            current = await user_conf.bait()
            await user_conf.bait.set(current + bait)
            return False, f"🧚 A water sprite blesses you with **{bait}** bait."
        await user_conf.luck.set((await user_conf.luck()) + 1)
        return False, "🧚 A sprite whispers. Your luck increases slightly."

    async def _event_whirlpool(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        data = await user_conf.caught()
        if data:
            lost = []
            lost_count = min(random.randint(1, 3), len(data))
            for _ in range(lost_count):
                lost.append(data.pop(random.randrange(len(data))))
            await user_conf.caught.set(data)
            return False, f"🌀 A whirlpool swallows {', '.join(lost)} from your haul!"
        return False, "🌀 A whirlpool churns but you had nothing to lose."

    async def _event_fisherman_friend(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        inv = await user_conf.caught()
        if not inv:
            coins = random.randint(1, 8)
            new_bal, currency = await self._deposit(ctx.author, coins, ctx)
            return False, f"🧑‍⚖️ A helpful fisherman tips you **{coins} {currency}**."
        fish = random.choice(inv)
        premium = int(self.fish_prices.get(fish, 10) * random.uniform(1.4, 2.5))
        inv.remove(fish)
        await user_conf.caught.set(inv)
        new_bal, currency = await self._deposit(ctx.author, premium, ctx)
        return False, f"🧑‍⚖️ A friendly fisherman buys your **{fish}** for **{premium} {currency}** on the spot."

    async def _event_barnacle_pearl(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.12:
            value = random.randint(30, 120)
            new_bal, currency = await self._deposit(ctx.author, value, ctx)
            return False, f"🐚 You pry open a barnacle and find a pearl worth **{value} {currency}**!"
        return False, "🐚 Barnacles cling to nothing of value this time."

    async def _event_crystal_wash(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.10:
            data = await user_conf.caught()
            data.append("Crystal Trout")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Crystal Trout")
            return False, "🔹 A crystal wash frees a **Crystal Trout** into your net!"
        return False, "🔹 Shimmering water passes but nothing uncommon shows."

    async def _event_echo_call(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.5:
            await user_conf.luck.set((await user_conf.luck()) + 2)
            return False, "🔔 Echoes call — your next casts are luckier."
        return False, "🔔 You hear distant echoes; nothing else."

    async def _event_drifting_crate(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        coins = random.randint(5, 40)
        new_bal, currency = await self._deposit(ctx.author, coins, ctx)
        items = await user_conf.items()
        if random.random() < 0.10:
            items.append("Rod Fragment")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "fragment_collector"):
                items_now = await user_conf.items()
                if items_now.count("Rod Fragment") >= 10:
                    await self._award_achievement(ctx, ctx.author, "fragment_collector")
        except Exception:
            pass            
            return False, f"📦 You pull a drifting crate with **{coins} {currency}** and a **Rod Fragment**!"
        return False, f"📦 You open a drifting crate and find **{coins} {currency}**."

    async def _event_phantom_net(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        await self._inc_stat(ctx.author, "spectral_events", 1)
        if random.random() < 0.08:
            data = await user_conf.caught()
            data.append("Spectral Herring")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Spectral Herring")
            spec_msg = None
            if not await self._has_achievement(ctx.author, "spectral_hunter"):
                spec_msg = await self._award_achievement(ctx, ctx.author, "spectral_hunter")
            text = "👻 A ghostly net yields a **Spectral Herring**!"
            return False, f"{text}\n\n{spec_msg}" if spec_msg else text
        return False, "👻 An old phantom net drops off a tangle of junk."

    async def _event_lazy_sun(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        await user_conf.luck.set((await user_conf.luck()) + 1)
        return False, "☀️ The sun is calm — common and uncommon fish are more likely."

    async def _event_thunder_clap(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        # reduce luck briefly but maybe rare storm fish
        # 8% chance to hook the rare Stormwing Tuna
        if random.random() < 0.08:
            data = await user_conf.caught()
            data.append("Stormwing Tuna")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Stormwing Tuna")

            # 10% chance to salvage a Storm Scale alongside it
            scale_msg = ""
            if random.random() < 0.10:
                items = await user_conf.items()
                items.append("Storm Scale")
                await user_conf.items.set(items)
                scale_msg = " You also salvage a **Storm Scale**!"

            return False, f"⚡ A thunderclap unleashes a **Stormwing Tuna**!{scale_msg}"

        # small luck penalty on a normal clap
        await user_conf.luck.set(max(0, (await user_conf.luck()) - 1))

        # still a 10% chance to get a Storm Scale even if no tuna
        scale_msg = ""
        if random.random() < 0.10:
            items = await user_conf.items()
            items.append("Storm Scale")
            await user_conf.items.set(items)
            scale_msg = " You salvage a small **Storm Scale** from the thunder."

        return False, f"⚡ A thunderclap startles the water; luck reduced slightly.{scale_msg}"

    async def _event_sponge_cache(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        bait_found = random.randint(1, 3)
        current = await user_conf.bait()
        await user_conf.bait.set(current + bait_found)
        if random.random() < 0.06:
            items = await user_conf.items()
            items.append("Rod Fragment")
            await user_conf.items.set(items)
        try:
            if not await self._has_achievement(ctx.author, "fragment_collector"):
                items_now = await user_conf.items()
                if items_now.count("Rod Fragment") >= 10:
                    await self._award_achievement(ctx, ctx.author, "fragment_collector")
        except Exception:
            pass            
            return False, f"🧽 A sponge cache yields **{bait_found}** bait and a **Rod Fragment**!"
        return False, f"🧽 A sponge cache yields **{bait_found}** bait."

    async def _event_tide_change(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        # temporarily give player a small luck boost and message; actual biome weighting handled elsewhere if implemented
        await user_conf.luck.set((await user_conf.luck()) + 1)
        return False, "🌊 The tide changes — coastal/reef spawns feel stronger for a short time."

    async def _event_moon_phase(self, ctx, user_conf):
      await self._inc_stat(ctx.author, "cosmic_events", 1)

      # try awarding the achievement and capture its message
      ach_msg = None
      if not await self._has_achievement(ctx.author, "cosmic_watcher"):
          ach_msg = await self._award_achievement(ctx, ctx.author, "cosmic_watcher")

      if random.random() < 0.05:
          catch = "Silver Seraph"
          data = await user_conf.caught()
          data.append(catch)
          await user_conf.caught.set(data)
          await self._maybe_update_unique_and_highest(ctx.author, catch)
          base = "🌕 Under the moon's eye you catch a **Silver Seraph**!"
      else:
          base = "🌕 The moon glances off the water — a quiet, promising night."

      # append achievement announcement if any
      if ach_msg:
          return False, f"{base}\n\n{ach_msg}"
      return False, base

    async def _event_rift_glimpse(self, ctx, user_conf):
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.03:
            data = await user_conf.caught()
            data.append("Abyssal Wisp")
            await user_conf.caught.set(data)
            await self._maybe_update_unique_and_highest(ctx.author, "Abyssal Wisp")
            return False, "🔱 A rift glimpse draws forth an **Abyssal Wisp**!"
        return False, "🔱 You glimpse a rift far below; nothing pulled up this time."
        
    async def _event_luminous_cavern(self, ctx, user_conf):
        """
        Bioluminal Sea vibes: catch a Glimmer Eel or find extra bait.
        """
        # count this cast
        await self._inc_stat(ctx.author, "casts", 1)

        r = random.random()
        if r < 0.25:
            # find bait in the glowing water
            bait = random.randint(1, 3)
            cur = await user_conf.bait()
            await user_conf.bait.set(cur + bait)
            return False, f"🌌 Luminous Cavern sparkles — you gather **{bait}** bait."

        # otherwise hook a Glimmer Eel
        catch = "Glimmer Eel"
        data = await user_conf.caught()
        data.append(catch)
        await user_conf.caught.set(data)

        info = fish_definitions[catch]
        await self._maybe_update_unique_and_highest(ctx.author, catch)
        await self._advance_quest_on_catch(ctx.author, catch)
        return False, f"{info['emoji']} You net a **{catch}** from the glowing depths!"

    async def _event_prehistoric_trench(self, ctx, user_conf):
        """
        Ancient waters: chance for a Coelacanth, Trilobite, or a brush with a Megalodon.
        """
        await self._inc_stat(ctx.author, "casts", 1)

        r = random.random()
        if r < 0.10:
            # Megalodon encounter—rod might break
            await user_conf.rod_broken.set(True)
            return False, "🦈 A colossal silhouette thrashes—your rod shatters as you escape!"

        if r < 0.35:
            # rare Coelacanth catch
            catch = "Coelacanth"
        else:
            # common Trilobite
            catch = "Trilobite"

        data = await user_conf.caught()
        data.append(catch)
        await user_conf.caught.set(data)

        info = fish_definitions[catch]
        await self._maybe_update_unique_and_highest(ctx.author, catch)
        await self._advance_quest_on_catch(ctx.author, catch)
        return False, f"{info['emoji']} In the trench you haul up a **{catch}**!"

    async def _event_smoldering_pool(self, ctx, user_conf):
        """Volcanic Spring: yielding Fire Goby or Magma Eel."""
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.20:
            choice = "Magma Eel"
        else:
            choice = "Fire Goby"
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)
        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)
        return False, f"{info['emoji']} Scorching currents yield a **{choice}** ({info['rarity']})!"

    async def _event_lava_spout(self, ctx, user_conf):
        """Volcanic Spring burst: Ember Carp blast."""
        await self._inc_stat(ctx.author, "casts", 1)
        # Always Ember Carp
        choice = "Ember Carp"
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)
        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)
        return False, f"{info['emoji']} A sudden lava spout spews a **{choice}**!"

    async def _event_phantom_tide(self, ctx, user_conf):
        """Haunted Shoals tide: Wraith Herring or Bonefish."""
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.30:
            choice = "Wraith Herring"
        else:
            choice = "Bonefish"
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)
        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)
        return False, f"{info['emoji']} Ghostly tide brings in a **{choice}** ({info['rarity']})!"

    async def _event_haunted_whispers(self, ctx, user_conf):
        """Haunted Shoals whispers: steal or grant Phantom Carp."""
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.25:
            inv = await user_conf.items()
            if inv:
                lost = inv.pop(random.randrange(len(inv)))
                await user_conf.items.set(inv)
                return False, f"👻 Haunting whispers steal your **{lost}**!"
        # Otherwise give a Phantom Carp
        choice = "Phantom Carp"
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)
        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)
        return False, f"{info['emoji']} You hook a **{choice}** from the darkness!"

    async def _event_dream_reverie(self, ctx, user_conf):
        """Dreaming Deep: chance for Dream Pike or Sleepfin."""
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.30:
            choice = "Dream Pike"
        else:
            choice = "Sleepfin"
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)
        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)
        return False, f"{info['emoji']} In a dream current you net a **{choice}**!"

    async def _event_nightmare_bloom(self, ctx, user_conf):
        """Dreaming Deep bloom: Nightmare Grouper lurks."""
        await self._inc_stat(ctx.author, "casts", 1)
        choice = "Nightmare Grouper"
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)
        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)
        return False, f"{info['emoji']} A nightmare bloom surfaces a **{choice}**!"

    async def _event_titan_quake(self, ctx, user_conf):
        """Titan's Trench tremor: Titan Crab or Pressure Pike."""
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.30:
            choice = "Titan Crab"
        else:
            choice = "Pressure Pike"
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)
        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)
        return False, f"{info['emoji']} A trench quake yields a **{choice}**!"

    async def _event_deepwyrm_raise(self, ctx, user_conf):
        """Titan's Trench abyss: Leviathan Cod or Deepwyrm."""
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.25:
            choice = "Leviathan Cod"
        else:
            choice = "Deepwyrm"
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)
        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)
        return False, f"{info['emoji']} From the depths a **{choice}** emerges!"

    async def _event_cavern_glow(self, ctx, user_conf):
        """Bioluminal Cavern glow: Neon Sprat or Glowfin Trout."""
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.40:
            choice = "Neon Sprat"
        else:
            choice = "Glowfin Trout"
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)
        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)
        return False, f"{info['emoji']} Cavern lights guide you to a **{choice}**!"

    async def _event_ethereal_gust(self, ctx, user_conf):
        """Ethereal Lagoon breeze: Moonshadow Koi or Celestial Salmon."""
        await self._inc_stat(ctx.author, "casts", 1)
        if random.random() < 0.30:
            choice = "Moonshadow Koi"
        else:
            choice = "Celestial Salmon"
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)
        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)
        return False, f"{info['emoji']} A gentle lagoon breeze lands a **{choice}**!"
        
    async def _event_volcanic_spring(self, ctx, user_conf):
        """
        Volcanic Spring:
        – 20% chance to uncover a Lava Pearl item
        – otherwise catch a volcanic fish (Cinderfish or Magma Carp)
        """
        # count the cast
        await self._inc_stat(ctx.author, "casts", 1)

        if random.random() < 0.20:
            # grant the Lava Pearl item
            items = await user_conf.items()
            items.append("Lava Pearl")
            await user_conf.items.set(items)

            # track as treasure event if you like
            await self._inc_stat(ctx.author, "treasure_found", 1)

            return False, (
                "🌋 You brave the molten depths and unearth a **Lava Pearl**! "
                "Use it or deliver it for special rewards."
            )

        # else hook one of the volcanic fish
        choice = random.choice(["Cinderfish", "Magma Carp"])
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)

        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)

        return False, f"{info['emoji']} You caught a **{choice}** ({info['rarity']}) in the lava spring!"

    async def _event_haunted_shoal(self, ctx, user_conf):
        """
        Haunted Shoals:
        – 15% chance to receive a Phantom Pearl item
        – else catch a ghostly fish (Spectral Herring or Ghost Carp)
        """
        await self._inc_stat(ctx.author, "casts", 1)

        if random.random() < 0.15:
            # grant the Phantom Pearl item
            items = await user_conf.items()
            items.append("Phantom Pearl")
            await user_conf.items.set(items)

            # track as a pearl event
            await self._inc_stat(ctx.author, "pearl_found", 1)

            return False, (
                "🌑 A skeletal tide washes in a **Phantom Pearl**! "
                "Keep it safe or turn it in to Grimma."
            )

        # else hook a ghost fish
        choice = random.choice(["Spectral Herring", "Ghost Carp"])
        data = await user_conf.caught()
        data.append(choice)
        await user_conf.caught.set(data)

        info = fish_definitions[choice]
        await self._maybe_update_unique_and_highest(ctx.author, choice)
        await self._advance_quest_on_catch(ctx.author, choice)

        return False, f"{info['emoji']} A shadowy form coalesces—you hook a **{choice}**!"
        
        
        

# cogs/fishing/quests.py

import asyncio
from redbot.core import commands
from .data import npcs as NPC_DEFS, quests as QUEST_DEFS
from .helpers import deposit, paginate

class Quests(commands.Cog):
    def __init__(self, config):
        self.config = config
        self.npcs   = NPC_DEFS
        self.quests = QUEST_DEFS

    @commands.command()
    async def npcs(self, ctx):
        """List known NPCs in the world (paged embed)."""
        await ctx.send(f"DEBUG: loaded NPC keys → {', '.join(self.npcs.keys())}")        
        entries = list(self.npcs.items())   # was using some other source
        embeds = []
        per_page = 6

        for i in range(0, len(entries), per_page):
            chunk = entries[i : i + per_page]
            emb = discord.Embed(title="Known NPCs", colour=discord.Colour.green())
            emb.set_image(url="https://files.catbox.moe/jgohga.png")
            for key, info in chunk:
                emb.add_field(
                    name=info["display"],
                    value=(
                        f"{info['greeting']}\n"
                        f"Quests: {', '.join(info['quests']) or 'None'}\n"
                        f"Command: `!talknpc {key}`"
                    ),
                    inline=False,
                )
            emb.set_footer(
                text=f"NPCs {i//per_page+1}/{(len(entries)-1)//per_page+1}"
            )
            embeds.append(emb)

        await paginate(ctx, embeds)

    @commands.command()
    async def talknpc(self, ctx, npc_key: str):
        npc = self.npcs.get(npc_key.lower())
        if not npc:
            return await ctx.send("❌ Unknown NPC. Use `npcs` to see available NPCs.")

        user_conf = self.config.user(ctx.author)
        user_qstate = await user_conf.quests()
        user_completed = user_qstate.get("completed", []) if isinstance(user_qstate, dict) else []

        emb = discord.Embed(title=npc.get("display", npc_key), colour=discord.Colour.teal())
        greeting = npc.get("greeting", "")
        if greeting:
            emb.description = greeting

        img = npc.get("image")
        if isinstance(img, str) and img.startswith("http"):
            try:
                emb.set_thumbnail(url=img)
            except Exception:
                pass

        # List quests available (filter out non-repeatable completed ones)
        quest_list = []
        for qid in npc.get("quests", []):
            qdef = self.quests.get(qid)
            if not qdef:
                continue
            if not qdef.get("repeatable", False) and qid in user_completed:
                # mark as completed and unavailable
                quest_list.append((qdef.get("title", qid) + " (completed)", qid, False))
            else:
                quest_list.append((qdef.get("title", qid), qid, True))

        if quest_list:
            for title, qid, available in quest_list:
                status = "Available" if available else "Unavailable"
                emb.add_field(name=title, value=f"ID: `{qid}` — {status}\nUse `{ctx.clean_prefix}acceptquest {qid}` to accept", inline=False)
        else:
            emb.add_field(name="Quests", value="No quests available right now.", inline=False)

        # Footer with quick usage hint
        emb.set_footer(text=f"Use {ctx.clean_prefix}acceptquest <id> to accept. Use {ctx.clean_prefix}npcs to list NPCs.")

        await ctx.send(embed=emb)
        pass

    @commands.command()
    async def acceptquest(self, ctx, quest_id: str):
        """
        Preview then accept a quest by ID with an embed banner + NPC thumbnail.
        React ✅ to accept or ❌ to cancel.
        """
        # lookup
        qdef = self.quests.get(quest_id)
        if not qdef:
            return await ctx.send(
                f"❌ Unknown quest ID `{quest_id}`. Use `talknpc <npc>` to see available quests."
            )

        # figure out who offers this quest by reverse‐looking up in self.npcs
        npc_img = None
        for key, info in self.npcs.items():
            if quest_id in info.get("quests", []):
                npc_img = info.get("image")
                break

        # build preview embed
        emb = discord.Embed(
            title=f"🗺️ Quest Preview: {qdef['title']}",
            description="React ✅ to accept or ❌ to cancel.",
            colour=discord.Colour.dark_blue(),
        )

        # banner image at bottom
        emb.set_image(url="https://files.catbox.moe/8eh42q.png")

        # NPC avatar as thumbnail
        if npc_img:
            emb.set_thumbnail(url=npc_img)

        # list each step
        for idx, step in enumerate(qdef["steps"], start=1):
            stype = step["type"]
            if stype == "collect_fish":
                req = (f"{step['count']}× {step['name']}"
                       if "name" in step
                       else f"{step['count']}× {step['rarity']} fish")
            elif stype == "deliver_item":
                req = f"{step['count']}× {step['item']}"
            elif stype == "sell_value":
                req = f"Sell {step['amount']} coins worth"
            elif stype == "visit_npc":
                display = self.npcs.get(step["npc"], {}).get("display", step["npc"])
                req = f"Visit {display}"
            else:
                req = step.get("desc", stype)
            emb.add_field(
                name=f"Step {idx}: {req}",
                value=step.get("desc", ""),
                inline=False,
            )

        # rewards summary
        rew = qdef.get("rewards", {})
        parts = []
        if "coins" in rew:
            parts.append(f"{rew['coins']} coins")
        if "items" in rew:
            parts += [f"{cnt}× {name}" for name, cnt in rew["items"].items()]
        if parts:
            emb.add_field(name="Rewards", value=", ".join(parts), inline=False)

        emb.set_footer(text=f"Repeatable: {'Yes' if qdef.get('repeatable') else 'No'}")

        # send & react
        preview = await ctx.send(embed=emb)
        for emoji in ("✅", "❌"):
            await preview.add_reaction(emoji)

        def check(r, u):
            return (
                u == ctx.author
                and r.message.id == preview.id
                and str(r.emoji) in ("✅", "❌")
            )

        try:
            reaction, user = await ctx.bot.wait_for("reaction_add", timeout=60, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("⌛ Quest acceptance timed out.")

        if str(reaction.emoji) == "✅":
            # accept logic
            user_conf = self.config.user(ctx.author)
            qstate    = await user_conf.quests()
            if qstate.get("active"):
                return await ctx.send("❌ Finish or abandon your current quest first.")
            prev = qstate.get("completed", [])
            await user_conf.quests.set({
                "active":    quest_id,
                "step":      0,
                "progress":  {},
                "completed": prev,
            })
            await ctx.send(f"✅ Quest accepted: **{qdef['title']}**. Use `quest` to track progress.")
        else:
            await ctx.send("❌ Quest acceptance cancelled.")
        pass

    @commands.command()
    async def quest(self, ctx):
        """Show your current quest and progress (embed + static image)."""
        user_conf = self.config.user(ctx.author)
        qstate    = await user_conf.quests()
        active    = qstate.get("active")
        if not active:
            return await ctx.send(
                "You have no active quest. Use `talknpc <npc>` to find quests or "
                "`acceptquest <id>` to accept one."
            )

        qdef       = self.quests.get(active)
        if not qdef:
            await user_conf.quests.set({})
            return await ctx.send(
                "Your active quest was invalid and has been cleared. Please pick a new quest."
            )

        # progress bookkeeping
        step_idx    = qstate.get("step", 0)
        total_steps = len(qdef["steps"])
        current     = min(step_idx + 1, total_steps)

        # build embed
        emb = discord.Embed(
            title=f"🗺️ {qdef['title']}",
            description=f"Step **{current}/{total_steps}**",
            colour=discord.Colour.purple()
        )
        emb.set_image(url=QUEST_BANNER_URL)

        # current step details
        if step_idx < total_steps:
            step = qdef["steps"][step_idx]
            emb.add_field(
                name="Objective",
                value=step.get("desc", "No description provided."),
                inline=False
            )

            # only add a “Progress” field for collect/deliver/sell steps
            prog = None
            if step["type"] == "collect_fish":
                needed = step["count"]
                name   = step.get("name")
                rarity = step.get("rarity")
                inv    = await user_conf.caught()
                have = (
                    inv.count(name)
                    if name
                    else sum(1 for f in inv
                             if f in self.fish_definitions
                             and self.fish_definitions[f]["rarity"] == rarity)
                )
                prog = f"{have}/{needed}"
            elif step["type"] == "deliver_item":
                needed = step["count"]
                item   = step["item"]
                inv_it = await user_conf.items()
                have   = inv_it.count(item)
                prog   = f"{have}/{needed} × {item}"
            elif step["type"] == "sell_value":
                needed = step["amount"]
                stats  = await user_conf.stats()
                have   = stats.get("sell_total", 0)
                curr   = await bank.get_currency_name(ctx.guild)
                prog   = f"{have}/{needed} {curr}"

            if prog:
                emb.add_field(name="Progress", value=prog, inline=True)

        else:
            emb.add_field(
                name="✅ All steps complete!",
                value="Use `completequest` to claim your rewards.",
                inline=False
            )

        await ctx.send(embed=emb)
        pass

    @commands.command()
    async def abandonquest(self, ctx):
        """Abandon your current active quest."""
        user_conf = self.config.user(ctx.author)
        qstate = await user_conf.quests()
        if not qstate or not qstate.get("active"):
            return await ctx.send("You have no active quest to abandon.")
        prev_completed = qstate.get("completed", [])
        await user_conf.quests.set({"completed": prev_completed})
        await ctx.send("You abandoned your active quest. Use `talknpc <npc>` to pick up new ones.")

    async def _advance_quest_on_catch(self, user, fish_name: str):
        user_conf = self.config.user(user)
        qstate = await user_conf.quests()
        active = qstate.get("active")
        if not active:
            return
        qdef = self.quests.get(active)
        if not qdef:
            return
        step_idx = qstate.get("step", 0)
        if step_idx >= len(qdef["steps"]):
            return
        step = qdef["steps"][step_idx]
        if step["type"] == "collect_fish":
            needed = step.get("count", 1)
            name = step.get("name")
            rarity = step.get("rarity")
            inv = await user_conf.caught()
            have = 0
            if name:
                have = inv.count(name)
            else:
                for f in inv:
                    if f in self.fish_definitions and self.fish_definitions[f].get("rarity") == rarity:
                        have += 1
            if have >= needed:
                qstate["step"] = step_idx + 1
                await user_conf.quests.set(qstate)

    async def _complete_quest_for_user(self, user, ctx=None):
        """Internal helper: complete and pay out the active quest for a user. Returns message string."""
        user_conf = self.config.user(user)
        qstate = await user_conf.quests()
        active = qstate.get("active")
        if not active:
            return "No active quest to complete."
        qdef = self.quests.get(active)
        if not qdef:
            await user_conf.quests.set({})
            return "Quest data invalid; cleared."
        inv = await user_conf.caught()
        items = await user_conf.items()
        stats = await user_conf.stats()
        # verify steps
        for step in qdef["steps"]:
            t = step["type"]
            if t == "collect_fish":
                needed = step.get("count", 1)
                name = step.get("name")
                rarity = step.get("rarity")
                have = 0
                if name:
                    have = inv.count(name)
                else:
                    for f in inv:
                        if f in self.fish_definitions and self.fish_definitions[f].get("rarity") == rarity:
                            have += 1
                if have < needed:
                    return "You have not yet completed the quest steps."
            elif t == "deliver_item":
                needed = step.get("count", 1)
                item = step.get("item")
                have = items.count(item)
                if have < needed:
                    return "You have not yet completed the quest steps."
            elif t == "sell_value":
                needed = step.get("amount", 0)
                if stats.get("sell_total", 0) < needed:
                    return "You have not yet completed the quest steps."
            elif t == "visit_npc":
                continue
            else:
                return "Unknown quest step type; cannot complete."

        # consume required things
        remaining_inv = list(inv)
        remaining_items = list(items)
        for step in qdef["steps"]:
            if step["type"] == "collect_fish":
                needed = step.get("count", 1)
                name = step.get("name")
                rarity = step.get("rarity")
                if name:
                    removed = 0
                    new_rem = []
                    for f in remaining_inv:
                        if f == name and removed < needed:
                            removed += 1
                            continue
                        new_rem.append(f)
                    remaining_inv = new_rem
                else:
                    to_remove = needed
                    for f in list(remaining_inv):
                        if to_remove <= 0:
                            break
                        if f in self.fish_definitions and self.fish_definitions[f].get("rarity") == rarity:
                            remaining_inv.remove(f)
                            to_remove -= 1
            elif step["type"] == "deliver_item":
                needed = step.get("count", 1)
                item = step.get("item")
                removed = 0
                new_items = []
                for it in remaining_items:
                    if it == item and removed < needed:
                        removed += 1
                        continue
                    new_items.append(it)
                remaining_items = new_items

        await user_conf.caught.set(remaining_inv)
        await user_conf.items.set(remaining_items)

        rewards = qdef.get("rewards", {})
        messages = []
        if "coins" in rewards:
            amt = int(rewards["coins"])
            new_bal, currency = await self._deposit(user, amt, ctx)
            messages.append(f"You received {amt} {currency}. New balance: {new_bal} {currency}.")
        if "items" in rewards:
            added_items = []
            items_cfg = await user_conf.items()
            for iname, cnt in rewards["items"].items():
                for _ in range(cnt):
                    items_cfg.append(iname)
                added_items.append(f"{cnt}× {iname}")
            await user_conf.items.set(items_cfg)
            messages.append("You received: " + ", ".join(added_items))

        prev = await self.config.user(user).quests()
        completed_list = prev.get("completed", [])
        if not qdef.get("repeatable", False):
            if active not in completed_list:
                completed_list.append(active)
        await user_conf.quests.set({"completed": completed_list})
        try:
            stats = await user_conf.stats()
            stats["quests_completed_total"] = stats.get("quests_completed_total", 0) + 1
            await user_conf.stats.set(stats)
            if stats["quests_completed_total"] >= 5 and not await self._has_achievement(user, "npc_friend"):
                await self._award_achievement(ctx or None, user, "npc_friend")
            if stats["quests_completed_total"] >= 25 and not await self._has_achievement(user, "quest_master"):
                await self._award_achievement(ctx or None, user, "quest_master")
        except Exception:
            pass        
        return "Quest complete! " + " ".join(messages)
        pass

    @commands.command()
    async def completequest(self, ctx):
        """Attempt to complete and claim rewards for your active quest."""
        user_conf = self.config.user(ctx.author)
        qstate = await user_conf.quests()
        active = qstate.get("active")
        if not active:
            return await ctx.send("You have no active quest.")
        msg = await self._complete_quest_for_user(ctx.author, ctx)
        await ctx.send(msg)
        pass

    @commands.command()
    async def visitnpc(self, ctx, npc_key: str):
        """Visit an NPC to advance quest steps that require visiting."""
        npc = self.npcs.get(npc_key.lower())
        if not npc:
            return await ctx.send("Unknown NPC key. Use `npcs` to list them.")
        user_conf = self.config.user(ctx.author)
        qstate = await user_conf.quests()
        active = qstate.get("active")
        if not active:
            return await ctx.send(f"You visit {npc['display']}. {npc.get('greeting','')}")
        qdef = self.quests.get(active)
        if not qdef:
            return await ctx.send(f"You visit {npc['display']}. {npc.get('greeting','')}")
        step_idx = qstate.get("step", 0)
        if step_idx >= len(qdef["steps"]):
            return await ctx.send(f"You visit {npc['display']}. It seems you've completed the steps; use `completequest`.")
        step = qdef["steps"][step_idx]
        if step["type"] == "visit_npc" and step.get("npc") == npc_key.lower():
            qstate["step"] = step_idx + 1
            await user_conf.quests.set(qstate)
            return await ctx.send(f"You spoke with {npc['display']}. Quest advanced.")
        return await ctx.send(f"You speak with {npc['display']}. {npc.get('greeting','')}")
        pass

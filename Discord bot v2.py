# bot_economy.py
import json
import os
import time
import random as rand
import asyncio
from dataclasses import dataclass, asdict
from typing import Dict, List

import discord
from discord.ext import commands

DATA_FILE = "user_data.json"

@dataclass
class User:
    money: int = 10
    xp: int = 0
    lastBegTime: float = 0.0
    lastWorkTime: float = 0.0
    hasJob: bool = False
    itemsOwned: List[str] = None
    curJob: str = "none"

    def __post_init__(self):
        if self.itemsOwned is None:
            self.itemsOwned = []

class UserStore:
    """In-memory store with JSON persistence and an asyncio.Lock for safety."""
    def __init__(self, path: str):
        self.path = path
        self.lock = asyncio.Lock()
        self.users: Dict[int, User] = {}

    async def load(self):
        """Load user data from JSON file (if present)."""
        try:
            if not os.path.exists(self.path):
                self.users = {}
                return
            async with self.lock:
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self.users = {int(k): User(**v) for k, v in raw.items()}
        except Exception as e:
            print("Failed to load user data:", e)
            self.users = {}

    async def save(self):
        """Save user data atomically to JSON."""
        async with self.lock:
            serializable = {str(k): asdict(v) for k, v in self.users.items()}
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=2)
            os.replace(tmp, self.path)

    def get(self, user_id: int) -> User:
        """Return a User instance for user_id (create if missing)."""
        if user_id not in self.users:
            self.users[user_id] = User()
        return self.users[user_id]

    def set(self, user_id: int, user: User):
        self.users[user_id] = user


# Setup bot
intents = discord.Intents.default()
intents.message_content = True  # enable only if you need message content
bot = commands.Bot(command_prefix="!", intents=intents)

store = UserStore(DATA_FILE)

# Data for jobs/shop
AVAIL_JOBS = [
    {"id": 1, "name": "The very legal pizzeria", "req_xp": 5000},
    {"id": 2, "name": "Not selling stolen goods", "req_xp": 5000},
]
SHOP = [
    {"name": "Cardboard trophy", "req_xp": 10, "cost": 10},
    {"name": "Iron trophy", "req_xp": 250, "cost": 300},
    {"name": "Diamond trophy", "req_xp": 1000, "cost": 1500},
]

COOLDOWN_BEG = 20       # seconds
COOLDOWN_WORK = 3600    # seconds (1 hour)


@bot.event
async def on_ready():
    await store.load()
    print(f"Bot ready as {bot.user} — loaded {len(store.users)} users.")


# Helper functions that operate on a User instance (no globals)
def beg_act(user: User):
    now = time.time()
    if now - user.lastBegTime < COOLDOWN_BEG:
        remaining = int(COOLDOWN_BEG - (now - user.lastBegTime))
        return False, f"Please wait {remaining} seconds before begging again."

    user.lastBegTime = now
    mGained = rand.randint(5, 80)
    xpGained = rand.randint(5, 15)
    user.money += mGained
    user.xp += xpGained
    return True, f"You begged and received ${mGained} and gained {xpGained} XP. Total: ${user.money}, XP: {user.xp}"


def work_act(user: User):
    now = time.time()
    if now - user.lastWorkTime < COOLDOWN_WORK:
        remaining = int(COOLDOWN_WORK - (now - user.lastWorkTime))
        minutes = max(1, int(remaining / 60))
        return False, f"Please wait {minutes} minutes before trying to work again."

    user.lastWorkTime = now
    mGained = rand.randint(150, 300)
    xpGained = rand.randint(25, 35)
    user.money += mGained
    user.xp += xpGained
    return True, f"You worked and earned ${mGained} and gained {xpGained} XP. Total: ${user.money}"


def check_inventory(user: User):
    lines = [f"Balance: ${user.money}", f"XP: {user.xp}", f"Job: {user.curJob if user.hasJob else 'None'}"]
    if user.itemsOwned:
        lines.append("Items: " + ", ".join(user.itemsOwned))
    return "\n".join(lines)


# Command handlers — with safe saves (try/except)
@bot.command(name="beg")
async def cmd_beg(ctx: commands.Context):
    user_id = ctx.author.id
    user = store.get(user_id)
    ok, msg = beg_act(user)
    if ok:
        store.set(user_id, user)
        try:
            await store.save()
        except Exception as e:
            print("Failed to save after beg:", e)
    await ctx.send(f"{ctx.author.mention} {msg}")


@bot.command(name="work")
async def cmd_work(ctx: commands.Context):
    user_id = ctx.author.id
    user = store.get(user_id)
    if not user.hasJob:
        await ctx.send(f"{ctx.author.mention} You do not have a job. Type `!joblist` to see options.")
        return
    ok, msg = work_act(user)
    if ok:
        store.set(user_id, user)
        try:
            await store.save()
        except Exception as e:
            print("Failed to save after work:", e)
    await ctx.send(f"{ctx.author.mention} {msg}")


@bot.command(name="inventory")
async def cmd_inventory(ctx: commands.Context):
    user = store.get(ctx.author.id)
    await ctx.send(f"{ctx.author.mention}\n{check_inventory(user)}")


@bot.command(name="joblist")
async def cmd_joblist(ctx: commands.Context):
    user = store.get(ctx.author.id)
    # show available jobs even if they don't qualify (helpful UX)
    job_lines = [f"{j['id']}. {j['name']} (req XP: {j['req_xp']})" for j in AVAIL_JOBS]
    if user.xp < 5000 and not user.hasJob:
        await ctx.send(f"{ctx.author.mention} You do not have enough XP to take a job right now (need 5000). You have {user.xp} XP.\nAvailable jobs:\n" + "\n".join(job_lines) + "\nPick with `!job 1` or `!job 2`.")
        return
    await ctx.send(f"{ctx.author.mention} Available jobs:\n" + "\n".join(job_lines) + "\nPick with `!job 1` or `!job 2`.")


@bot.command(name="job")
async def cmd_job(ctx: commands.Context, job_id: int):
    user_id = ctx.author.id
    user = store.get(user_id)
    job = next((j for j in AVAIL_JOBS if j["id"] == job_id), None)
    if job is None:
        await ctx.send(f"{ctx.author.mention} Unknown job id.")
        return
    if user.hasJob:
        await ctx.send(f"{ctx.author.mention} You already have a job: {user.curJob}.")
        return
    if user.xp < job["req_xp"]:
        await ctx.send(f"{ctx.author.mention} You don't have enough XP ({user.xp}) for that job (needs {job['req_xp']}).")
        return
    user.hasJob = True
    user.curJob = job["name"]
    store.set(user_id, user)
    try:
        await store.save()
    except Exception as e:
        print("Failed to save after job claim:", e)
    await ctx.send(f"{ctx.author.mention} You are now working at \"{job['name']}\".")


@bot.command(name="xpboost")
@commands.is_owner()
async def cmd_xpboost(ctx: commands.Context, amount: int = 5000):
    user = store.get(ctx.author.id)
    user.xp += amount
    store.set(ctx.author.id, user)
    try:
        await store.save()
    except Exception as e:
        print("Failed to save after xpboost:", e)
    await ctx.send(f"{ctx.author.mention} Owner boosted your XP by {amount}. New XP: {user.xp}")


@bot.command(name="setmoney")
@commands.has_permissions(administrator=True)
async def cmd_setmoney(ctx: commands.Context, member: discord.Member, amount: int):
    user = store.get(member.id)
    user.money = amount
    store.set(member.id, user)
    try:
        await store.save()
    except Exception as e:
        print("Failed to save after setmoney:", e)
    await ctx.send(f"{member.mention}'s money set to ${amount} by {ctx.author.mention}.")


# Run the bot (use environment variable or replace with your token)
if __name__ == "__main__":
    # recommended env var name: DISCORD_BOT_TOKEN
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not TOKEN:
        print("Set DISCORD_BOT_TOKEN environment variable.")
    else:
        bot.run(TOKEN)

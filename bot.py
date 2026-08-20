import os
import random
import json

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load your 1000‑movie JSON file
with open("movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

# ⭐ Set this to the channel where the bot should post daily
DAILY_CHANNEL_ID = 1539941178672291842  # ← replace with your channel ID


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    daily_movie.start()  # start the daily loop when bot is ready


@tasks.loop(hours=24)
async def daily_movie():
    """Sends a random movie once every 24 hours."""
    channel = bot.get_channel(DAILY_CHANNEL_ID)
    if channel is None:
        print("Daily channel not found. Check the ID.")
        return

    movie = random.choice(movies)

    embed = discord.Embed(
        title=f"🎬 Movie of the Day: {movie['title']}",
        description=movie["description"]
    )

    embed.add_field(name="📅 Year", value=movie["year"])
    embed.add_field(name="🎭 Genre", value=movie["genre"])
    embed.set_footer(text="🍿 The Usher's Movie of the Day")

    await channel.send(embed=embed)


@bot.command()
async def movie(ctx):
    """Manual command still works."""
    movie = random.choice(movies)

    embed = discord.Embed(
        title=f"🎬 Movie of the Day: {movie['title']}",
        description=movie["description"]
    )

    embed.add_field(name="📅 Year", value=movie["year"])
    embed.add_field(name="🎭 Genre", value=movie["genre"])
    embed.set_footer(text="🍿 The Usher's Movie of the Day")

    await ctx.send(embed=embed)


bot.run(TOKEN)

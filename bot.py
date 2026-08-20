import os
import random
import json
from datetime import time
from zoneinfo import ZoneInfo
from threading import Thread

from flask import Flask
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is missing")

# Flask web server for Render
app = Flask(__name__)


@app.route("/")
def home():
    return "Discord bot is running!"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load your 1000-movie JSON file
with open("movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

# Channel where the bot should post daily
DAILY_CHANNEL_ID = 1538316181470187550

# Daily posting time: 9:00 AM GMT
GMT = ZoneInfo("Etc/GMT")
DAILY_MOVIE_TIME = time(hour=9, minute=0, tzinfo=GMT)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    if not daily_movie.is_running():
        daily_movie.start()


@tasks.loop(time=DAILY_MOVIE_TIME)
async def daily_movie():
    """Sends a random movie every day at 9:00 AM GMT."""
    channel = bot.get_channel(DAILY_CHANNEL_ID)

    if channel is None:
        print("Daily channel not found. Check the ID.")
        return

    movie = random.choice(movies)

    embed = discord.Embed(
        title=f"🎬 Movie of the Day: {movie['title']}",
        description=movie["description"]
    )

    embed.add_field(name="📅 Year", value=str(movie["year"]))
    embed.add_field(name="🎭 Genre", value=str(movie["genre"]))
    embed.set_footer(text="🍿 The Usher's Movie of the Day")

    await channel.send(embed=embed)


@bot.command()
async def movie(ctx):
    """Posts a random movie manually."""
    movie = random.choice(movies)

    embed = discord.Embed(
        title=f"🎬 Movie of the Day: {movie['title']}",
        description=movie["description"]
    )

    embed.add_field(name="📅 Year", value=str(movie["year"]))
    embed.add_field(name="🎭 Genre", value=str(movie["genre"]))
    embed.set_footer(text="🍿 The Usher's Movie of the Day")

    await ctx.send(embed=embed)


if __name__ == "__main__":
    # Start the web server in the background for Render
    Thread(target=run_web, daemon=True).start()

    # Start the Discord bot
    bot.run(TOKEN)
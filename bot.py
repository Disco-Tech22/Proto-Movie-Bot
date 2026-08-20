import os
import random
import json
import webserver
from datetime import time, timezone
from threading import Thread


from flask import Flask
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is missing. "
        "Add DISCORD_TOKEN to your Render Environment Variables."
    )


# ============================================================
# FLASK WEB SERVER
# Required because this is running as a Render Web Service
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "🎬 The Usher's Movie Bot is online!"


@app.route("/health")
def health():
    return "OK"


def run_web():
    port = int(os.environ.get("PORT", 10000))

    print(f"Starting web server on port {port}")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# ============================================================
# DISCORD BOT
# ============================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# MOVIES
# ============================================================

try:
    with open("movies.json", "r", encoding="utf-8") as f:
        movies = json.load(f)
except FileNotFoundError:
    raise RuntimeError(
        "movies.json was not found. "
        "Make sure movies.json is committed to your GitHub repository."
    )

if not movies:
    raise RuntimeError("movies.json is empty.")


# ============================================================
# SETTINGS
# ============================================================

# Discord channel where the daily movie will be posted
DAILY_CHANNEL_ID = 1538316181470187550

# 09:00 GMT every day
#
# UTC is equivalent to GMT for this purpose.
# Using timezone.utc avoids the ZoneInfo/tzdata problem.
DAILY_MOVIE_TIME = time(
    hour=16,
    minute=0,
    tzinfo=timezone.utc
)


# ============================================================
# MOVIE EMBED
# ============================================================

def create_movie_embed():
    """Create an embed containing a random movie."""

    movie = random.choice(movies)

    embed = discord.Embed(
        title=f"🎬 Movie of the Day: {movie['title']}",
        description=movie.get(
            "description",
            "No description available."
        )
    )

    embed.add_field(
        name="📅 Year",
        value=str(movie.get("year", "Unknown")),
        inline=True
    )

    embed.add_field(
        name="🎭 Genre",
        value=str(movie.get("genre", "Unknown")),
        inline=True
    )

    embed.set_footer(
        text="🍿 The Usher's Movie of the Day"
    )

    return embed


# ============================================================
# DISCORD EVENTS
# ============================================================

@bot.event
async def on_ready():
    print("========================================")
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Movies loaded: {len(movies)}")
    print("========================================")

    if not daily_movie.is_running():
        daily_movie.start()
        print("Daily movie task started.")


# ============================================================
# DAILY MOVIE
# ============================================================

@tasks.loop(time=DAILY_MOVIE_TIME)
async def daily_movie():
    """Posts a random movie every day at 09:00 GMT."""

    print("Daily movie task triggered.")

    channel = bot.get_channel(DAILY_CHANNEL_ID)

    if channel is None:
        print(
            f"ERROR: Could not find Discord channel "
            f"{DAILY_CHANNEL_ID}"
        )
        return

    try:
        embed = create_movie_embed()

        await channel.send(embed=embed)

        print("Daily movie successfully posted.")

    except discord.Forbidden:
        print(
            "ERROR: Discord rejected the message. "
            "Make sure the bot has permission to send messages "
            "and embed links in the channel."
        )

    except discord.HTTPException as e:
        print(f"ERROR: Discord API error: {e}")

    except Exception as e:
        print(f"ERROR sending daily movie: {e}")


# ============================================================
# MANUAL COMMAND
# ============================================================

@bot.command()
async def movie(ctx):
    """Posts a random movie manually using !movie."""

    try:
        embed = create_movie_embed()

        await ctx.send(embed=embed)

    except discord.Forbidden:
        await ctx.send(
            "❌ I don't have permission to send messages or embeds here."
        )

    except Exception as e:
        print(f"ERROR with !movie command: {e}")


# ============================================================
# ERROR HANDLING
# ============================================================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ You're missing a required argument.")

    else:
        print(f"Command error: {error}")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    # Start Flask in the background.
    # Render needs the web server to listen on its assigned PORT.
    web_thread = Thread(
        target=run_web,
        daemon=True
    )

    web_thread.start()

    print("Flask web server started.")

    # Start Discord bot
    print("Starting Discord bot...")

    webserver.keep_alive

    bot.run(TOKEN)
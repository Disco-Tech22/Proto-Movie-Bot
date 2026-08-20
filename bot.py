import os
import random
import json
from datetime import datetime, time
from zoneinfo import ZoneInfo
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

DAILY_CHANNEL_ID = 1538316181470187550

# UK timezone
UK_TIMEZONE = ZoneInfo("Europe/London")

# Daily movie post time: 17:28 UK time
DAILY_MOVIE_TIME = time(
    hour=17,
    minute=28,
    tzinfo=UK_TIMEZONE
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
# GET DAILY CHANNEL
# ============================================================

async def get_daily_channel():

    print(f"Looking for Discord channel: {DAILY_CHANNEL_ID}")

    channel = bot.get_channel(DAILY_CHANNEL_ID)

    if channel is not None:
        print(
            f"Channel found in cache: "
            f"#{getattr(channel, 'name', 'unknown')}"
        )
        return channel

    print("Channel not in cache. Fetching from Discord...")

    try:
        channel = await bot.fetch_channel(DAILY_CHANNEL_ID)

        print(
            f"Channel successfully fetched: "
            f"#{getattr(channel, 'name', 'unknown')}"
        )

        return channel

    except discord.NotFound:
        print(
            "ERROR: Discord says this channel does not exist."
        )

    except discord.Forbidden:
        print(
            "ERROR: Discord denied access to this channel."
        )

    except discord.HTTPException as e:
        print(
            f"ERROR fetching channel from Discord: {e}"
        )

    return None


# ============================================================
# DISCORD READY
# ============================================================

@bot.event
async def on_ready():

    print("")
    print("========================================")
    print("DISCORD BOT CONNECTED")
    print("========================================")

    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Movies loaded: {len(movies)}")

    now = datetime.now(UK_TIMEZONE)

    print(f"Current UK time: {now}")
    print(f"Scheduled time: {DAILY_MOVIE_TIME}")

    # Check target channel
    channel = await get_daily_channel()

    if channel:
        print(
            f"Target channel confirmed: "
            f"#{getattr(channel, 'name', 'unknown')}"
        )
    else:
        print(
            "WARNING: Target channel could not be accessed."
        )

    # Start scheduler
    if not daily_movie.is_running():

        daily_movie.start()

        print("Daily movie scheduler STARTED.")

    else:

        print("Daily movie scheduler was already running.")

    print("========================================")
    print("")


# ============================================================
# DAILY MOVIE
# ============================================================

@tasks.loop(time=DAILY_MOVIE_TIME)
async def daily_movie():
    """Posts a random movie every day at 17:28 UK time."""

    now = datetime.now(UK_TIMEZONE)

    print("")
    print("========================================")
    print("DAILY MOVIE TASK TRIGGERED")
    print(f"UK time: {now}")
    print("========================================")

    channel = await get_daily_channel()

    if channel is None:

        print(
            "ERROR: Cannot post because the Discord "
            "channel could not be accessed."
        )

        return

    try:

        embed = create_movie_embed()

        await channel.send(embed=embed)

        print("SUCCESS: Daily movie posted.")

    except discord.Forbidden:

        print(
            "ERROR: Discord rejected the message."
        )

        print(
            "Check that the bot has these permissions "
            "in the target channel:"
        )

        print("- View Channel")
        print("- Send Messages")
        print("- Embed Links")

    except discord.HTTPException as e:

        print(
            f"ERROR: Discord API error: {e}"
        )

    except Exception as e:

        print(
            f"ERROR sending daily movie: {e}"
        )


# ============================================================
# SCHEDULER ERROR
# ============================================================

@daily_movie.error
async def daily_movie_error(error):

    print("")
    print("========================================")
    print("DAILY MOVIE SCHEDULER ERROR")
    print("========================================")

    print(repr(error))

    print("========================================")
    print("")


# ============================================================
# MANUAL MOVIE COMMAND
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

        print(
            f"ERROR with !movie command: {e}"
        )


# ============================================================
# TEST TARGET CHANNEL
# ============================================================

@bot.command()
@commands.is_owner()
async def testmovie(ctx):
    """Test posting to the configured daily movie channel."""

    print("TESTMOVIE command triggered.")

    channel = await get_daily_channel()

    if channel is None:

        await ctx.send(
            "❌ I cannot access the configured daily movie channel."
        )

        return

    try:

        embed = create_movie_embed()

        await channel.send(embed=embed)

        await ctx.send(
            "✅ Test movie successfully posted to the daily channel."
        )

        print(
            "SUCCESS: testmovie posted to target channel."
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ Discord denied permission to post in the target channel."
        )

    except discord.HTTPException as e:

        await ctx.send(
            f"❌ Discord API error: {e}"
        )

        print(
            f"Discord API error: {e}"
        )


# ============================================================
# COMMAND ERROR HANDLING
# ============================================================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.NotOwner):

        await ctx.send(
            "❌ Only the bot owner can use that command."
        )

        return

    if isinstance(error, commands.MissingRequiredArgument):

        await ctx.send(
            "❌ You're missing a required argument."
        )

        return

    print(
        f"Command error: {repr(error)}"
    )


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

    bot.run(TOKEN)
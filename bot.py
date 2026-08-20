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
# DISCORD BOT SETTINGS
# ============================================================

intents = discord.Intents.default()
intents.message_content = True


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

# Always use UK local time.
# This automatically handles GMT and BST.
UK_TIMEZONE = ZoneInfo("Europe/London")

# Daily movie time: 17:28 UK time
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
# DAILY MOVIE TASK
# ============================================================

@tasks.loop(time=DAILY_MOVIE_TIME)
async def daily_movie():
    """Posts a random movie every day at 17:28 UK time."""

    now = datetime.now(UK_TIMEZONE)

    print("")
    print("========================================")
    print("DAILY MOVIE TASK TRIGGERED")
    print(f"UK TIME: {now}")
    print("========================================")

    channel = bot.get_channel(DAILY_CHANNEL_ID)

    if channel is None:

        print(
            f"Channel {DAILY_CHANNEL_ID} "
            "was not found in cache."
        )

        try:

            channel = await bot.fetch_channel(
                DAILY_CHANNEL_ID
            )

            print(
                f"Successfully fetched channel: "
                f"{getattr(channel, 'name', 'unknown')}"
            )

        except discord.NotFound:

            print(
                "ERROR: Discord says the channel "
                "does not exist."
            )

            return

        except discord.Forbidden:

            print(
                "ERROR: Discord denied access to "
                "the channel."
            )

            return

        except discord.HTTPException as e:

            print(
                f"ERROR fetching channel: {e}"
            )

            return

    try:

        embed = create_movie_embed()

        await channel.send(embed=embed)

        print("")
        print("========================================")
        print("SUCCESS: DAILY MOVIE POSTED")
        print(f"Channel: {channel.name}")
        print("========================================")
        print("")

    except discord.Forbidden:

        print("")
        print("========================================")
        print("ERROR: DISCORD FORBIDDEN")
        print("========================================")
        print("The bot does not have permission to post.")
        print("Required permissions:")
        print("- View Channel")
        print("- Send Messages")
        print("- Embed Links")
        print("========================================")
        print("")

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
# DISCORD BOT CLASS
# ============================================================

class MovieBot(commands.Bot):

    async def setup_hook(self):

        print("")
        print("========================================")
        print("SETTING UP MOVIE BOT")
        print("========================================")

        print(
            f"Scheduled daily time: "
            f"{DAILY_MOVIE_TIME}"
        )

        print(
            f"Target channel ID: "
            f"{DAILY_CHANNEL_ID}"
        )

        if not daily_movie.is_running():

            daily_movie.start()

            print(
                "Daily movie scheduler STARTED."
            )

        else:

            print(
                "Daily movie scheduler "
                "was already running."
            )

        print("========================================")
        print("")


# ============================================================
# CREATE BOT
# ============================================================

bot = MovieBot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# DISCORD READY
# ============================================================

@bot.event
async def on_ready():

    now = datetime.now(UK_TIMEZONE)

    print("")
    print("========================================")
    print("DISCORD BOT CONNECTED")
    print("========================================")

    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Movies loaded: {len(movies)}")
    print(f"Current UK time: {now}")
    print(f"Daily scheduled time: {DAILY_MOVIE_TIME}")

    channel = bot.get_channel(DAILY_CHANNEL_ID)

    if channel:

        print(
            f"Target channel: #{channel.name}"
        )

    else:

        print(
            "Target channel is not currently cached."
        )

    print("========================================")
    print("")


# ============================================================
# MANUAL MOVIE COMMAND
# ============================================================

@bot.command()
async def movie(ctx):
    """Posts a random movie manually."""

    try:

        embed = create_movie_embed()

        await ctx.send(embed=embed)

        print(
            f"Manual movie requested by {ctx.author}"
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ I don't have permission to send "
            "messages or embeds here."
        )

    except Exception as e:

        print(
            f"ERROR with !movie command: {e}"
        )


# ============================================================
# TEST DAILY CHANNEL
# ============================================================

@bot.command()
@commands.is_owner()
async def testmovie(ctx):
    """Immediately tests the daily movie channel."""

    print("")
    print("========================================")
    print("TESTMOVIE COMMAND TRIGGERED")
    print("========================================")

    try:

        channel = bot.get_channel(
            DAILY_CHANNEL_ID
        )

        if channel is None:

            print(
                "Channel not in cache. "
                "Fetching from Discord..."
            )

            channel = await bot.fetch_channel(
                DAILY_CHANNEL_ID
            )

        print(
            f"Posting test movie to: "
            f"#{channel.name}"
        )

        embed = create_movie_embed()

        await channel.send(embed=embed)

        await ctx.send(
            "✅ Test movie posted successfully."
        )

        print(
            "SUCCESS: Test movie posted."
        )

    except discord.NotFound:

        await ctx.send(
            "❌ The configured channel does not exist."
        )

        print(
            "ERROR: Channel not found."
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ The bot does not have permission "
            "to post in the daily channel."
        )

        print(
            "ERROR: Discord Forbidden."
        )

    except discord.HTTPException as e:

        await ctx.send(
            f"❌ Discord API error: {e}"
        )

        print(
            f"ERROR: Discord API error: {e}"
        )

    except Exception as e:

        await ctx.send(
            f"❌ Unexpected error: {e}"
        )

        print(
            f"ERROR: {e}"
        )


# ============================================================
# COMMAND ERROR HANDLING
# ============================================================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(
        error,
        commands.CommandNotFound
    ):

        return

    if isinstance(
        error,
        commands.NotOwner
    ):

        await ctx.send(
            "❌ Only the bot owner can use that command."
        )

        return

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

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

    # Start Flask web server in background.
    # Render requires the service to listen on PORT.
    web_thread = Thread(
        target=run_web,
        daemon=True
    )

    web_thread.start()

    print(
        "Flask web server started."
    )

    # Start Discord bot.
    print(
        "Starting Discord bot..."
    )

    bot.run(TOKEN)
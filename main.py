"""This discord bot is a real piece of shit held together by sweat, blood, duct tape and glue."""

# Import needed modules
from discord.ext import commands
import discord
import sqlite3
import os

# Configure logging, code copied straight from the discordpy docs :drippysmile:
import logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Import cog class files
from bin.cogs.image import Image
from bin.cogs.alerts import Alert
from bin.cogs.roles import Roles

# Import class for custom help commands
from bin.helpers.help_command import CustomHelpCommand

# Import hidden commands module
from bin.helpers.util import commands_from_module, error_embed


# Initiate bot. Default intents, but enable members to be able to see the server's members for the roleopt command.
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=".", help_command=CustomHelpCommand(), case_insensitive=True, intents=intents)


# If you can't open the database why even start the bot lmao
if os.path.isfile("./bin/db/bot.sqlite"):
    db_path = "./bin/db/bot.sqlite"
else:
    print("haha oopsie database not found")
    exit()


# Initiate SQLite database (db) connection, to manipulate the database containing required information.
# Declare detect_types to convert TIMESTAMP values to datetime objects automatically.
db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)


# Add cogs to bot
bot.add_cog(Alert(bot, db))
bot.add_cog(Roles(bot, db))
bot.add_cog(Image(bot))


# Execute on login
@bot.event
async def on_ready():
    # Set bot's current activity and status
    status = discord.Game(name="Sus Fuckers")
    await bot.change_presence(status=discord.Status.online, activity=status)

    # Print login on console
    print("Logged in as {0}.".format(bot.user))


# Catch command errors so there are no runtime exceptions.
# # Probably comment this out if you're changing shit around, yeah?
@bot.event
async def on_command_error(ctx, error):
    if ctx.guild is None:
        return
    else:
        return await ctx.send(embed=error_embed(str(error)))


# Starts up the bot.
bot.run(os.getenv("BOT_TOKEN"))
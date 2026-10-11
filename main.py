import discord
import os
import importlib
import sys

from lib import database as db
from dotenv import load_dotenv

# Setup
load_dotenv()

OWNER = int(os.getenv("OWNER", "0"))
bot = discord.Bot()

# Bot loader
def get_extensions():
    return [
        f"cogs.{file[:-3]}"
        for file in os.listdir("cogs")
        if file.endswith(".py") and not file.startswith("_")
    ]


def reload_lib():
    modules = sorted(
        [
            name for name in sys.modules
            if name.startswith("lib.")
            and name != "lib.database"
        ],
        key=lambda name: name.count("."),
    )

    for name in modules:
        importlib.reload(sys.modules[name])
        print(f"↻ Reloaded {name}")


def reload_cogs():
    for extension in get_extensions():
        try:
            if extension in bot.extensions:
                bot.reload_extension(extension)
                print(f"↻ Reloaded {extension}")
            else:
                bot.load_extension(extension)
                print(f"+ Loaded {extension}")
        except Exception as e:
            print(f"✗ {extension}: {e}")
            raise


def reload_all():
    print("--- Reloading libraries ---")
    reload_lib()

    print("--- Reloading cogs ---")
    reload_cogs()


# Developer command group
dev = discord.SlashCommandGroup("dev", "Developer commands")

@dev.command(name="reload", description="Reload bot libraries and cogs")
async def dev_reload(ctx: discord.ApplicationContext):
    if ctx.author.id != OWNER:
        await ctx.respond("return to this command if youre a dev", ephemeral=True)
        return

    await ctx.defer(ephemeral=True)

    try:
        reload_all()
    except Exception as e:
        print(f"✗ Reload failed: {e}")
        await ctx.followup.send(
            f"Reload failed: `{type(e).__name__}: {e}`",
            ephemeral=True,
        )
        return

    await ctx.followup.send("Libraries and cogs reloaded.", ephemeral=True)


@dev.command(name="migrate", description="Run database migrations")
async def dev_migrate(ctx: discord.ApplicationContext):
    if ctx.author.id != OWNER:
        await ctx.respond("return to this command if youre a dev", ephemeral=True)
        return

    await ctx.defer(ephemeral=True)

    try:
        db.migrate()
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        await ctx.followup.send(
            f"Migration failed: `{type(e).__name__}: {e}`",
            ephemeral=True,
        )
        return

    await ctx.followup.send("atabase migrations completed.", ephemeral=True)


bot.add_application_command(dev)


# Load cogs
reload_cogs()

# Run bot
bot.run(os.getenv("TOKEN"))
import discord
import os
import threading
from dotenv import load_dotenv

# Setup
load_dotenv()
bot = discord.Bot()

# Bot loader
def get_extensions():
    return [
        f"cogs.{file[:-3]}"
        for file in os.listdir("cogs")
        if file.endswith(".py") and not file.startswith("_")
    ]

def reload_cogs():
    extensions = get_extensions()

    for extension in extensions:
        try:
            if extension in bot.extensions:
                bot.reload_extension(extension)
                print(f"↻ Reloaded {extension}")
            else:
                bot.load_extension(extension)
                print(f"+ Loaded {extension}")

        except Exception as e:
            print(f"✗ {extension}: {e}")

def input_menu():
    while True:
        key = input().strip().lower()

        if key == "r":
            reload_cogs()

reload_cogs()
threading.Thread(target=input_menu, daemon=True).start()

# Run bot
bot.run(os.getenv('TOKEN'))
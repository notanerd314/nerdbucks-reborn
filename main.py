import discord
import os
from dotenv import load_dotenv

load_dotenv()
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name="ping", description="all discord bots have this")
async def hello(ctx: discord.ApplicationContext):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="Pong!",
        description=f"**Latency:** `{latency}`",
        color=15548997
    )

    embed.set_thumbnail(
        url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT9NOUAn5ffT57TkgqMyQNZ7U_2HbgXVD-GV5OdEUUtUQ&s=10"
    )

    await ctx.respond(embed=embed)

bot.run(os.getenv('TOKEN'))
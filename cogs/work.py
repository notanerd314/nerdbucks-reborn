import random

import discord
from discord.ext import commands
from lib import database as db

import lib.jobs.guess_number as guess_number
import lib.jobs.package_sorter as package_sorter
import lib.jobs.trivia as trivia

class Work(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(name="work", description="Work to earn money.")
    async def work(self, ctx: discord.ApplicationContext):
        game = random.choice(
            (
                guess_number.main,
                package_sorter.main,
                trivia.main,
            )
        )
        pay = await game(ctx)

        if pay is None:
            return

        # The game has finished; now award the money.
        db.change_amount(ctx.author.id, pay, "wallet")

        await ctx.followup.send(f"You earned **${pay}**!")

def setup(bot: commands.Bot):
    bot.add_cog(Work(bot))
import discord
from discord.ext import commands
from lib import database as db

import lib.jobs.package_sorter as package_sorter

class Work(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(name="work", description="Work to earn money.")
    async def work(self, ctx: discord.ApplicationContext):
        pay = await package_sorter.main(ctx)

        # The game has finished; now award the money.
        db.change_amount(ctx.author.id, pay, "wallet")

        await ctx.followup.send(f"You earned **${pay}**!")

def setup(bot: commands.Bot):
    bot.add_cog(Work(bot))
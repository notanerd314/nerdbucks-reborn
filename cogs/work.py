
import random

import discord
from discord.ext import commands
from lib import database as db
from lib.emojis import NERDBUCKS
from lib import util

import lib.jobs.guess_number as guess_number
import lib.jobs.package_sorter as package_sorter
import lib.jobs.trivia as trivia


class Work(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(name="work", description="Work to earn money.")
    async def work(self, ctx: discord.ApplicationContext):
        on_cooldown, remaining = db.is_on_cooldown(
            ctx.author.id, "work", 40 * 60
        )

        if on_cooldown:
            await ctx.respond(
                "don't overwork man! hard work doesnt always bring happiness, "
                f"wait `{util.pretty_time(remaining)}` for your next shift",
                ephemeral=True,
            )
            return

        await ctx.defer()

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
        db.set_cooldown(ctx.author.id, "work")

        await ctx.followup.send(f"You earned **{pay} {NERDBUCKS}**!")


def setup(bot: commands.Bot):
    bot.add_cog(Work(bot))

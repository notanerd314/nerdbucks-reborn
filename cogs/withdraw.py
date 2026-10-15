import discord
from discord.ext import commands
from lib import database as db


class Withdraw(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(name="withdraw", description="Withdraw money from your bank.")
    @discord.option(
        "amount",
        int,
        required=True,
        description="The amount to withdraw",
    )
    async def withdraw(self, ctx: discord.ApplicationContext, amount: int):
        if amount <= 0:
            await ctx.respond("Enter an amount greater than zero.", ephemeral=True)
            return

        transferred = db.transfer_amount(
            ctx.author.id,
            amount,
            "bank",
            "wallet",
        )
        if not transferred:
            await ctx.respond("You don't have enough money in your bank.", ephemeral=True)
            return

        await ctx.respond(f"Withdrew **${amount:,}** from your bank.")


def setup(bot: commands.Bot):
    bot.add_cog(Withdraw(bot))

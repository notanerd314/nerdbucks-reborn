import discord
from discord.ext import commands
from lib import database as db


class Deposit(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(name="deposit", description="Deposit money into your bank.")
    @discord.option(
        "amount",
        int,
        required=True,
        description="The amount to deposit",
    )
    async def deposit(self, ctx: discord.ApplicationContext, amount: int):
        if amount <= 0:
            await ctx.respond("Enter an amount greater than zero.", ephemeral=True)
            return

        fee = amount * 5 // 100
        deposited = amount - fee
        transferred = db.transfer_amount(
            ctx.author.id,
            amount,
            "wallet",
            "bank",
            fee,
        )
        if not transferred:
            await ctx.respond("You don't have enough money in your wallet.", ephemeral=True)
            return

        await ctx.respond(
            f"Deposited **${deposited:,}** into your bank. "
            f"Fee: **${fee:,}** (5%)."
        )


def setup(bot: commands.Bot):
    bot.add_cog(Deposit(bot))

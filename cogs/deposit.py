
import discord
from discord.ext import commands
from lib import database as db
from lib.emojis import NERDBUCKS

DEPOSIT_FEE = 8

class Deposit(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(
        name="deposit",
        description="Deposit money into your bank.",
    )
    @discord.option(
        "amount",
        int,
        required=True,
        description="The amount to deposit",
    )
    async def deposit(self, ctx: discord.ApplicationContext, amount: int):
        if amount <= 0:
            await ctx.respond(
                "Enter an amount greater than zero.",
                ephemeral=True,
            )
            return

        fee = amount * DEPOSIT_FEE // 100
        deposited = amount - fee

        transferred = db.transfer_amount(
            ctx.author.id,
            amount,
            "wallet",
            "bank",
            fee,
        )

        if not transferred:
            await ctx.respond(
                "You don't have enough money in your wallet.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Deposit Successful",
            description=(
                f"Successfully deposited **{deposited:,} {NERDBUCKS}** into your bank."
            ),
        )

        embed.add_field(
            name="💵 Amount",
            value=f"{amount:,} {NERDBUCKS}",
            inline=True,
        )
        embed.add_field(
            name="📉 Transaction Fee (8%)",
            value=f"-{fee:,} {NERDBUCKS}",
            inline=True,
        )
        embed.add_field(
            name="🏦 Deposited",
            value=f"**{deposited:,} {NERDBUCKS}**",
            inline=True,
        )

        await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Deposit(bot))

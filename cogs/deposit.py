
import discord
from discord.ext import commands
from discord.ui import Container, DesignerView, Separator, TextDisplay
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

        view = DesignerView()
        view.add_item(
            Container(
                TextDisplay(
                    "# Deposit Successful\n"
                    f"Successfully deposited **{deposited:,} {NERDBUCKS}** into your bank."
                ),
                Separator(),
                TextDisplay(
                    f"💵 **Amount:** {amount:,} {NERDBUCKS}\n"
                    f"📉 **Transaction Fee (8%):** -{fee:,} {NERDBUCKS}\n"
                    f"🏦 **Deposited:** **{deposited:,} {NERDBUCKS}**"
                ),
            )
        )

        await ctx.respond(view=view)


def setup(bot: commands.Bot):
    bot.add_cog(Deposit(bot))

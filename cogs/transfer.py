import discord
from discord.ext import commands
from discord.ui import Container, DesignerView, TextDisplay
from lib import database as db
from lib.emojis import NERDBUCKS


class Transfer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(
        name="transfer",
        description="Transfer money to someone else.",
    )
    @discord.option(
        "user",
        discord.User,
        required=True,
        description="Target user to transfer to"
    )
    @discord.option(
        "amount",
        int,
        required=True,
        description="The amount to transfer",
    )
    async def transfer(self, ctx: discord.ApplicationContext, user: discord.User, amount: int):
        if amount <= 0:
            await ctx.respond(
                "Enter an amount greater than zero.",
                ephemeral=True,
            )
            return

        transferred = db.transfer_user(
            ctx.author.id,
            user.id,
            "wallet",
            amount
        )
        
        if not transferred:
            await ctx.respond(
                "You don't have enough money in your bank.",
                ephemeral=True,
            )
            return

        view = DesignerView()
        view.add_item(
            Container(
                TextDisplay(
                    "# Transfer Successful\n"
                    f"Successfully transferred **{amount:,} {NERDBUCKS}** from your wallet "
                    f"to {user.mention}'s wallet."
                )
            )
        )

        await ctx.respond(view=view)


def setup(bot: commands.Bot):
    bot.add_cog(Transfer(bot))
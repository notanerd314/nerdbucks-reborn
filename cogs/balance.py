
import discord
from discord.ext import commands
from discord.ui import (
    DesignerView,
    Container,
    TextDisplay,
    Separator,
    Section,
    Thumbnail,
    ActionRow,
    button,
)
from lib import database as db


class BalanceViewActions(ActionRow):
    def __init__(self, view: "BalanceView"):
        super().__init__()
        self.balance_view = view

    @button(label="Refresh", style=discord.ButtonStyle.secondary)
    async def refresh(self, button, interaction: discord.Interaction):
        view = self.balance_view

        if (
            interaction.user is None
            or interaction.user.id != view.interaction_owner_id
        ):
            await interaction.response.send_message(
                "who the fuck do you think you are?",
                ephemeral=True,
            )
            return

        await view.refresh(interaction)

class BalanceView(DesignerView):
    def __init__(
        self,
        interaction_owner_id: int,
        user_id: int,
        username: str,
        display_name: str,
        rank: str,
        wallet: int,
        bank: int,
        avatar_url: str,
    ):
        super().__init__(timeout=180.0)

        self.interaction_owner_id = interaction_owner_id
        self.user_id = user_id
        self.username = username
        self.display_name = display_name
        self.rank = rank
        self.avatar_url = avatar_url

        self.add_item(self.make_container(wallet, bank))
        self.add_item(BalanceViewActions(self))

    def make_container(self, wallet: int, bank: int) -> Container:
        net_worth = wallet + bank

        return Container(
            Section(
                TextDisplay(
                    f"# {self.display_name} ({self.username})\n"
                    f"**Rank:** {self.rank}"
                ),
                accessory=Thumbnail(self.avatar_url),
            ),
            Separator(),
            TextDisplay(
                f"## Total Net Worth: {net_worth:,} 🪙\n"
                f"**Wallet:** {wallet:,} 🪙\n"
                f"**Bank:** {bank:,} 🪙"
            ),
            colour=discord.Colour(5793266),
        )

    async def refresh(self, interaction: discord.Interaction):
        profile = db.get_user(self.user_id)

        if profile is None:
            await interaction.response.send_message(
                "This user doesn't have an account yet.",
                ephemeral=True,
            )
            return

        new_view = BalanceView(
            interaction_owner_id=self.interaction_owner_id,
            user_id=self.user_id,
            username=self.username,
            display_name=self.display_name,
            rank=self.rank,
            wallet=profile["wallet"],
            bank=profile["bank"],
            avatar_url=self.avatar_url,
        )

        await interaction.response.edit_message(view=new_view)


class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(
        name="balance",
        description="Check your or another user's balance",
    )
    @discord.option(
        "user",
        discord.User,
        required=False,
        description="The user to check the balance of",
    )
    async def balance(
        self,
        ctx: discord.ApplicationContext,
        user: discord.User | None = None,
    ):
        target_user = user or ctx.author
        profile = db.get_user(target_user.id)

        if profile is None:
            await ctx.respond(
                "This user doesn't have an account yet.",
                ephemeral=True,
            )
            return

        await ctx.respond(
            view=BalanceView(
                interaction_owner_id=ctx.author.id,
                user_id=target_user.id,
                username=target_user.name,
                display_name=target_user.display_name,
                rank="N/A",
                wallet=profile["wallet"],
                bank=profile["bank"],
                avatar_url=target_user.display_avatar.url,
            )
        )


def setup(bot):
    bot.add_cog(Balance(bot))

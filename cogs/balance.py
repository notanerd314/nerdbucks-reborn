import discord
from lib import database as db

class Balance(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(
        name="balance",
        description="Check youan users balance"
    )
    async def balance(self, ctx: discord.ApplicationContext):
        user = db.get_user(ctx.author.id)

def setup(bot):
    bot.add_cog(Balance(bot))
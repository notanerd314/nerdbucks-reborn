import discord
from lib import database as db

class Events(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        print("NerdBucks is ready!")
        print("R to reload extensions")

    @discord.Cog.listener()
    async def on_disconnect(self):
        db.close_connection()

def setup(bot: discord.Bot):
    bot.add_cog(Events(bot))
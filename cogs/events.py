import discord

class Events(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        print("[NerdBucks is ready!]")

def setup(bot: discord.Bot):
    bot.add_cog(Events(bot))
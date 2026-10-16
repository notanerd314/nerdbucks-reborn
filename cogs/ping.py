import discord
from discord.ui import Container, DesignerView, Section, TextDisplay, Thumbnail

class Ping(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(
        name="ping",
        description="all discord bots have this"
    )
    async def ping(self, ctx: discord.ApplicationContext):
        latency = round(self.bot.latency * 1000)
        
        view = DesignerView()
        view.add_item(
            Container(
                Section(
                    TextDisplay(f"# Pong!\n**Latency:** `{latency}ms`"),
                    accessory=Thumbnail(
                        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT9NOUAn5ffT57TkgqMyQNZ7U_2HbgXVD-GV5OdEUUtUQ&s=10"
                    ),
                )
            )
        )

        await ctx.respond(view=view)

def setup(bot):
    bot.add_cog(Ping(bot))
import discord

class Ping(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(
        name="ping",
        description="all discord bots have this"
    )
    async def ping(self, ctx: discord.ApplicationContext):
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="Pong!",
            description=f"**Latency:** `{latency}ms`",
            color=15548997
        )

        embed.set_thumbnail(
            url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT9NOUAn5ffT57TkgqMyQNZ7U_2HbgXVD-GV5OdEUUtUQ&s=10"
        )

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Ping(bot))
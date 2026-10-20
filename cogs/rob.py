import discord
from lib import database as db

import random
import discord
from discord.ui import (
    DesignerView
)

class RobView(DesignerView):
    def __init__(self, ctx: discord.ApplicationContext, target: discord.User):
        super().__init__(timeout=40.0)

        self.ctx = ctx
        self.target = target

class Rob(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(name="rob", description="Rob someone, isn't that self explanatory?")
    @discord.option("user", discord.User, required=False, description="choose an user to rob, leave blank for random")
    async def rob(self, ctx: discord.ApplicationContext, user: discord.User | None = None):
        # choose a random mf
        if not user:
            user_id = db.choose_random_user("wallet", 100)
            if user_id is None:
                await ctx.respond("this server full of brokies, cant choose a random dude")
                return
            
            try:
                user = await self.bot.fetch_user(user_id)
            except discord.NotFound:
                await ctx.respond("the dude our algorithm picked doesnt exist, tough luck")
                return

        # if robbing yourself
        if user.id == ctx.author.id:
            db.change_amount(ctx.author.id, -100, "wallet")
            await ctx.respond("since you like robbing yourself so much i just took 100 bucks off your wallet")
            return

        # check if user is broke
        data = db.get_user(user.id)
        if data["wallet"] < 100:
            await ctx.respond("the dude you chose is broke (less than a hundred bucks), leave them alone mf")
            return

        pass
        
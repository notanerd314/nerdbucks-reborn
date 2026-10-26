from lib import database as db

import random
import discord
import asyncio
from discord.ui import (
    DesignerView,
    Container,
    TextDisplay,
    MediaGallery,
    Separator
)
from lib import emojis
from lib import util

MESSAGES = {
    "success": [
        "{a} stole {b}'s ass!",
        "{b} is too gullible and got stolen by {a}.",
        "{b} fucked up big time and got stolen by {a}.",
        "{a} robbed {b}!",
        "{b} slept away while {a} stole the cash.",
        "{b} thought life was fair and was robbed by {a}."
    ],
    "failed": [
        "{a} fucked up and got beaten by {b}!",
        "{a} tried to rob {b}.",
        "{b} turned on the lights and kicked {a}'s ass!",
        "{a} unsuccessfully robbed {b}.",
        "{a} got caught lacking by {b}.",
        "{a} committed a sin and didn't repent."
    ]
}

class RobView(DesignerView):
    def __init__(self, ctx: discord.ApplicationContext, target: discord.User):
        super().__init__()

        self.ctx = ctx
        self.target = target
        self.finished = False

        self.dice = None
        self.success = None
        self.amount = None

        self.add_item(self.build())

    async def start(self):
        await asyncio.sleep(5)

        self.roll()
        self.finished = True
        self.clear_items()
        self.add_item(self.build())

        await self.ctx.edit(view=self)

    def build(self):
        if not self.finished:
            container = Container(
                TextDisplay(
                    "# Rob"
                ),
                TextDisplay(f"**{self.ctx.author.display_name}** is robbing **{self.target.display_name}**!"),
                MediaGallery(
                    discord.MediaGalleryItem("https://tenor.com/view/angry-birds-gif-12007401521632546156")
                )
            )
        else:
            if self.success:
                container = Container(
                    TextDisplay(
                        "# Rob Successful"
                    ),
                    TextDisplay(
                        f"{random.choice(MESSAGES['success']).format(a=self.ctx.author.display_name, b=self.target.display_name)} \n"
                    ),
                    Separator(),
                    TextDisplay(
                        f"**Rolled a** {self.dice} 🎲 \n"
                        f"**Stole** {self.amount} {emojis.NERDBUCKS}"
                    ),
                    MediaGallery(
                        discord.MediaGalleryItem("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS9cqfES8cfJwrFyIR0K-shi7U3YGQqyFUnTJvtPXYnRbcJxVv-LeyGdWw&s=10")
                    )
                )
            else:
                container = Container(
                    TextDisplay(
                        "# Rob Failed"
                    ),
                    TextDisplay(
                        f"{random.choice(MESSAGES['failed']).format(a=self.ctx.author.display_name, b=self.target.display_name)} \n"
                    ),
                    Separator(),
                    TextDisplay(
                        f"**Rolled a** {self.dice} 🎲 \n"
                        f"**Lost** {self.amount} {emojis.NERDBUCKS}"
                    ),
                    MediaGallery(
                        discord.MediaGalleryItem("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcREZs7vt-Z2mSpS_bCT8XCvM_g869ckJUkvlM2AV2mslQ&s=10")
                    )
                )

        return container

    def roll(self):
        threshold = 3
        self.dice = random.randint(1, 6)

        target = db.get_user(self.target.id)
        robber = db.get_user(self.ctx.author.id)

        if self.dice > threshold:
            self.success = True
            self.amount = max(100, min(5000, int(target["wallet"] * 0.1)))

            db.transfer_user(self.target.id, self.ctx.author.id, "wallet", self.amount)
        else:
            self.success = False
            self.amount = max(100, min(4500, int(robber["wallet"] * 0.12)))
            db.transfer_user(self.ctx.author.id, self.target.id, "wallet", self.amount)


class Rob(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(name="rob", description="Rob someone, isn't that self explanatory?")
    async def rob(self, ctx: discord.ApplicationContext):
        on_cooldown, remaining = db.is_on_cooldown(ctx.author.id, "beg", 30 * 60)
        if on_cooldown:
            await ctx.respond(f"there are other ways. wait `{util.pretty_time(remaining)}`")
            return
        
        user: discord.User | None = None

        # choose a random mf
        user_id = db.choose_random_user("wallet", 100, [ctx.author.id])
        if user_id is None:
            await ctx.respond("this server full of brokies, cant choose a dude")
            return
        
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:
            await ctx.respond("the dude our algorithm picked doesnt exist, tough luck")
            return

        db.set_cooldown(ctx.author.id, "rob")

        view = RobView(ctx, user)

        await ctx.respond(view=view)
        await view.start()

def setup(bot: discord.Bot):
    bot.add_cog(Rob(bot))
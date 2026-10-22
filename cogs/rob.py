import discord
from lib import database as db

import random
import discord
from discord.ui import (
    DesignerView,
    Container,
    TextDisplay,
    MediaGallery,
    Separator
)
from lib import emojis

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
        super().__init__(timeout=40.0)

        self.ctx = ctx
        self.target = target
        self.finished = False

        self.dice = None
        self.success = None
        self.amount = None

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
        else:
            self.success = False
            self.amount = max(100, min(4500, int(robber["wallet"] * 0.12)))


class Rob(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    # @discord.slash_command(name="rob", description="Rob someone, isn't that self explanatory?")
    async def rob(self, ctx: discord.ApplicationContext):
        user: discord.User | None = None

        # choose a random mf
        user_id = db.choose_random_user("wallet", 100)
        if user_id is None:
            await ctx.respond("this server full of brokies, cant choose a random dude")
            return
        
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:
            await ctx.respond("the dude our algorithm picked doesnt exist, tough luck")
            return

def setup(bot: discord.Bot):
    bot.add_cog(Rob(bot))
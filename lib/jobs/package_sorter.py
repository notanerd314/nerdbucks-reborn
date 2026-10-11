import asyncio
import discord
import random
from discord.ui import (
    DesignerView,
    Container,
    TextDisplay,
    Separator,
    ActionRow,
    Button,
)
import json

with open("lib/jobs/package_sorter.json", "r") as f:
    ITEMS = json.load(f)

class PackageSorterView(DesignerView):
    def __init__(self, ctx: discord.ApplicationContext):
        # Disable the built-in timeout; we manage the 15-second timer ourselves.
        super().__init__(timeout=30)

        self.ctx = ctx
        self.correct = 0
        self.incorrect = 0
        self.pay = 0
        self.correct_category = None
        self.finished = False

        # main() awaits this Future to receive the final pay.
        self.result = asyncio.get_running_loop().create_future()

        self.add_item(self.build())

    async def finish_game(self):
        """Finish the game and return its final pay through the Future."""
        if self.finished:
            return

        self.finished = True

        if not self.result.done():
            self.result.set_result(self.pay)

        # Disable further interaction after the game ends.
        self.clear_items()
        self.stop()

    async def on_package_click(
        self,
        interaction: discord.Interaction,
        chosen: str,
    ):
        if interaction.user is None or interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "not your game jackass",
                ephemeral=True,
            )
            return

        if self.finished:
            await interaction.response.send_message(
                "the game's already over, move on",
                ephemeral=True,
            )
            return

        if chosen == self.correct_category:
            self.correct += 1
            self.pay += random.randint(20, 45)
        else:
            self.incorrect += 1
            self.pay = max(0, self.pay - random.randint(10, 25))

        self.clear_items()
        self.add_item(self.build())

        await interaction.response.edit_message(
            content=None,
            view=self,
        )

    def generate_round(self):
        item = random.choice(list(ITEMS.keys()))
        correct_category = ITEMS[item]

        categories = list(set(ITEMS.values()))
        categories.remove(correct_category)
        incorrect_categories = random.sample(categories, 3)

        options = [correct_category] + incorrect_categories
        random.shuffle(options)

        return item, correct_category, options

    def build(self):
        self.item, self.correct_category, self.options = self.generate_round()

        container = Container(
            TextDisplay(
                "# Item Sorter\n"
                "Sort the current item to the correct category as fast as possible.\n"
                "You have **20** seconds."
            ),
            Separator(),
            TextDisplay(f"Current Item:\n## {self.item}"),
            TextDisplay(
                f"✅ **Correct:** {self.correct}    "
                f"❌ **Incorrect:** {self.incorrect}    "
                f"💵 **Pay:** ${self.pay}"
            ),
            Separator(),
            colour=discord.Colour.nitro_pink(),
        )

        buttons = []

        for option in self.options:
            button = Button(
                label=option,
                style=discord.ButtonStyle.primary,
            )

            button.callback = (
                lambda interaction, chosen=option:
                self.on_package_click(interaction, chosen)
            )

            buttons.append(button)

        container.add_item(ActionRow(*buttons))

        return container


async def main(ctx: discord.ApplicationContext) -> int:
    """Run the minigame and return the final pay after 15 seconds."""
    view = PackageSorterView(ctx)

    # Send the minigame.
    await ctx.respond(view=view)
    asyncio.create_task(finish_after_delay(view, 20))

    return await view.result

async def finish_after_delay(view: PackageSorterView, seconds: int):
    await asyncio.sleep(seconds)
    await view.finish_game()
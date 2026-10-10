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

ITEMS = {
    # 🍎 Food
    "🍎 Apple": "🍎 Food",
    "🍞 Bread": "🍎 Food",
    "🍕 Pizza": "🍎 Food",
    "🧀 Cheese": "🍎 Food",
    "🍉 Watermelon": "🍎 Food",
    "🍌 Banana": "🍎 Food",
    "🥪 Sandwich": "🍎 Food",
    "🍩 Donut": "🍎 Food",
    "🍣 Sushi": "🍎 Food",
    "🍫 Chocolate Bar": "🍎 Food",

    # 🔧 Tools
    "🔨 Hammer": "🔧 Tools",
    "🪛 Screwdriver": "🔧 Tools",
    "🔧 Wrench": "🔧 Tools",
    "🪚 Saw": "🔧 Tools",
    "🪏 Shovel": "🔧 Tools",
    "🗜️ Pliers": "🔧 Tools",
    "🛠️ Drill": "🔧 Tools",
    "📏 Measuring Tape": "🔧 Tools",
    "🔩 Crowbar": "🔧 Tools",
    "🖌️ Paintbrush": "🔧 Tools",

    # 👕 Clothing
    "👕 T-shirt": "👕 Clothing",
    "👖 Jeans": "👕 Clothing",
    "🧥 Hoodie": "👕 Clothing",
    "🧦 Socks": "👕 Clothing",
    "👟 Sneakers": "👕 Clothing",
    "🧥 Jacket": "👕 Clothing",
    "🩳 Shorts": "👕 Clothing",
    "🧤 Gloves": "👕 Clothing",
    "🧣 Scarf": "👕 Clothing",
    "🧢 Baseball Cap": "👕 Clothing",

    # 📱 Electronics
    "📱 Phone": "📱 Electronics",
    "💻 Laptop": "📱 Electronics",
    "⌨️ Keyboard": "📱 Electronics",
    "🎧 Headphones": "📱 Electronics",
    "📺 Television": "📱 Electronics",
    "🖱️ Mouse": "📱 Electronics",
    "📹 Webcam": "📱 Electronics",
    "🧮 Calculator": "📱 Electronics",
    "🎮 Game Controller": "📱 Electronics",
    "💾 USB Drive": "📱 Electronics",

    # 📚 Books & Stationery
    "📓 Notebook": "📚 Books & Stationery",
    "✏️ Pencil": "📚 Books & Stationery",
    "🩹 Eraser": "📚 Books & Stationery",
    "📘 Textbook": "📚 Books & Stationery",
    "📎 Stapler": "📚 Books & Stationery",
    "📏 Ruler": "📚 Books & Stationery",
    "🖊️ Marker": "📚 Books & Stationery",
    "✂️ Scissors": "📚 Books & Stationery",
    "✉️ Envelope": "📚 Books & Stationery",
    "🗒️ Sticky Notes": "📚 Books & Stationery",

    # 🪑 Furniture
    "🪑 Chair": "🪑 Furniture",
    "🖥️ Desk": "🪑 Furniture",
    "🛋️ Sofa": "🪑 Furniture",
    "📚 Bookshelf": "🪑 Furniture",
    "🛏️ Bed": "🪑 Furniture",
    "🚪 Wardrobe": "🪑 Furniture",
    "☕ Coffee Table": "🪑 Furniture",
    "🗄️ Nightstand": "🪑 Furniture",
    "🪑 Stool": "🪑 Furniture",
    "🍽️ Dining Table": "🪑 Furniture",

    # 🧴 Household Supplies
    "🧼 Soap": "🧴 Household Supplies",
    "🧽 Sponge": "🧴 Household Supplies",
    "🫧 Detergent": "🧴 Household Supplies",
    "🧻 Toilet Paper": "🧴 Household Supplies",
    "🗑️ Trash Bag": "🧴 Household Supplies",
    "🧹 Broom": "🧴 Household Supplies",
    "🪣 Mop": "🧴 Household Supplies",
    "🧴 Dishwashing Liquid": "🧴 Household Supplies",
    "🌬️ Air Freshener": "🧴 Household Supplies",
    "🧻 Paper Towels": "🧴 Household Supplies",

    # 🧸 Toys & Games
    "🧸 Teddy Bear": "🧸 Toys & Games",
    "🧱 LEGO Bricks": "🧸 Toys & Games",
    "♟️ Chess Set": "🧸 Toys & Games",
    "🪀 Yo-yo": "🧸 Toys & Games",
    "🦆 Rubber Duck": "🧸 Toys & Games",
    "🚗 Toy Car": "🧸 Toys & Games",
    "🧩 Puzzle": "🧸 Toys & Games",
    "🃏 Playing Cards": "🧸 Toys & Games",
    "🥏 Frisbee": "🧸 Toys & Games",
    "🤖 Toy Robot": "🧸 Toys & Games",

    # 🌿 Plants & Gardening
    "🪴 Flower Pot": "🌿 Plants & Gardening",
    "🌵 Cactus": "🌿 Plants & Gardening",
    "🌱 Seeds": "🌿 Plants & Gardening",
    "🚿 Watering Can": "🌿 Plants & Gardening",
    "🌿 Fertilizer": "🌿 Plants & Gardening",
    "🧤 Garden Gloves": "🌿 Plants & Gardening",
    "✂️ Pruning Shears": "🌿 Plants & Gardening",
    "💦 Plant Mister": "🌿 Plants & Gardening",
    "🌷 Flower Bulbs": "🌿 Plants & Gardening",
    "🪴 Garden Hose": "🌿 Plants & Gardening",
}

class PackageSorterView(DesignerView):
    def __init__(self, ctx: discord.ApplicationContext):
        # Disable the built-in timeout; we manage the 15-second timer ourselves.
        super().__init__(timeout=None)

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
            colour=discord.Colour(0x57F287),
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

    view.message = await ctx.interaction.original_response()
    asyncio.create_task(finish_after_delay(view, 20))

    return await view.result


async def finish_after_delay(view: PackageSorterView, seconds: int):
    await asyncio.sleep(seconds)
    await view.finish_game()
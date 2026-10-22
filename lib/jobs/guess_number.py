import asyncio
import math
import random

import discord
from lib.emojis import NERDBUCKS
from discord.ui import (
    ActionRow,
    Button,
    Container,
    DesignerView,
    InputText,
    Modal,
    Separator,
    TextDisplay,
)


MAX_PAY = 450
MAX_GUESSES_FOR_PAYOUT = 15
RANGE = 200

def calculate_pay(guess_count: int) -> int:
    """Reduce the reward along a normalized reverse-log curve."""
    if guess_count <= 1:
        return MAX_PAY

    progress = math.log(guess_count) / math.log(MAX_GUESSES_FOR_PAYOUT)
    return max(0, round(MAX_PAY * (1 - progress)))


class GuessNumberView(DesignerView):
    def __init__(self, ctx: discord.ApplicationContext):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.target = random.randint(0, 200)
        self.guesses = 0
        self.pay = 0
        self.finished = False
        self.status = "Open the guess form to make your first attempt."
        self.result: asyncio.Future[int | None] = (
            asyncio.get_running_loop().create_future()
        )
        self.add_item(self.build())

    def build(self) -> Container:
        container = Container(
            TextDisplay(
                "# Guess the Number\n"
                f"Phonk Industries is cracking a code, they only know the range is **0 to {RANGE}**. Can you help?\n"
                f"**Guesses:** {self.guesses}          "
                f"💵 **Pay:** {calculate_pay(max(1, self.guesses))} {NERDBUCKS}"
            ),
            Separator(),
            TextDisplay(self.status),
        )

        if not self.finished:
            guess_button = Button(
                label="Guess",
                style=discord.ButtonStyle.secondary,
            )
            guess_button.callback = self.open_guess_modal
            container.add_item(ActionRow(guess_button))

        return container

    async def respond_ephemeral(
        self,
        interaction: discord.Interaction,
        message: str,
    ):
        await interaction.response.send_message(message, ephemeral=True)

    async def is_active_player(self, interaction: discord.Interaction) -> bool:
        if interaction.user is None or interaction.user.id != self.ctx.author.id:
            await self.respond_ephemeral(interaction, "not your game jackass")
            return False

        if self.finished:
            await self.respond_ephemeral(interaction, "move on, it already ended")
            return False

        return True

    async def refresh_message(self):
        self.clear_items()
        self.add_item(self.build())
        await self.ctx.interaction.edit_original_response(view=self)

    async def open_guess_modal(self, interaction: discord.Interaction):
        if not await self.is_active_player(interaction):
            return

        await interaction.response.send_modal(GuessNumberModal(self))

    async def submit_guess(
        self,
        interaction: discord.Interaction,
        raw_guess: str | None,
    ):
        if not await self.is_active_player(interaction):
            return

        try:
            guess = int(raw_guess or "")
        except ValueError:
            await self.respond_ephemeral(
                interaction,
                f"Enter a whole number from 0 to {RANGE}.",
            )
            return

        if not 0 <= guess <= RANGE:
            await self.respond_ephemeral(
                interaction,
                f"Your guess must be from 0 to {RANGE}.",
            )
            return

        self.guesses += 1
        if guess < self.target:
            self.status = f"**{guess}** is too low."
        elif guess > self.target:
            self.status = f"**{guess}** is too high."
        else:
            self.finished = True
            self.pay = calculate_pay(self.guesses)
            self.status = (
                f"Correct! The number was **{self.target}**. "
                f"You guessed it in **{self.guesses}** attempts and earned **{self.pay} {NERDBUCKS}**."
            )

        await interaction.response.defer()
        await self.refresh_message()

        if self.finished:
            if not self.result.done():
                self.result.set_result(self.pay)
            self.stop()

    async def on_timeout(self):
        self.finished = True
        self.status = f"Time is up. The number was **{self.target}**."
        
        if not self.result.done():
            self.result.set_result(0)
        try:
            await self.refresh_message()
        except discord.HTTPException:
            pass

        self.stop()


class GuessNumberModal(Modal):
    def __init__(self, game: GuessNumberView):
        self.game = game
        self.guess_input = InputText(
            label=f"Your guess (0-{RANGE})",
            placeholder="Enter a whole number, eg. 67",
            min_length=1,
            max_length=len(str(RANGE)),
        )
        super().__init__(
            self.guess_input,
            title="Guess the Number",
            timeout=120,
        )

    async def callback(self, interaction: discord.Interaction):
        await self.game.submit_guess(interaction, self.guess_input.value)


async def main(ctx: discord.ApplicationContext) -> int | None:
    """Run the number guessing game and return its payout when completed."""
    view = GuessNumberView(ctx)
    await ctx.respond(view=view)
    return await view.result
import asyncio
import random
from pathlib import Path

import discord
from discord.ui import (
    ActionRow,
    Button,
    Container,
    DesignerView,
    MediaGallery,
    Separator,
    TextDisplay,
)

import lib.database as db
import lib.emojis as emojis
import lib.util as util


CrewMember = discord.Member | discord.User

CREW_SIZE = 3
COOLDOWN = 60 * 60

WORD_LENGTH = 5
BASE_CHANCE = 30
CHANCE_DECAY = 0.85
RESULT_DELAY = 2


HEIST_MESSAGES = {
    "success": [
        "The crew robbed {}'s ass!",
        "The heist was successful and {} left crying.",
        "{} forgot the bank wasn't always safe.",
        "Don't worry, {} can always get the money back!",
        "{} just funded the crew's retirement.",
        "The vault has been liberated. {} has not.",
        "{} got financially violated.",
        "The crew walked in broke and walked out richer. {} did the opposite.",
        "Another successful day of professional unemployment.",
        "{}'s bank account just experienced character development.",
        "The security system was apparently decorative.",
        "{} should probably change banks.",
        "The crew has successfully committed financial tomfoolery.",
        "{} just became the crew's biggest sponsor.",
        "The vault is empty. The crew is happy. {} is not.",
        "Somebody check on {}'s financial advisor.",
        "The crew pulled off the impossible. {} pulled up the banking app.",
        "Another victory for organized unemployment.",
        "{} unknowingly donated to the crew's charity.",
        "The crew has left the building. So has {}'s money.",
    ],

    "failed": [
        "{}'s bank caught the crew.",
        "The crew fucked up big time.",
        "Seems like the crew forgot how banks work.",
        "The crew has been promoted to unpaid volunteers.",
        "Somebody clearly skipped the planning phase.",
        "The crew walked in confident and left broke.",
        "The bank sends its regards.",
        "The crew successfully donated to {}.",
        "That was certainly one of the heists of all time.",
        "The crew has discovered the consequences of incompetence.",
        "Turns out the vault doesn't open with confidence.",
        "The bank staff are laughing in the break room.",
        "The only thing stolen was everyone's time.",
        "The crew should consider a career change.",
        "At least the crew got some exercise.",
    ],
}


WORDLE_DIR = Path(__file__).resolve().parent.parent / "lib" / "wordle"


def load_words(filename: str) -> list[str]:
    with (WORDLE_DIR / filename).open(encoding="utf-8") as file:
        words = (line.strip().lower() for line in file)
        return [word for word in words if len(word) == WORD_LENGTH]


ANSWERS = load_words("answers.txt")
VALID_WORDS = set(load_words("valid.txt"))


def clamp(value: float, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def evaluate_guess(guess: str, answer: str) -> list[str]:
    """Wordle scoring: 🟩 correct, 🟨 misplaced, ⬛ absent."""
    result = ["⬛"] * WORD_LENGTH
    unmatched: dict[str, int] = {}

    for i, (letter, correct) in enumerate(zip(guess, answer)):
        if letter == correct:
            result[i] = "🟩"
        else:
            unmatched[correct] = unmatched.get(correct, 0) + 1

    for i, letter in enumerate(guess):
        if result[i] == "⬛" and unmatched.get(letter, 0):
            result[i] = "🟨"
            unmatched[letter] -= 1

    return result


class GuessModal(discord.ui.Modal):
    def __init__(self, heist: "HeistView"):
        super().__init__(title="Submit a guess")
        self.heist = heist

        self.guess = discord.ui.InputText(
            label=f"Enter a {WORD_LENGTH}-letter word",
            min_length=WORD_LENGTH,
            max_length=WORD_LENGTH,
        )
        self.add_item(self.guess)

    async def callback(self, interaction: discord.Interaction):
        await self.heist.submit_guess(interaction, self.guess.value or "")


class HeistView(DesignerView):
    """Wordle challenge, then the heist outcome."""

    def __init__(
        self,
        ctx: discord.ApplicationContext,
        crew: list[CrewMember],
        target: CrewMember,
    ):
        super().__init__(timeout=900)

        self.ctx = ctx
        self.crew = random.sample(crew, len(crew))
        self.target = target

        self.answer = random.choice(ANSWERS)
        self.history: list[tuple[CrewMember, str, list[str]]] = []
        self.turn = 0
        self.chance = BASE_CHANCE
        self.finished = False
        self.timed_out = False
        self.status = "Proceeding with the heist..."

        self.refresh()

    @property
    def player(self) -> CrewMember:
        return self.crew[self.turn]

    # ── display ──

    def refresh(self):
        self.clear_items()
        self.add_item(self.build())

    def build(self) -> Container:
        history = "\n".join(
            f"`{guess.upper()}` {''.join(result)} — {player.display_name}"
            for player, guess, result in self.history[-12:]
        ) or "*No attempts yet.*"

        if self.timed_out:
            return Container(TextDisplay(
                "# Heist Abandoned\n"
                "The crew took too long and the heist fell apart.\n\n"
                f"**Password:** `{self.answer.upper()}`\n"
                f"**Total guesses:** {len(self.history)}\n\n"
                f"{history}"
            ))

        if self.finished:
            return Container(TextDisplay(
                "# Wordle Solved\n"
                f"**{self.status}**\n\n"
                f"**Password:** `{self.answer.upper()}`\n"
                f"**Total guesses:** {len(self.history)}\n"
                f"**Heist success chance:** {self.chance:.1f}%\n\n"
                f"{history}"
            ))

        container = Container(TextDisplay(
            "# Wordle\n"
            "Crack the vault password! Take turns guessing a five-letter word. "
            "The fewer guesses it takes, the better your odds of pulling off the heist.\n\n"
            "🟩 right letter, right spot\n"
            "🟨 right letter, wrong spot\n"
            "⬛ letter not in the word\n\n"
            f"**Current player:** {self.player.mention}\n"
            f"**Total guesses:** {len(self.history)}\n\n"
            f"{history}"
        ))

        button = Button(
            label="Submit Guess",
            style=discord.ButtonStyle.primary,
        )
        button.callback = self.on_submit_click
        container.add_item(ActionRow(button))

        return container

    # ── guesses ──

    async def check_turn(self, interaction: discord.Interaction) -> bool:
        if self.finished:
            message = "The challenge is already complete."
        elif interaction.user is None:
            message = "Unable to identify the player taking this turn."
        elif interaction.user.id != self.player.id:
            message = f"It's {self.player.display_name}'s turn!"
        else:
            return True

        await interaction.response.send_message(message, ephemeral=True)
        return False

    async def on_submit_click(self, interaction: discord.Interaction):
        if await self.check_turn(interaction):
            await interaction.response.send_modal(GuessModal(self))

    async def submit_guess(self, interaction: discord.Interaction, guess: str):
        if not await self.check_turn(interaction):
            return

        player = self.player
        guess = guess.strip().lower()

        if guess not in VALID_WORDS:
            await interaction.response.send_message(
                "Not a valid word.",
                ephemeral=True,
            )
            return

        self.history.append(
            (player, guess, evaluate_guess(guess, self.answer))
        )

        if guess != self.answer:
            self.turn = (self.turn + 1) % len(self.crew)
            self.refresh()
            await interaction.response.edit_message(view=self)
            return

        self.finished = True
        self.chance = BASE_CHANCE + (
            (100 - BASE_CHANCE) * CHANCE_DECAY ** (len(self.history) - 1)
        )

        self.refresh()
        await interaction.response.edit_message(view=self)

        await asyncio.sleep(RESULT_DELAY)

        success, total, share = self.resolve()

        self.refresh()
        await interaction.edit_original_response(view=self)

        await interaction.followup.send(
            view=HeistResultView(self.target, success, total, share)
        )

    async def on_timeout(self):
        if self.finished:
            return

        self.finished = True
        self.timed_out = True
        self.refresh()

        try:
            await self.ctx.interaction.edit_original_response(view=self)
        except discord.HTTPException:
            pass

    # ── outcome ──

    def resolve(self) -> tuple[bool, int, int]:
        """Roll against the success chance, transfer the money, return the results."""

        crew_size = len(self.crew)

        if random.random() * 100 < self.chance:
            bank = db.get_user(self.target.id)["bank"]
            share = clamp(bank * 0.15, 100, 10000) // crew_size

            for member in self.crew:
                db.transfer_user(
                    self.target.id,
                    member.id,
                    "bank",
                    share,
                )

            return True, share * crew_size, share

        crew_bank = sum(
            db.get_user(member.id)["bank"]
            for member in self.crew
        )

        share = clamp(crew_bank * 0.20, 100, 8500) // crew_size

        for member in self.crew:
            db.transfer_user(
                member.id,
                self.target.id,
                "bank",
                share,
            )

        return False, share * crew_size, share


class HeistResultView(DesignerView):
    def __init__(
        self,
        target: CrewMember,
        success: bool,
        total: int,
        share: int,
    ):
        super().__init__()

        self.target = target
        self.success = success
        self.total = total
        self.share = share

        self.add_item(self.build())

    def build(self) -> Container:
        if self.success:
            primary = random.choice(HEIST_MESSAGES["success"]).format(
                self.target.display_name
            )

            return Container(
                TextDisplay("# Bank Heist Successful"),
                TextDisplay(
                    f"{primary}\n\n"
                    f"**Total stolen:** {self.total:,} {emojis.NERDBUCKS}\n"
                    f"**Per crew member:** {self.share:,} {emojis.NERDBUCKS}"
                ),
                Separator(),
                MediaGallery(
                    discord.MediaGalleryItem(
                        "https://media.gettyimages.com/id/1399933347/photo/gang-of-robber-tries-to-enter-vault-with-a-welding-torch.jpg?s=612x612&w=gi&k=20&c=kOucNdEu_wuLovwrYODnscFX0gMnnhFeSKjc0-OFkh4="
                    )
                ),
            )

        primary = random.choice(HEIST_MESSAGES["failed"]).format(
            self.target.display_name
        )

        return Container(
            TextDisplay("# Bank Heist Failed"),
            TextDisplay(
                f"{primary}\n\n"
                f"**Total lost:** {self.total:,} {emojis.NERDBUCKS}\n"
                f"**Per crew member:** {self.share:,} {emojis.NERDBUCKS}"
            ),
            Separator(),
            MediaGallery(
                discord.MediaGalleryItem(
                    "https://t4.ftcdn.net/jpg/06/20/48/65/360_F_620486523_GruOPyrGnCROTuUunMaqV4lLikMKcVo5.jpg"
                )
            ),
        )


class HeistLobby(DesignerView):
    """Collects players, then starts the Wordle challenge."""

    def __init__(
        self,
        ctx: discord.ApplicationContext,
        target: CrewMember,
    ):
        super().__init__(timeout=120)

        self.ctx = ctx
        self.target = target
        self.players: list[CrewMember] = [ctx.author]
        self.finished = False
        self.status = "Waiting for more players..."

        self.refresh()

    def refresh(self):
        self.clear_items()

        roster = "\n".join(
            f"{i}. {player.display_name}"
            for i, player in enumerate(self.players, 1)
        )

        container = Container(TextDisplay(
            "# Bank Heist\n"
            f"**Target:** {self.target.display_name}\n\n"
            "**How it works**\n"
            f"1. Click **Join Heist** until the crew is full ({CREW_SIZE} players).\n"
            "2. Solve a Wordle together, taking turns guessing.\n"
            "3. Fewer guesses means a higher chance of success.\n"
            "4. Win and the crew splits money stolen from the target's bank. "
            "Lose and the crew pays the target instead.\n\n"
            f"**Crew ({len(self.players)}/{CREW_SIZE})**\n"
            f"{roster}\n\n"
            f"{self.status}"
        ))

        if not self.finished:
            button = Button(
                label="Join Heist",
                style=discord.ButtonStyle.primary,
            )
            button.callback = self.on_join
            container.add_item(ActionRow(button))

        self.add_item(container)

    async def on_join(self, interaction: discord.Interaction):
        player = interaction.user

        if player is None:
            message = "Unable to identify the player joining this heist."

        elif self.finished:
            message = "This heist is no longer open."

        elif any(member.id == player.id for member in self.players):
            message = "You're already in this crew."

        elif player.id == self.target.id:
            message = "You can't join a heist against yourself."

        else:
            on_cooldown, remaining = db.is_on_cooldown(
                player.id,
                "heist",
                COOLDOWN,
            )

            if on_cooldown:
                await interaction.response.send_message(
                    f"You need to wait `{util.pretty_time(remaining)}`.",
                    ephemeral=True,
                )
                return

            self.players.append(player)
            db.set_cooldown(player.id, "heist")

            if len(self.players) >= CREW_SIZE:
                self.finished = True
                self.stop()

                await interaction.response.edit_message(
                    view=HeistView(self.ctx, self.players, self.target)
                )
                return

            self.refresh()
            await interaction.response.edit_message(view=self)
            return

        await interaction.response.send_message(message, ephemeral=True)

    async def on_timeout(self):
        if self.finished:
            return

        self.finished = True
        self.status = "The lobby expired before the crew was assembled."
        self.refresh()

        try:
            await self.ctx.interaction.edit_original_response(view=self)
        except discord.HTTPException:
            pass


class Heist(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(
        name="heist",
        description="Start a bank heist.",
    )
    @discord.option(
        "target",
        discord.User,
        required=True,
        description="Who are you robbing?",
    )
    async def heist(
        self,
        ctx: discord.ApplicationContext,
        target: discord.User,
    ):
        if target.bot or target.id == ctx.author.id:
            await ctx.respond("Invalid target.", ephemeral=True)
            return

        on_cooldown, remaining = db.is_on_cooldown(
            ctx.author.id,
            "heist",
            COOLDOWN,
        )

        if on_cooldown:
            await ctx.respond(
                f"there are other ways. wait `{util.pretty_time(remaining)}`"
            )
            return

        db.set_cooldown(ctx.author.id, "heist")
        await ctx.respond(view=HeistLobby(ctx, target))


def setup(bot: discord.Bot):
    bot.add_cog(Heist(bot))
import asyncio
import html
import random
import requests
import discord
from lib.emojis import NERDBUCKS
from discord.ui import (
    DesignerView,
    Container,
    TextDisplay,
    Separator,
    ActionRow,
    Button,
)


def fetch_questions(amount: int = 5) -> list[dict[str, str | list[str]]]:
    """Fetch and normalize mixed multiple-choice and true/false questions."""
    response = requests.get(
        "https://opentdb.com/api.php",
        params={"amount": amount},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("response_code") != 0:
        raise ValueError(
            f"Open Trivia Database returned response code "
            f"{payload.get('response_code')}"
        )

    questions = []
    for result in payload["results"]:
        answer = html.unescape(result["correct_answer"])
        options = [html.unescape(option) for option in result["incorrect_answers"]]
        options.append(answer)
        random.shuffle(options)

        questions.append(
            {
                "type": (
                    "true_false"
                    if result["type"] == "boolean"
                    else "multiple_choice"
                ),
                "question": html.unescape(result["question"]),
                "options": options,
                "answer": answer,
            }
        )

    return questions

class TriviaView(DesignerView):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        questions: list[dict[str, str | list[str]]],
    ):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.questions = questions
        self.question_index = 0
        self.correct = 0
        self.incorrect = 0
        self.pay = 0
        self.result: asyncio.Future[int | None] = (
            asyncio.get_running_loop().create_future()
        )

        self.add_item(self.build())

    async def on_timeout(self):
        if not self.result.done():
            self.result.set_result(None)

    async def on_answer(
        self,
        interaction: discord.Interaction,
        selected_answer: str,
        question_index: int,
    ):
        if interaction.user is None or interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "not your game jackass",
                ephemeral=True,
            )
            return

        if question_index != self.question_index:
            await interaction.response.send_message(
                "move on, it already ended",
                ephemeral=True,
            )
            return

        question = self.questions[question_index]
        if selected_answer == question["answer"]:
            self.correct += 1
            self.pay += random.randint(60, 75)
        else:
            self.incorrect += 1

        self.question_index += 1
        self.clear_items()
        self.add_item(self.build())
        await interaction.response.edit_message(view=self)

        if self.question_index >= len(self.questions):
            if not self.result.done():
                self.result.set_result(self.pay)
            self.stop()

    def build(self) -> Container:
        total_questions = len(self.questions)
        if self.question_index >= total_questions:
            return Container(
                TextDisplay(
                    "# Trivia Complete\n"
                    "Welcome to the **Israel Intellectual Agency**! "
                    f"You answered all **{total_questions}** questions.\n"
                    f"✅ **Correct:** {self.correct}       "
                    f"❌ **Incorrect:** {self.incorrect}        "
                    f"💵 **Pay:** {self.pay} {NERDBUCKS}"
                ),
            )

        question = self.questions[self.question_index]
        question_number = self.question_index + 1

        container = Container(
            TextDisplay(
                "# Trivia\n"
                "Welcome to the **Israel Intellectual Agency**! "
                f"Answer these **{total_questions}** questions below.\n"
                f"✅ **Correct:** {self.correct}    "
                f"❌ **Incorrect:** {self.incorrect}    "
                f"💵 **Pay:** {self.pay} {NERDBUCKS}"
            ),
            Separator(),
            TextDisplay(
                f"-# Question **{question_number}** of {total_questions}\n"
                f"## {question['question']}"
            ),
        )

        answer_buttons = []
        for option in question["options"]:
            button = Button(
                label=option,
                style=discord.ButtonStyle.secondary,
            )
            button.callback = (
                lambda interaction, answer=option, index=self.question_index:
                self.on_answer(interaction, answer, index)
            )
            answer_buttons.append(button)

        container.add_item(ActionRow(*answer_buttons))
        return container


async def main(ctx: discord.ApplicationContext) -> int | None:
    """Run a trivia game using questions from Open Trivia Database."""
    try:
        questions = await asyncio.to_thread(fetch_questions, 5)
    except (requests.RequestException, ValueError, KeyError) as error:
        print(f"Failed to fetch trivia questions: {error}")
        await ctx.respond(
            "my dumbass server lagged and i cant fetch the fuckin' questions, try again",
            ephemeral=True,
        )
        return

    if not questions:
        await ctx.respond(
            "my dumbass server lagged and i cant fetch the fuckin' questions, try again",
            ephemeral=True,
        )
        return

    view = TriviaView(ctx, questions)

    await ctx.respond(view=view)
    return await view.result

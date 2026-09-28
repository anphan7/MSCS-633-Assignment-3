"""Build and train the ChatterBot conversational engine.

ChatterBot is a machine-learning based dialog engine: it stores known
statement/response pairs, then answers new input by finding the closest
known statement and returning one of its recorded responses.

Both front ends in this project (the console client and the Django web app)
call `getChatBot()`, so they share one trained database and give the same
answers.
"""

from __future__ import annotations

from pathlib import Path

from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer

# Display name reported by the bot.
BOT_NAME = "MSCS-633 Assistant"

# The trained knowledge base lives next to the project, not inside this
# package, so it sits alongside Django's own db.sqlite3.
DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent.parent / "chatbot.sqlite3"

# ChatterBot's bundled English training data (supplied by chatterbot-corpus).
ENGLISH_CORPUS = "chatterbot.corpus.english"

# Returned when no stored statement is a close enough match to the input.
DEFAULT_RESPONSE = "I'm sorry, I don't understand. Could you rephrase that?"

# Extra conversations trained on top of the English corpus. Each list is read
# as an alternating exchange: item 0 is an input, item 1 is the response to it,
# item 2 is the response to item 1, and so on. The first list is the sample
# exchange given in the assignment.
CUSTOM_CONVERSATIONS = [
    [
        "Good morning! How are you doing?",
        "I am doing very well, thank you for asking.",
        "You're welcome.",
        "Do you like hats?",
    ],
    [
        "Hello",
        "Hello! How can I help you today?",
        "I have a question.",
        "Sure, go ahead and ask.",
    ],
    [
        "What is your name?",
        f"My name is {BOT_NAME}.",
    ],
    [
        "What can you do?",
        "I can hold a simple conversation using responses I was trained on.",
    ],
    [
        "Goodbye",
        "Goodbye! Have a great day.",
    ],
]

# Cache of the bot built by `getChatBot()`. Training is slow relative to
# answering, so the Django app must not rebuild the bot on every request.
_cachedBot: ChatBot | None = None


def buildChatBot(databasePath: Path | None = None, readOnly: bool = True) -> ChatBot:
    """Create a ChatBot wired to the SQLite knowledge base at `databasePath`.

    Args:
        databasePath: SQLite file holding the trained statements. Defaults to
            `DEFAULT_DATABASE_PATH`. It is created if it does not exist.
        readOnly: When True the bot does not learn from what users type. This
            keeps the web app's answers reproducible and stops untrusted input
            from being written into the knowledge base.

    Returns:
        A ChatBot instance. It is *not* trained yet - call `trainChatBot()`,
        or use `getChatBot()`, which handles training for you.
    """
    databasePath = databasePath or DEFAULT_DATABASE_PATH

    # The storage adapter expects a SQLAlchemy URL, not a bare path. Four
    # slashes after "sqlite:" denote an absolute file path.
    databasePath.parent.mkdir(parents=True, exist_ok=True)
    databaseUri = f"sqlite:///{databasePath}"

    return ChatBot(
        BOT_NAME,
        database_uri=databaseUri,
        read_only=readOnly,
        logic_adapters=[
            {
                # BestMatch picks the stored statement closest to the input.
                "import_path": "chatterbot.logic.BestMatch",
                # Stop searching once a match this similar is found; below this
                # the adapter's confidence drops and the default is used.
                "maximum_similarity_threshold": 0.90,
                "default_response": DEFAULT_RESPONSE,
            }
        ],
    )


def isTrained(bot: ChatBot) -> bool:
    """Return True if `bot`'s knowledge base already contains statements."""
    return bot.storage.count() > 0


def trainChatBot(bot: ChatBot, showProgress: bool = True) -> None:
    """Teach `bot` the English corpus plus the custom conversations above.

    Training is additive and idempotent in effect: re-training an already
    trained database simply re-records the same statement/response pairs.

    Args:
        bot: The ChatBot to train.
        showProgress: Whether to print ChatterBot's training progress bars.
    """
    ChatterBotCorpusTrainer(bot, show_training_progress=showProgress).train(
        ENGLISH_CORPUS
    )

    listTrainer = ListTrainer(bot, show_training_progress=showProgress)
    for conversation in CUSTOM_CONVERSATIONS:
        listTrainer.train(conversation)


def getChatBot(
    databasePath: Path | None = None,
    readOnly: bool = True,
    forceRetrain: bool = False,
) -> ChatBot:
    """Return a trained, ready-to-use ChatBot, building it only once.

    The first call builds the bot and trains it if its database is empty.
    Later calls reuse the cached instance, so answering a message does not
    pay the training cost again.

    Args:
        databasePath: SQLite file holding the trained statements.
        readOnly: See `buildChatBot()`.
        forceRetrain: Train again even if the database already has statements.

    Returns:
        A trained ChatBot.
    """
    global _cachedBot

    if _cachedBot is not None and not forceRetrain:
        return _cachedBot

    # Training writes to the database, so the bot must not be read-only while
    # it happens. Build it writable, train, then re-open with the caller's
    # chosen mode.
    bot = buildChatBot(databasePath, readOnly=False)

    if forceRetrain or not isTrained(bot):
        trainChatBot(bot)

    if readOnly:
        bot = buildChatBot(databasePath, readOnly=True)

    _cachedBot = bot
    return bot


def getResponse(message: str, **kwargs) -> str:
    """Return the bot's reply to `message` as plain text.

    Args:
        message: What the user typed.
        **kwargs: Passed through to `getChatBot()`.

    Returns:
        The bot's reply. Empty or whitespace-only input yields a prompt to
        say something rather than an arbitrary corpus match.
    """
    if not message or not message.strip():
        return "Please say something and I will reply."

    return str(getChatBot(**kwargs).get_response(message.strip()))


if __name__ == "__main__":
    # Running `python -m chatbot.bot` trains the knowledge base up front, so
    # the first web request or console prompt responds immediately.
    print(f"Training {BOT_NAME}...")
    getChatBot(forceRetrain=True)
    print(f"Done. Knowledge base: {DEFAULT_DATABASE_PATH}")

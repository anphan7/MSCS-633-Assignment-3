"""Console front end for the MSCS-633 Assignment 3 ChatterBot bot.

Produces the conversation style shown in the assignment:

    user: Good morning! How are you doing?
    bot: I am doing very well, thank you for asking.
    user: You're welcome.
    bot: Do you like hats?

Usage:
    python chat_cli.py              # chat, training first if needed
    python chat_cli.py --retrain    # rebuild the knowledge base, then chat
    python chat_cli.py --learn      # let the bot learn from this session
"""

from __future__ import annotations

import argparse
import sys

from chatbot.bot import BOT_NAME, getChatBot

# Typing any of these ends the session.
EXIT_COMMANDS = {"quit", "exit", "bye", "goodbye"}

USER_PROMPT = "user: "
BOT_PREFIX = "bot: "


def parseArguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Define and parse the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Chat with the ChatterBot bot from the terminal."
    )
    parser.add_argument(
        "--retrain",
        action="store_true",
        help="Retrain the knowledge base before chatting.",
    )
    parser.add_argument(
        "--learn",
        action="store_true",
        help="Let the bot learn from this conversation (default: it does not).",
    )
    return parser.parse_args(argv)


def runChatLoop(bot) -> None:
    """Read user input and print bot replies until the user exits.

    Ends on an exit command, on Ctrl-D (end of input), or on Ctrl-C.
    """
    while True:
        try:
            message = input(USER_PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            # Ctrl-D / Ctrl-C: finish the partial line, then stop cleanly.
            print()
            break

        if not message:
            continue

        if message.lower() in EXIT_COMMANDS:
            print(f"{BOT_PREFIX}Goodbye! Have a great day.")
            break

        print(f"{BOT_PREFIX}{bot.get_response(message)}")


def main(argv: list[str] | None = None) -> int:
    """Program entry point. Returns a shell exit code (0 = success)."""
    args = parseArguments(argv)

    # The first run trains on the English corpus, which takes a few seconds.
    print(f"Starting {BOT_NAME} (this can take a moment on first run)...")
    try:
        bot = getChatBot(readOnly=not args.learn, forceRetrain=args.retrain)
    except Exception as error:
        # Most likely causes: the spaCy model or the corpus package is
        # missing. Point at the fix rather than dumping a traceback.
        print(f"Error: could not start the chat bot - {error}", file=sys.stderr)
        print(
            "Check that setup finished: pip install -r requirements.txt "
            "and python -m spacy download en_core_web_sm",
            file=sys.stderr,
        )
        return 1

    print(f"Ready. Type {'/'.join(sorted(EXIT_COMMANDS))} to leave.\n")
    runChatLoop(bot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

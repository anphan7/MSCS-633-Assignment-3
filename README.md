# ChatterBot Conversational Dialog Engine (MSCS-633 - Assignment 3)

A chat bot built on [ChatterBot](https://pypi.org/project/ChatterBot/), a
machine-learning based conversational dialog engine that generates responses
from collections of known conversations.

The bot is exposed through two front ends that share one trained knowledge
base, so both give the same answers:

- **Console client** (`chat_cli.py`) - the terminal conversation shown in the
  assignment.
- **Django web app** (`chatbot_site/` + `chat/`) - a browser chat page.

## Requirements

- Python 3.10 - 3.14 (developed and tested on 3.12)
- Packages listed in `requirements.txt`
- The spaCy English model `en_core_web_sm`, which ChatterBot uses to tag text

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Optionally train the bot up front, so the first message answers immediately.
Both front ends do this automatically on first use if you skip it:

```bash
python -m chatbot.bot
```

Training uses ChatterBot's built-in English corpus plus the custom
conversations in `chatbot/bot.py`, and takes a few seconds.

## Usage

### Console

```bash
python chat_cli.py
```

```
$ python chat_cli.py
Starting MSCS-633 Assistant (this can take a moment on first run)...
Ready. Type bye/exit/goodbye/quit to leave.

user: Good morning! How are you doing?
bot: I am doing very well, thank you for asking.
user: You're welcome.
bot: Do you like hats?
user: bye
bot: Goodbye! Have a great day.
```

| Option | Description |
| --- | --- |
| `--retrain` | Rebuild the knowledge base before chatting |
| `--learn` | Let the bot learn from this session (off by default) |

### Web

```bash
python manage.py migrate        # first run only: sets up Django's own tables
python manage.py runserver
```

Then open <http://127.0.0.1:8000/>. See `screenshot_web.png` for the result.

## Tests

```bash
python manage.py test
```

Eight tests cover the chat page, the trained sample exchange, the fallback
response for unrecognised input, and rejection of malformed requests.

## How it works

`chatbot/bot.py` builds one `ChatBot` backed by a SQLite knowledge base and
trains it with two trainers:

- `ChatterBotCorpusTrainer` on `chatterbot.corpus.english`, the bundled
  English conversation corpus.
- `ListTrainer` on `CUSTOM_CONVERSATIONS`, hand-written exchanges that include
  the sample conversation from the assignment.

At reply time the `BestMatch` logic adapter compares the input against every
stored statement and returns a response recorded for the closest one. If
nothing scores above the similarity threshold, the bot returns
`DEFAULT_RESPONSE` rather than an unrelated corpus line.

The bot is cached after the first build and runs read-only by default, so the
web app does not retrain per request and untrusted input is never written into
the knowledge base.


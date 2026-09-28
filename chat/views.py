"""Views for the browser chat interface.

Two endpoints:
    chatPage  - renders the chat page itself.
    chatReply - JSON endpoint the page calls to get the bot's reply.

The bot itself lives in `chatbot.bot`, shared with the console client.
"""

from __future__ import annotations

import json

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from chatbot.bot import BOT_NAME, getResponse

# Guard against a single oversized request tying up the matching step.
MAX_MESSAGE_LENGTH = 500


@require_GET
def chatPage(request: HttpRequest) -> HttpResponse:
    """Render the chat page."""
    return render(request, "chat/index.html", {"botName": BOT_NAME})


@require_POST
def chatReply(request: HttpRequest) -> JsonResponse:
    """Return the bot's reply to a posted message as JSON.

    Expects a JSON body of `{"message": "..."}` and responds with
    `{"response": "..."}`. Returns HTTP 400 with an `error` key if the body
    is not valid JSON or the message is missing or too long.
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Request body must be valid JSON."}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"error": "Request body must be a JSON object."}, status=400)

    message = payload.get("message", "")

    if not isinstance(message, str):
        return JsonResponse({"error": "'message' must be a string."}, status=400)

    message = message.strip()

    if not message:
        return JsonResponse({"error": "'message' must not be empty."}, status=400)

    if len(message) > MAX_MESSAGE_LENGTH:
        return JsonResponse(
            {"error": f"'message' must be {MAX_MESSAGE_LENGTH} characters or fewer."},
            status=400,
        )

    return JsonResponse({"response": getResponse(message)})

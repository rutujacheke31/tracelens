import base64
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings


class OllamaServiceError(RuntimeError):
    """Raised when TraceLens cannot obtain a valid response from Ollama."""


def encode_image(image_path: Path) -> str:
    """Convert an image into the base64 format required by Ollama's REST API."""
    if not image_path.is_file():
        raise FileNotFoundError(
            f"Screenshot could not be found: {image_path}"
        )

    image_bytes = image_path.read_bytes()

    return base64.b64encode(image_bytes).decode("utf-8")


async def chat_with_ollama(
    prompt: str,
    image_path: Path | None = None,
    response_format: dict[str, Any] | str | None = None,
) -> str:
    """Send text and an optional screenshot to the local Ollama model."""

    # Every request contains instructions for the model.
    user_message: dict[str, Any] = {
        "role": "user",
        "content": prompt,
    }

    # Vision requests include the screenshot as base64-encoded data.
    if image_path is not None:
        user_message["images"] = [
            encode_image(image_path),
        ]

    request_body: dict[str, Any] = {
        "model": settings.ollama_model,
        "messages": [user_message],
        "stream": False,
        # Zero temperature makes debugging results more consistent.
        "options": {
            "temperature": 0,
        },
    }

    # A JSON schema forces Ollama to return a predictable structure.
    if response_format is not None:
        request_body["format"] = response_format

    chat_url = (
        f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    )

    try:
        async with httpx.AsyncClient(
            timeout=settings.ollama_timeout_seconds,
        ) as client:
            response = await client.post(
                chat_url,
                json=request_body,
            )

            response.raise_for_status()

    except httpx.ConnectError as error:
        raise OllamaServiceError(
            "TraceLens could not connect to Ollama. "
            "Make sure Ollama is installed and running."
        ) from error

    except httpx.TimeoutException as error:
        raise OllamaServiceError(
            "Ollama took too long to analyze the request."
        ) from error

    except httpx.HTTPStatusError as error:
        raise OllamaServiceError(
            "Ollama rejected the analysis request."
        ) from error

    except httpx.RequestError as error:
        raise OllamaServiceError(
            "An error occurred while communicating with Ollama."
        ) from error

    try:
        response_data = response.json()
        generated_text = response_data["message"]["content"]

    except (ValueError, KeyError, TypeError) as error:
        raise OllamaServiceError(
            "Ollama returned an invalid response."
        ) from error

    if not isinstance(generated_text, str) or not generated_text.strip():
        raise OllamaServiceError(
            "Ollama returned an empty response."
        )

    return generated_text.strip()
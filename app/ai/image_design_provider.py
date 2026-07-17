from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from typing import Any

from app.utils.settings import Settings


@dataclass(frozen=True)
class GeneratedDesignImage:
    data_url: str
    provider: str
    model: str
    mime_type: str = "image/png"


@dataclass(frozen=True)
class ImageProviderStatus:
    configured: bool
    provider: str
    model: str
    size: str
    quality: str


class ImageDesignProvider:
    """Generate product concept images behind a provider-neutral interface."""

    def is_enabled(self) -> bool:
        return bool(str(Settings.OPENAI_API_KEY or "").strip())

    def status(self) -> ImageProviderStatus:
        return ImageProviderStatus(
            configured=self.is_enabled(),
            provider="OpenAI",
            model=Settings.IMAGE_MODEL,
            size=Settings.IMAGE_SIZE,
            quality=Settings.IMAGE_QUALITY,
        )

    @staticmethod
    def _friendly_error(exc: Exception) -> str:
        """Return a concise provider error while preserving useful API details."""
        text = str(exc).strip() or type(exc).__name__
        lower = text.lower()
        if "billing_hard_limit_reached" in lower or "billing hard limit" in lower:
            return "OpenAI API billing hard limit has been reached. Update API billing or usage limits."
        if "insufficient_quota" in lower:
            return "OpenAI API quota is unavailable. Check API billing, credits, and project limits."
        if "invalid_api_key" in lower or "incorrect api key" in lower or "401" in lower:
            return "OpenAI rejected the API key. Confirm OPENAI_API_KEY belongs to the funded project."
        if "model_not_found" in lower:
            return f"OpenAI image model '{Settings.IMAGE_MODEL}' is unavailable to this project."
        return text

    @staticmethod
    def _extract_base64(result: Any) -> str:
        data = getattr(result, "data", None)
        if not data:
            raise RuntimeError("OpenAI image generation returned no image records.")
        value = getattr(data[0], "b64_json", None)
        if not value:
            raise RuntimeError("OpenAI image generation returned no base64 image data.")
        return str(value)

    def generate(self, prompt: str) -> GeneratedDesignImage:
        prompt = str(prompt or "").strip()
        if not prompt:
            raise ValueError("An image-generation prompt is required.")
        if not self.is_enabled():
            raise RuntimeError(
                "AI image generation is not configured. Add OPENAI_API_KEY to .env "
                "and restart the Streamlit dashboard."
            )

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The openai package is not installed. Run: python -m pip install -r requirements.txt"
            ) from exc

        try:
            client = OpenAI(api_key=Settings.OPENAI_API_KEY)
            result = client.images.generate(
                model=Settings.IMAGE_MODEL,
                prompt=prompt,
                size=Settings.IMAGE_SIZE,
                quality=Settings.IMAGE_QUALITY,
            )
            raw_b64 = self._extract_base64(result)
            image_bytes = base64.b64decode(raw_b64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise RuntimeError("OpenAI returned invalid base64 image data.") from exc
        except Exception as exc:
            detail = self._friendly_error(exc)
            raise RuntimeError(
                f"OpenAI image generation failed using {Settings.IMAGE_MODEL}: {detail}"
            ) from exc

        if not image_bytes:
            raise RuntimeError("OpenAI returned an empty image.")

        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        return GeneratedDesignImage(
            data_url=f"data:image/png;base64,{image_b64}",
            provider="openai",
            model=Settings.IMAGE_MODEL,
            mime_type="image/png",
        )

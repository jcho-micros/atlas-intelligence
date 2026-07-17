from __future__ import annotations

import base64
import sys
from pathlib import Path

from dotenv import load_dotenv


# Add the Atlas project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.ai.image_design_provider import ImageDesignProvider


OUTPUT_FILE = PROJECT_ROOT / "test_image.png"


def save_data_url_as_image(data_url: str, output_file: Path) -> None:
    """Decode a base64 image data URL and save it as a PNG file."""

    if not data_url:
        raise ValueError("The image provider returned an empty data URL.")

    if "," not in data_url:
        raise ValueError(
            "The image provider response is not a valid image data URL."
        )

    header, encoded_image = data_url.split(",", 1)

    if not header.startswith("data:image/"):
        raise ValueError(
            f"Unexpected data URL header: {header[:100]}"
        )

    try:
        image_bytes = base64.b64decode(
            encoded_image,
            validate=True,
        )
    except Exception as exc:
        raise ValueError(
            "The returned image contains invalid base64 data."
        ) from exc

    if not image_bytes:
        raise ValueError("The decoded image is empty.")

    output_file.write_bytes(image_bytes)


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")

    prompt = (
        "Photorealistic studio product render of a premium magnetic "
        "baseball lineup board. The board should have a professional "
        "baseball coaching design, clearly organized player positions, "
        "durable materials, magnetic name plates, and a clean premium "
        "product photography background."
    )

    print("Testing Atlas image generation...")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Output file: {OUTPUT_FILE}")
    print()

    try:
        provider = ImageDesignProvider()
        result = provider.generate(prompt)

        print("SUCCESS")
        print(f"Provider: {result.provider}")
        print(f"Model: {result.model}")
        print(
            f"Image received: "
            f"{len(result.data_url):,} characters"
        )
        print()
        print("Data URL preview:")
        print(result.data_url[:100])
        print()

        save_data_url_as_image(
            data_url=result.data_url,
            output_file=OUTPUT_FILE,
        )

        file_size = OUTPUT_FILE.stat().st_size

        print(f"Saved image: {OUTPUT_FILE}")
        print(f"Image file size: {file_size:,} bytes")
        print()
        print(
            "Open test_image.png to confirm the generated image "
            "is valid."
        )

        return 0

    except Exception as exc:
        print("IMAGE GENERATION FAILED")
        print()
        print("FULL ERROR:")
        print(repr(exc))
        print()
        print("MESSAGE:")
        print(str(exc))

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
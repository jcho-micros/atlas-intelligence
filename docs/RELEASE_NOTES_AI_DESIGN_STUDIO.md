# Atlas Enterprise v2.7.2 — AI Design Studio

## Why this release exists
The v2.7.1 SVG concepts proved the review workflow but did not produce credible product design. v2.7.2 keeps the workflow and replaces wireframe-first design with provider-backed product visualization.

## New
- OpenAI image-generation provider adapter.
- Noah creates three materially distinct industrial-design prompts.
- AI-generated photorealistic product concept images are stored directly with each design concept.
- Design Studio renders PNG data images and retains SVG fallback behavior.
- Clean material presentation in concept cards.
- Provider configuration through `.env`.

## Configuration
Add to `.env`:

```env
OPENAI_API_KEY=your_api_key
ATLAS_IMAGE_MODEL=gpt-image-1
ATLAS_IMAGE_QUALITY=medium
ATLAS_IMAGE_SIZE=1536x1024
```

Without an API key, Atlas intentionally renders a labeled local fallback so the rest of the workflow remains testable.

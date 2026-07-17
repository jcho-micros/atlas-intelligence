# Atlas Enterprise v2.7.3 — Real AI Designer Hardening

## Purpose

Remove the misleading SVG fallback from Noah's Design Studio and make AI image-provider failures explicit and actionable.

## Changes

- Real AI product image is now required before a concept can be approved for Manufacturing.
- Provider failures are persisted with the concept and displayed in the Design Studio.
- Design Studio shows provider configuration, model, image size, and quality.
- Added Retry AI Image per concept.
- Added Regenerate All AI Images for the selected project.
- Legacy v2.7.1 SVG wireframes are detected and labeled as non-approvable.
- Existing legacy concepts can be replaced with a real AI render without deleting the database.
- Removed silent fallback to placeholder triangle/rectangle SVG artwork.
- Added automated tests for successful AI design generation and explicit provider failure handling.

## Validation

`python -m pytest` => 16 passed.

## Upgrade

Keep `.env` and `data/atlas.db`. Replace project files and restart the dashboard. In Design Studio, use **Regenerate All AI Images** to replace stored legacy wireframes.

## v2.7.4 AI Image Pipeline Fix

- Replaced HTML-embedded multi-megabyte data URLs with decoded byte rendering through `st.image`.
- Added strict Base64 validation before a concept is considered approvable.
- Added friendly OpenAI billing, quota, key, and model error messages.
- Added generation spinners and disabled image actions when the provider is not configured.
- Incremented concept versions when images are retried or regenerated.
- Added stored image size and render-version visibility in Design Studio.

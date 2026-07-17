# Atlas Enterprise v2.7.0 — Design & Manufacturing Execution

## New
- Design Studio with Noah Reed as Product Designer
- Three visual SVG mockups per product project
- Design rationale, materials, dimensions, price, designer notes, and provider-ready image prompts
- CEO approve / revision / reject workflow
- Approved design package handoff to David
- Sourcing assignments and supplier recommendation engine
- Communications handoff among Noah, David, and Mia
- Supplier approval triggers Michael's Finance Intelligence recalculation
- Design & Manufacturing employee timeline

## Architecture note
v2.7 uses deterministic local SVG mockups so the workflow is testable without an image API. `image_prompt` is persisted for a future pluggable image-generation provider.

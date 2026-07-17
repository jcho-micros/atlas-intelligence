# Atlas Enterprise v2.7.1

## Design Studio SVG Rendering Fix

- Fixes `PIL.UnidentifiedImageError` when rendering locally generated SVG design mockups in Streamlit.
- Design concepts are now rendered as inline base64 SVG images instead of passing SVG bytes to `st.image`.
- Preserves Design Studio approval, revision, manufacturing handoff, and finance workflow.
- Full test suite: 13 passed.

# Atlas OS Foundation Baseline

This baseline defines the next architecture layer for Atlas: CEO Workspace, product projects, agent contracts, workflow events, and persistent agent memory.

## How to apply

Copy these folders into your existing Atlas project:

- `docs/`
- `app/os/`
- `tests/`

Then run:

```bash
python -m pytest tests/test_os_baseline.py
```

This is a foundation layer only. It does not replace your current dashboard or Etsy connector yet.

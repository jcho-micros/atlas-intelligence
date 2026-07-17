# Upgrade Guide — v1.1.0

## Recommended local upgrade

Because this release adds new business-level tables, the simplest local alpha upgrade is:

```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```

Keep your `.env` file. Do not overwrite or commit it.

## Git commit

```bash
git add .
git commit -m "Upgrade Atlas to v1.1.0 Business Engine"
git push
```

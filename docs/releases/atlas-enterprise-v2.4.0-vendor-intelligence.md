# Atlas Enterprise v2.4.0 — Vendor Intelligence

## Theme
Manufacturing becomes a real business function.

## Added
- Vendor Intelligence navigation section.
- Vendor Directory and Vendor Workspace.
- RFQ Center for supplier quote requests.
- Vendor Timeline.
- Vendor models: Vendor, VendorContact, VendorQuote, VendorEvent.
- VendorIntelligenceService with deterministic seed vendors and recommendation logic.
- Analytics queries for vendors, quotes, contacts, and vendor events.
- Tests for vendor seeding and recommendation.

## Validation
```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```

## Recommended commit
```bash
git add .
git commit -m "Add Atlas Enterprise vendor intelligence"
git push
```

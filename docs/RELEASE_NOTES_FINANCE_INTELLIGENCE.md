# Atlas Enterprise v2.6.0 — Finance Intelligence

## Theme
Atlas answers the next executive question: **can this business actually make money?**

## Added
- Finance Intelligence section in the sidebar
- Finance Workspace for business-level finance analysis
- Unit Economics view
- Profit Scenarios view
- Finance Timeline view
- FinanceAnalysis, FinanceScenario, FinanceEvent models
- FinanceIntelligenceService
- Deterministic cost stack: unit cost, packaging, shipping, marketplace fees, payment fees, ads, reserve
- Gross profit, gross margin, break-even units, target price, and monthly profit estimate
- Finance approval status: approved, review, rejected
- Michael/Finance Agent timeline events and task completion

## Validation
```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```

## Notes
This release uses deterministic assumptions so Atlas can run locally without accounting integrations. Future releases should connect Finance Intelligence to real vendor quotes, QuickBooks/Xero, Stripe, Etsy fees, shipping carriers, and ad spend.

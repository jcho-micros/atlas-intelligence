# Atlas Intelligence - Sprint 1

Local AI commerce research foundation. Sprint 1 adds:

- SQLite database
- Keyword manager
- Research queue records
- Sample marketplace connector
- Etsy connector placeholder for when credentials are approved
- Opportunity scoring
- Streamlit dashboard

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Run Dashboard

```bash
streamlit run app/dashboard/app.py
```

## Data Modes

Use sample mode until Etsy approves your API app:

```env
ATLAS_DATA_MODE=sample
```

When ready:

```env
ATLAS_DATA_MODE=etsy
ETSY_API_KEY=your_keystring_here
```

## Add Keywords

Edit `config/config.yaml`, then rerun:

```bash
python main.py
```

## Local Only

Everything runs locally. No paid service is required.

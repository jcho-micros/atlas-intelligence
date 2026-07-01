# Atlas Intelligence v0.2.0

Local-first commerce intelligence platform for researching product opportunities.

## Setup

```bash
python -m venv .venv
source .venv/Scripts/activate  # Git Bash on Windows
python -m pip install -r requirements.txt
cp .env.example .env
```

## Run sample research

```bash
python main.py
```

or

```bash
python atlas.py research
```

## Dashboard

```bash
python atlas.py dashboard
```

## Etsy mode

Update `.env`:

```env
ATLAS_DATA_MODE=etsy
ETSY_API_KEY=your_keystring
ETSY_SHARED_SECRET=your_secret
```

Then run:

```bash
python main.py
```

Never commit `.env`.

# Atlas Enterprise v2.5.0 — Communications Hub

## Theme
The Communications Hub becomes the nervous system of Atlas Enterprise.

## Added
- First-class conversations
- Conversation participants
- Conversation messages
- Communication actions and follow-ups
- Communications Center dashboard section
- Vendor conversation/RFQ draft workflow
- Customer conversation foundation
- Communications service for seeding and routing local conversations

## Validation
```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```

## Navigation
New section:

- 📬 Communications
  - Communications Center
  - Vendor Conversations
  - Customer Conversations
  - Communication Actions

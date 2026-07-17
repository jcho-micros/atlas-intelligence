# Atlas Enterprise v2.6.2

## Compatibility Fix

- Restores Communications Hub ORM models alongside Finance Intelligence models.
- Fixes pytest collection imports for `CommunicationAction`, `Conversation`, and `FinanceAnalysis`.
- Preserves `expire_on_commit=False` session behavior used by Streamlit approval actions.
- No database deletion is required for test validation. Existing SQLite databases may still require schema migration if the new tables were never created.

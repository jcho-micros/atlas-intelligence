# Atlas Enterprise v2.6.1

## Communications model recovery

This patch restores the Communications Hub ORM models required by `CommunicationsService` and `tests/test_communications_hub.py`:

- `Conversation`
- `ConversationParticipant`
- `ConversationMessage`
- `CommunicationAction`

The missing model definitions caused pytest collection to fail with `ImportError: cannot import name CommunicationAction`.

## Validation

`python -m pytest -q` passes all 11 tests.

Fresh local databases remain supported through `DatabaseManager.initialize()` / SQLAlchemy metadata creation.

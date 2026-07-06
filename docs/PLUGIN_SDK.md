# Atlas Plugin SDK Draft

Atlas should eventually support plugins for marketplaces, agents, and external business systems.

## Connector Interface

```python
class MarketplaceConnector:
    name: str

    def search(self, keyword: str, limit: int = 25):
        ...
```

## Agent Interface

```python
class AtlasAgent:
    name: str
    skills: list[str]

    def can_handle(self, task_type: str) -> bool:
        return task_type in self.skills

    def execute(self, task):
        ...
```

## Future Plugin Types

- Marketplace connectors
- Manufacturing connectors
- Shipping connectors
- Accounting connectors
- Customer service connectors
- AI model providers

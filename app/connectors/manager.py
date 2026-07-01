from app.connectors.etsy import EtsyConnector
from app.connectors.sample import SampleConnector


class ConnectorManager:
    def __init__(self):
        self._connectors = {
            "sample": SampleConnector,
            "etsy": EtsyConnector,
        }

    def get_connector(self, name: str):
        connector_name = name.lower().strip()
        if connector_name not in self._connectors:
            available = ", ".join(sorted(self._connectors.keys()))
            raise ValueError(f"Unknown connector '{name}'. Available connectors: {available}")
        return self._connectors[connector_name]()

    def available_connectors(self) -> list[str]:
        return sorted(self._connectors.keys())

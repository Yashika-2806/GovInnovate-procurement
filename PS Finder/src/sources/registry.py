import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type

from src.models.source import AuthorityLevel, SourceRegistryEntry
from src.sources.base import SourceAdapter

logger = logging.getLogger(__name__)


class SourceRegistry:
    """Manages registered official sources and adapter instantiation."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent / "registry.json"
        self._adapters: Dict[str, SourceAdapter] = {}
        self._adapter_classes: Dict[str, Type[SourceAdapter]] = {}

    def register_adapter_class(self, name: str, adapter_cls: Type[SourceAdapter]):
        """Register adapter implementation class by name."""
        self._adapter_classes[name] = adapter_cls

    def load_sources(self) -> List[SourceRegistryEntry]:
        """Load sources from configuration JSON."""
        if not self.config_path.exists():
            logger.warning(f"Registry file {self.config_path} not found.")
            return []

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [SourceRegistryEntry(**item) for item in data if item.get("enabled", True)]
        except Exception as e:
            logger.error(f"Error loading source registry: {e}")
            return []

    def get_adapter(self, source_entry: SourceRegistryEntry) -> Optional[SourceAdapter]:
        """Get or instantiate adapter for given source entry."""
        if source_entry.source_id in self._adapters:
            return self._adapters[source_entry.source_id]

        adapter_cls = self._adapter_classes.get(source_entry.adapter)
        if not adapter_cls:
            logger.warning(f"No adapter class registered for '{source_entry.adapter}'")
            return None

        adapter_instance = adapter_cls(source_entry)
        self._adapters[source_entry.source_id] = adapter_instance
        return adapter_instance

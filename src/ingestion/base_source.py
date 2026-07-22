# ==============================================================================
# Abstract Traffic Data Source Interface (src/ingestion/base_source.py)
# Base Class Specification for Offline Lab & Online TomTom Data Sources
# ==============================================================================

from abc import ABC, abstractmethod
from typing import Any, List, Dict


class TrafficDataSource(ABC):
    """
    Abstract Base Class defining standard interface for all traffic data sources.
    """

    @abstractmethod
    def read(self) -> List[Dict[str, Any]]:
        """
        Abstract method to read and normalize traffic records into a list of dictionaries.

        Returns:
            List[Dict[str, Any]]: Normalized traffic records matching UNIFIED_RAW_TRAFFIC_SCHEMA.
        """
        pass

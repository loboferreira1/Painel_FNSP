"""TI impact dashboard package."""

from .config import DashboardConfig
from .contracts import validate_portaria_schema, validate_relation_schema

__all__ = [
    "DashboardConfig",
    "validate_portaria_schema",
    "validate_relation_schema",
]

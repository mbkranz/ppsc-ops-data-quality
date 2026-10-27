"""Domain-independent schema conversion; application profiles live with their queries."""

from .ddl import schema_from_ddl

__all__ = ["schema_from_ddl"]

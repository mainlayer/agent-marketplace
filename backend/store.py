"""
In-memory agent store.

In production replace this with a database (Postgres, SQLite, etc.).
The store is a plain dict keyed by agent_id so all routes share state
within a single process.
"""

from typing import Any

# agent_id -> agent record dict
agent_store: dict[str, Any] = {}

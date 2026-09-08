"""
In-memory data store.

This prototype intentionally has NO real database. Every "table" is a plain
Python dict keyed by id, guarded by a lock for thread safety under Uvicorn's
threadpool. Data lives only for the lifetime of the process — restarting the
server wipes everything.

Swapping this for PostgreSQL later means replacing this module with
SQLAlchemy repositories; the service layer above it is written against
simple get/list/create/update calls so that swap should not touch
controllers or business logic.
"""

import threading
from typing import Any, Callable, Optional
from uuid import uuid4


class InMemoryTable:
    def __init__(self):
        self._data: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self, record: dict[str, Any], id_field: str = "id") -> dict[str, Any]:
        with self._lock:
            record_id = record.get(id_field) or str(uuid4())
            record[id_field] = record_id
            self._data[record_id] = record
            return record

    def get(self, record_id: str) -> Optional[dict[str, Any]]:
        return self._data.get(record_id)

    def find_one(self, predicate: Callable[[dict[str, Any]], bool]) -> Optional[dict[str, Any]]:
        for record in self._data.values():
            if predicate(record):
                return record
        return None

    def find_all(self, predicate: Callable[[dict[str, Any]], bool]) -> list[dict[str, Any]]:
        return [record for record in self._data.values() if predicate(record)]

    def all(self) -> list[dict[str, Any]]:
        return list(self._data.values())

    def update(self, record_id: str, changes: dict[str, Any]) -> Optional[dict[str, Any]]:
        with self._lock:
            record = self._data.get(record_id)
            if record is None:
                return None
            record.update(changes)
            return record

    def delete(self, record_id: str) -> bool:
        with self._lock:
            return self._data.pop(record_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


class Store:
    """Namespace holding every in-memory table (the prototype's 'database')."""

    def __init__(self):
        self.users = InMemoryTable()
        self.sessions = InMemoryTable()
        self.metrics = InMemoryTable()
        self.interactions = InMemoryTable()
        self.screenshots = InMemoryTable()
        self.ai_reports = InMemoryTable()

    def reset(self) -> None:
        for table in (
            self.users,
            self.sessions,
            self.metrics,
            self.interactions,
            self.screenshots,
            self.ai_reports,
        ):
            table.clear()


store = Store()

"""Table access with two backends behind one small interface.

- SqlTable: SQLAlchemy over a direct database connection (DATABASE_URL).
  Used locally, in Docker and in tests.
- RestTable: Supabase's REST API (PostgREST) over HTTPS. Used when
  SUPABASE_URL and SUPABASE_KEY are set, e.g. on PythonAnywhere's free plan,
  which blocks database connections but allows HTTPS to *.supabase.co.

Both return rows as plain dicts keyed by column name, with datetimes as
datetime objects, so the stores (crud.py, users.py, recruiters.py) hold all
the logic once and work with either backend.
"""
from datetime import datetime
from typing import Optional, Union

import httpx
from pydantic import TypeAdapter
from sqlalchemy import DateTime, exists, select
from sqlalchemy.orm import Session


# PostgREST trims trailing zeros from fractional seconds ("12:29:33.79421"),
# which datetime.fromisoformat rejects before Python 3.11; pydantic parses any ISO form.
_parse_datetime = TypeAdapter(datetime).validate_python


def _columns(model) -> list:
    return list(model.__table__.columns)


class SqlTable:
    def __init__(self, session: Session, model):
        self.session = session
        self.model = model

    def _to_dict(self, row) -> dict:
        return {c.key: getattr(row, c.key) for c in _columns(self.model)}

    def _find(self, filters: dict):
        return self.session.scalar(select(self.model).filter_by(**filters).limit(1))

    def get(self, **filters) -> Optional[dict]:
        row = self._find(filters)
        return self._to_dict(row) if row else None

    def all(self) -> list:
        return [self._to_dict(row) for row in self.session.scalars(select(self.model))]

    def exists(self) -> bool:
        return bool(self.session.scalar(select(exists().select_from(self.model))))

    def insert(self, values: dict) -> dict:
        row = self.model(**values)
        self.session.add(row)
        self.session.commit()
        return self._to_dict(row)

    def update(self, values: dict, **filters) -> Optional[dict]:
        row = self._find(filters)
        if not row:
            return None
        for key, value in values.items():
            setattr(row, key, value)
        self.session.commit()
        return self._to_dict(row)

    def delete(self, **filters) -> bool:
        row = self._find(filters)
        if not row:
            return False
        self.session.delete(row)
        self.session.commit()
        return True


class SupabaseError(RuntimeError):
    pass


class SupabaseRest:
    """A thin client for Supabase's REST API. One per process; thread-safe."""

    # Supabase returns at most 1000 rows per request by default
    PAGE_SIZE = 1000

    def __init__(self, url: str, key: str, timeout: float = 10.0, rest_path: str = "/rest/v1"):
        headers = {"apikey": key}
        # Legacy keys (anon/service_role) are JWTs and also go in Authorization.
        # New secret keys (sb_secret_...) must only be sent as apikey.
        if key.startswith("eyJ"):
            headers["Authorization"] = f"Bearer {key}"
        # trust_env (the default) makes httpx use the https_proxy that
        # PythonAnywhere sets for free accounts.
        self.http = httpx.Client(
            base_url=url.rstrip("/") + rest_path, headers=headers, timeout=timeout
        )

    def request(self, method: str, table: str, **kwargs) -> httpx.Response:
        response = self.http.request(method, f"/{table}", **kwargs)
        if response.status_code >= 400:
            # PostgREST explains the problem in the body; the key is never included
            raise SupabaseError(
                f"Supabase {method} /{table} failed ({response.status_code}): {response.text[:300]}"
            )
        return response

    def close(self):
        self.http.close()


class RestTable:
    RETURN_ROWS = {"Prefer": "return=representation"}

    def __init__(self, client: SupabaseRest, model):
        self.client = client
        self.name = model.__tablename__
        self.datetime_columns = [c.key for c in _columns(model) if isinstance(c.type, DateTime)]
        self.first_key = model.__table__.primary_key.columns.values()[0].key

    @staticmethod
    def _filters(filters: dict) -> dict:
        return {key: f"eq.{value}" for key, value in filters.items()}

    def _encode(self, values: dict) -> dict:
        return {k: v.isoformat() if isinstance(v, datetime) else v for k, v in values.items()}

    def _decode(self, row: dict) -> dict:
        for key in self.datetime_columns:
            if isinstance(row.get(key), str):
                row[key] = _parse_datetime(row[key])
        return row

    def get(self, **filters) -> Optional[dict]:
        rows = self.client.request(
            "GET", self.name, params={"select": "*", "limit": 1, **self._filters(filters)}
        ).json()
        return self._decode(rows[0]) if rows else None

    def all(self) -> list:
        rows, offset = [], 0
        while True:
            page = self.client.request(
                "GET", self.name,
                params={"select": "*", "order": self.first_key,
                        "limit": self.client.PAGE_SIZE, "offset": offset},
            ).json()
            rows.extend(page)
            if len(page) < self.client.PAGE_SIZE:
                return [self._decode(row) for row in rows]
            offset += len(page)

    def exists(self) -> bool:
        rows = self.client.request(
            "GET", self.name, params={"select": self.first_key, "limit": 1}
        ).json()
        return bool(rows)

    def insert(self, values: dict) -> dict:
        rows = self.client.request(
            "POST", self.name, json=self._encode(values), headers=self.RETURN_ROWS
        ).json()
        return self._decode(rows[0])

    def update(self, values: dict, **filters) -> Optional[dict]:
        if not values:
            return self.get(**filters)
        rows = self.client.request(
            "PATCH", self.name, params=self._filters(filters),
            json=self._encode(values), headers=self.RETURN_ROWS,
        ).json()
        return self._decode(rows[0]) if rows else None

    def delete(self, **filters) -> bool:
        rows = self.client.request(
            "DELETE", self.name, params=self._filters(filters), headers=self.RETURN_ROWS
        ).json()
        return bool(rows)


Database = Union[Session, SupabaseRest]
Table = Union[SqlTable, RestTable]


def table(db: Database, model) -> Table:
    """Access one table through whichever backend `db` is"""
    if isinstance(db, SupabaseRest):
        return RestTable(db, model)
    return SqlTable(db, model)

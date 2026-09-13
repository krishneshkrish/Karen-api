import logging
import sqlite3
import os
from functools import lru_cache
from typing import Any, List, Dict, Optional, Union
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "karen_local.db")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_local_schema():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_hash TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_hash TEXT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            topic TEXT,
            final_severity TEXT DEFAULT 'low',
            turn_count INT DEFAULT 0
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_hash TEXT NOT NULL,
            dominant_emotion TEXT,
            severity TEXT,
            severity_score REAL,
            topic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ml_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emotion TEXT,
            severity TEXT,
            topic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()


# Initialize schema on module import
try:
    init_local_schema()
except Exception as e:
    logger.warning(f"Failed to initialize local SQLite schema: {e}")


class FallbackResponse:
    def __init__(self, data: Any):
        self.data = data


class ResilientQueryBuilder:
    def __init__(self, conn: sqlite3.Connection, table_name: str, real_builder: Any = None):
        self.conn = conn
        self.table_name = table_name
        self.real_builder = real_builder
        self._action = "select"
        self._select_cols = "*"
        self._where_clauses: List[str] = []
        self._where_params: List[Any] = []
        self._order_by: Optional[str] = None
        self._desc: bool = False
        self._limit: Optional[int] = None
        self._single: bool = False
        self._data_to_save: Optional[Union[Dict, List[Dict]]] = None

    def select(self, cols: str = "*"):
        if self.real_builder is not None:
            try:
                self.real_builder = self.real_builder.select(cols)
            except Exception:
                self.real_builder = None
        self._action = "select"
        self._select_cols = cols
        return self

    def insert(self, data: Union[Dict, List[Dict]]):
        if self.real_builder is not None:
            try:
                self.real_builder = self.real_builder.insert(data)
            except Exception:
                self.real_builder = None
        self._action = "insert"
        self._data_to_save = data
        return self

    def upsert(self, data: Union[Dict, List[Dict]]):
        if self.real_builder is not None:
            try:
                self.real_builder = self.real_builder.upsert(data)
            except Exception:
                self.real_builder = None
        self._action = "upsert"
        self._data_to_save = data
        return self

    def eq(self, column: str, value: Any):
        if self.real_builder is not None:
            try:
                self.real_builder = self.real_builder.eq(column, value)
            except Exception:
                self.real_builder = None
        self._where_clauses.append(f"{column} = ?")
        self._where_params.append(value)
        return self

    def order(self, column: str, desc: bool = False):
        if self.real_builder is not None:
            try:
                self.real_builder = self.real_builder.order(column, desc=desc)
            except Exception:
                self.real_builder = None
        self._order_by = column
        self._desc = desc
        return self

    def limit(self, count: int):
        if self.real_builder is not None:
            try:
                self.real_builder = self.real_builder.limit(count)
            except Exception:
                self.real_builder = None
        self._limit = count
        return self

    def single(self):
        if self.real_builder is not None:
            try:
                self.real_builder = self.real_builder.single()
            except Exception:
                self.real_builder = None
        self._single = True
        return self

    def execute(self) -> FallbackResponse:
        # Attempt real Supabase execution first
        if self.real_builder is not None:
            try:
                res = self.real_builder.execute()
                return res
            except Exception as e:
                logger.warning(
                    f"Supabase query execution failed on '{self.table_name}' ({e}). "
                    "Transparently falling back to local SQLite database."
                )

        # Fallback local SQLite execution
        cursor = self.conn.cursor()

        if self._action == "insert" or self._action == "upsert":
            items = self._data_to_save if isinstance(self._data_to_save, list) else [self._data_to_save]
            for item in items:
                if not item:
                    continue
                # Clean null values if needed
                filtered_item = {k: v for k, v in item.items() if v is not None}
                keys = list(filtered_item.keys())
                placeholders = ["?"] * len(keys)
                values = [filtered_item[k] for k in keys]

                cmd = "INSERT OR REPLACE" if self._action == "upsert" else "INSERT OR IGNORE"
                sql = f"{cmd} INTO {self.table_name} ({', '.join(keys)}) VALUES ({', '.join(placeholders)})"
                cursor.execute(sql, values)
            self.conn.commit()
            return FallbackResponse(data=items)

        elif self._action == "select":
            cols = self._select_cols.strip()
            # Handle comma-separated column selection
            if cols != "*":
                # Ensure clean column names
                col_names = [c.strip() for c in cols.split(",")]
                select_clause = ", ".join(col_names)
            else:
                select_clause = "*"

            sql = f"SELECT {select_clause} FROM {self.table_name}"
            if self._where_clauses:
                sql += " WHERE " + " AND ".join(self._where_clauses)
            if self._order_by:
                direction = "DESC" if self._desc else "ASC"
                sql += f" ORDER BY {self._order_by} {direction}"
            if self._limit is not None:
                sql += f" LIMIT {self._limit}"

            cursor.execute(sql, self._where_params)
            rows = [dict(r) for r in cursor.fetchall()]

            if self._single:
                if not rows:
                    raise Exception(f"No row found in '{self.table_name}' matching criteria")
                return FallbackResponse(data=rows[0])

            return FallbackResponse(data=rows)

        return FallbackResponse(data=[])


class ResilientSupabaseClient:
    def __init__(self, real_client: Optional[Client]):
        self.real_client = real_client

    def table(self, table_name: str) -> ResilientQueryBuilder:
        real_builder = None
        if self.real_client is not None:
            try:
                real_builder = self.real_client.table(table_name)
            except Exception:
                real_builder = None
        return ResilientQueryBuilder(get_db_connection(), table_name, real_builder)


@lru_cache
def get_supabase() -> ResilientSupabaseClient:
    """Initialize and return resilient Supabase client instance with SQLite local fallback."""
    real_client = None
    try:
        real_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    except Exception as e:
        logger.warning(f"Unable to initialize cloud Supabase client ({e}). Local SQLite store active.")
    return ResilientSupabaseClient(real_client)

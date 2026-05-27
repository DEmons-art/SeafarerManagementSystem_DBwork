from __future__ import annotations

import os
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import pymysql
from pymysql.cursors import DictCursor


DEFAULT_DATABASE_URL = (
    "mysql+pymysql://root:123456@127.0.0.1:3306/SeafarerDB?charset=utf8mb4"
)

# 业务层用它来识别“唯一约束冲突”（账号/身份证重复）
DatabaseIntegrityError = pymysql.err.IntegrityError


def get_database_url() -> str:
    return os.getenv("SEAFARER_DATABASE_URL", DEFAULT_DATABASE_URL)


class DbConnection:
    """对单个 MySQL 连接的轻量封装，统一增删改查与事务接口。"""

    def __init__(self, connection: Any):
        self._connection = connection

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self._connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with self._connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.rowcount

    def insert(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with self._connection.cursor() as cursor:
            cursor.execute(sql, params)
            return int(cursor.lastrowid)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()


class Database:
    """按 DATABASE_URL 建立 MySQL 连接。"""

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or get_database_url()

    def connect(self) -> DbConnection:
        parsed = urlparse(self.database_url)
        charset = parse_qs(parsed.query).get("charset", ["utf8mb4"])[0]
        connection = pymysql.connect(
            host=parsed.hostname or "127.0.0.1",
            port=parsed.port or 3306,
            user=unquote(parsed.username or "root"),
            password=unquote(parsed.password or ""),
            database=unquote(parsed.path.lstrip("/")),
            charset=charset,
            cursorclass=DictCursor,
            autocommit=False,
        )
        return DbConnection(connection)

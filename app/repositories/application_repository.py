"""Database operations for submitted loan applications."""

import json
import sqlite3
import time
from pathlib import Path


class ApplicationRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS applications("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT NOT NULL,"
            "created REAL NOT NULL,payload TEXT NOT NULL,result TEXT NOT NULL)"
        )
        return connection

    def save(self, email, payload, result):
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO applications(email,created,payload,result) VALUES(?,?,?,?)",
                (email.lower(), time.time(), json.dumps(payload), json.dumps(result)),
            )

    def history(self, email):
        with self._connect() as connection:
            return connection.execute(
                "SELECT created,payload,result FROM applications "
                "WHERE email=? ORDER BY created DESC",
                (email.lower(),),
            ).fetchall()

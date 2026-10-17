"""
database.py — SQLite database manager for the Voice Form Filling System.
Handles all CRUD operations, schema creation, search, and backup.
"""

import sqlite3
import shutil
import logging
import os
from datetime import datetime
from config import DB_PATH, DB_DIR, REPORTS_DIR

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages the SQLite database for user registration records."""

    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.db_path = DB_PATH
        self.create_table()
        logger.info("DatabaseManager initialised. DB: %s", self.db_path)

    # ─────────────────────────────────────────
    # Connection helper
    # ─────────────────────────────────────────
    def _connect(self):
        """Return a new SQLite connection with row_factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    # ─────────────────────────────────────────
    # Schema
    # ─────────────────────────────────────────
    def create_table(self):
        """Create the Users table if it does not exist."""
        sql = """
        CREATE TABLE IF NOT EXISTS Users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            age         INTEGER NOT NULL,
            gender      TEXT    NOT NULL,
            phone       TEXT    NOT NULL,
            email       TEXT    NOT NULL,
            address     TEXT    NOT NULL,
            occupation  TEXT    NOT NULL,
            reg_date    TEXT    NOT NULL,
            reg_time    TEXT    NOT NULL
        );
        """
        try:
            with self._connect() as conn:
                conn.execute(sql)
                conn.commit()
            logger.debug("Table 'Users' verified/created.")
        except sqlite3.Error as exc:
            logger.error("create_table error: %s", exc)
            raise

    # ─────────────────────────────────────────
    # Insert
    # ─────────────────────────────────────────
    def insert_user(self, data: dict) -> int:
        """
        Insert a new user record.

        Parameters
        ----------
        data : dict
            Keys: name, age, gender, phone, email, address, occupation

        Returns
        -------
        int
            Row ID of the inserted record.
        """
        now = datetime.now()
        sql = """
        INSERT INTO Users (name, age, gender, phone, email, address, occupation, reg_date, reg_time)
        VALUES (:name, :age, :gender, :phone, :email, :address, :occupation, :reg_date, :reg_time)
        """
        data["reg_date"] = now.strftime("%Y-%m-%d")
        data["reg_time"] = now.strftime("%H:%M:%S")

        try:
            with self._connect() as conn:
                cursor = conn.execute(sql, data)
                conn.commit()
                row_id = cursor.lastrowid
                logger.info("Inserted user ID=%d  Name=%s", row_id, data.get("name"))
                return row_id
        except sqlite3.Error as exc:
            logger.error("insert_user error: %s", exc)
            raise

    # ─────────────────────────────────────────
    # Read
    # ─────────────────────────────────────────
    def get_all_users(self) -> list:
        """Return all user records as a list of dicts."""
        sql = "SELECT * FROM Users ORDER BY id DESC"
        try:
            with self._connect() as conn:
                rows = conn.execute(sql).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as exc:
            logger.error("get_all_users error: %s", exc)
            return []

    def get_user_by_id(self, user_id: int) -> dict | None:
        """Return a single user dict by ID, or None."""
        sql = "SELECT * FROM Users WHERE id = ?"
        try:
            with self._connect() as conn:
                row = conn.execute(sql, (user_id,)).fetchone()
                return dict(row) if row else None
        except sqlite3.Error as exc:
            logger.error("get_user_by_id error: %s", exc)
            return None

    def search_users(self, query: str) -> list:
        """
        Search users by name, email, or phone (case-insensitive, partial match).

        Parameters
        ----------
        query : str
            The search term.
        """
        term = f"%{query}%"
        sql = """
        SELECT * FROM Users
        WHERE name  LIKE :q
           OR email LIKE :q
           OR phone LIKE :q
           OR occupation LIKE :q
        ORDER BY id DESC
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, {"q": term}).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as exc:
            logger.error("search_users error: %s", exc)
            return []

    # ─────────────────────────────────────────
    # Update
    # ─────────────────────────────────────────
    def update_user(self, user_id: int, data: dict) -> bool:
        """
        Update an existing user record.

        Parameters
        ----------
        user_id : int
        data    : dict  (name, age, gender, phone, email, address, occupation)
        """
        sql = """
        UPDATE Users
        SET name=:name, age=:age, gender=:gender, phone=:phone,
            email=:email, address=:address, occupation=:occupation
        WHERE id=:id
        """
        data["id"] = user_id
        try:
            with self._connect() as conn:
                conn.execute(sql, data)
                conn.commit()
                logger.info("Updated user ID=%d", user_id)
                return True
        except sqlite3.Error as exc:
            logger.error("update_user error: %s", exc)
            return False

    # ─────────────────────────────────────────
    # Delete
    # ─────────────────────────────────────────
    def delete_user(self, user_id: int) -> bool:
        """Delete a user record by ID."""
        sql = "DELETE FROM Users WHERE id = ?"
        try:
            with self._connect() as conn:
                conn.execute(sql, (user_id,))
                conn.commit()
                logger.info("Deleted user ID=%d", user_id)
                return True
        except sqlite3.Error as exc:
            logger.error("delete_user error: %s", exc)
            return False

    # ─────────────────────────────────────────
    # Statistics
    # ─────────────────────────────────────────
    def get_stats(self) -> dict:
        """
        Return summary statistics for the dashboard.

        Returns
        -------
        dict
            total_users, today_registrations, latest_user
        """
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with self._connect() as conn:
                total = conn.execute("SELECT COUNT(*) FROM Users").fetchone()[0]
                today_count = conn.execute(
                    "SELECT COUNT(*) FROM Users WHERE reg_date = ?", (today,)
                ).fetchone()[0]
                latest_row = conn.execute(
                    "SELECT name, reg_date FROM Users ORDER BY id DESC LIMIT 1"
                ).fetchone()
                latest = dict(latest_row) if latest_row else None
            return {
                "total_users":          total,
                "today_registrations":  today_count,
                "latest_user":          latest,
            }
        except sqlite3.Error as exc:
            logger.error("get_stats error: %s", exc)
            return {"total_users": 0, "today_registrations": 0, "latest_user": None}

    # ─────────────────────────────────────────
    # Backup
    # ─────────────────────────────────────────
    def backup_database(self) -> str:
        """
        Copy the database file to the reports folder with a timestamp.

        Returns
        -------
        str
            Path to the backup file.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(REPORTS_DIR, f"form_backup_{ts}.db")
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info("Database backed up to %s", backup_path)
            return backup_path
        except Exception as exc:
            logger.error("backup_database error: %s", exc)
            raise

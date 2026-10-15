import sqlite3
import time
from pathlib import Path
from typing import Literal
from functools import wraps

Path("db").mkdir(exist_ok=True)

_conn = sqlite3.connect("db/db.sqlite3")
_conn.execute("PRAGMA foreign_keys = ON")
_conn.row_factory = sqlite3.Row

migrations = Path("db/migrations")
migrations.mkdir(parents=True, exist_ok=True)

BalanceType = Literal["wallet", "bank"]

# migration
def sql_quote(value: str) -> str:
    """Escape a string for use as a SQL literal."""
    return "'" + value.replace("'", "''") + "'"

def migrate():
    """Apply all unapplied SQL migrations in filename order."""
    _conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    _conn.commit()

    applied = {
        row["version"]
        for row in _conn.execute(
            "SELECT version FROM schema_migrations"
        )
    }

    for path in sorted(migrations.glob("*.sql")):
        version = path.stem

        if version in applied:
            continue

        sql = path.read_text(encoding="utf-8")
        print(f"[DB] Applying {version}...")

        try:
            _conn.executescript(
                "BEGIN IMMEDIATE;\n"
                + sql
                + "\nINSERT INTO schema_migrations (version) "
                + f"VALUES ({sql_quote(version)});\n"
                + "COMMIT;"
            )
        except Exception:
            if _conn.in_transaction:
                _conn.rollback()
            raise

        print(f"[DB] Applied {version}")

# util functions
def can_commit(func):
    """Rollbacks if the function raises an Exception"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            _conn.commit()
            return result
        except Exception:
            _conn.rollback()
            raise

    return wrapper

def is_valid_balance_type(value: str):
    """Checks if the balance type is valid"""
    return value in ["wallet", "bank"]

def format_users(raw_data: tuple):
    return {
        "user_id": raw_data[0],
        "wallet": raw_data[1],
        "bank": raw_data[2],
        "joined_at": raw_data[3]
    }

# main functions
def close_connection():
    """Closes the connection"""
    _conn.close()

@can_commit
def add_user(user_id: int):
    """Creates an user if doesn't exist"""
    _conn.execute(f"""
        INSERT OR IGNORE INTO users (user_id)
        VALUES (?)
    """, (user_id,))

@can_commit
def get_user(user_id: int):
    """Fetches an user"""
    add_user(user_id)

    cursor = _conn.execute(f"""
        SELECT * FROM users WHERE user_id = ?
    """, (user_id,))

    return format_users(cursor.fetchone())

@can_commit
def change_amount(user_id: int, amount: int, balance_type: BalanceType):
    """Change the balance of an user"""
    if not is_valid_balance_type(balance_type):
        raise ValueError("Invalid BalanceType")

    add_user(user_id)

    _conn.execute(f"""
        UPDATE users
        SET {balance_type} = {balance_type} + ?
        WHERE user_id = ?
    """, (amount, user_id,))

@can_commit
def transfer_amount(
    user_id: int,
    amount: int,
    source: BalanceType,
    destination: BalanceType,
    fee: int = 0,
):
    """Move money between balances in one conditional update and commit."""
    if not is_valid_balance_type(source) or not is_valid_balance_type(destination):
        raise ValueError("Invalid BalanceType")
    if source == destination:
        raise ValueError("Source and destination must be different")
    if amount <= 0 or fee < 0 or fee > amount:
        raise ValueError("Invalid transfer amount or fee")

    _conn.execute("""
        INSERT OR IGNORE INTO users (user_id)
        VALUES (?)
    """, (user_id,))

    cursor = _conn.execute(f"""
        UPDATE users
        SET {source} = {source} - ?,
            {destination} = {destination} + ?
        WHERE user_id = ? AND {source} >= ?
    """, (amount, amount - fee, user_id, amount))

    return cursor.rowcount > 0

@can_commit
def set_cooldown(user_id: int, action_id: str):
    """Sets the cooldown for an user"""
    add_user(user_id)

    _conn.execute(f"""
        INSERT OR REPLACE INTO cooldowns (user_id, action_id, last_used)
        VALUES (?, ?, unixepoch())
    """, (user_id, action_id))

@can_commit
def get_cooldown(user_id: int, action_id: str):
    """Gets a cooldown for an user"""
    add_user(user_id)

    cursor = _conn.execute("""
        SELECT last_used FROM cooldowns WHERE user_id = ? AND action_id = ?
    """, (user_id, action_id))
    result = cursor.fetchone()

    if result:
        return result[0]
    else:
        return 0

@can_commit
def is_on_cooldown(user_id: int, action_id: str, cooldown: int):
    """Return whether an action is on cooldown and how much time remains.

    Returns a tuple of (is_on_cooldown, remaining_seconds). If the action has
    never been used before, it is treated as not on cooldown and the full cooldown
    duration is returned as remaining time.
    """
    # get_cooldown() returns 0 when the row does not exist yet.
    # Treat that as "not on cooldown" instead of a huge elapsed time.
    last_used = get_cooldown(user_id, action_id)

    if last_used == 0:
        return False, cooldown

    elapsed = time.time() - last_used
    remaining = max(0, cooldown - elapsed)

    # The action is still cooling down while remaining > 0.
    return remaining > 0, remaining
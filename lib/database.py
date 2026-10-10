import sqlite3
from pathlib import Path
from typing import Literal
from functools import wraps

Path("db").mkdir(exist_ok=True)

_conn = sqlite3.connect("db/db.sqlite3")
_conn.row_factory = sqlite3.Row

BalanceType = Literal["wallet", "bank"]

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
    cursor = _conn.execute(f"""
        SELECT * FROM users WHERE user_id = ?
    """, (user_id,))

    if cursor.rowcount == 0:
        return None

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
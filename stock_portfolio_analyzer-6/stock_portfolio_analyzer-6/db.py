"""
db.py
------
Lightweight SQLite persistence layer.

Two tables:
  users     -> id, username, email, password_hash, created_at
  holdings  -> id, user_id (FK), symbol, quantity, avg_price, uploaded_at

Each logged-in user's uploaded portfolio is saved here, replacing their
previous saved holdings on every new upload — so "My Portfolio" always
shows what they last uploaded, even after logging out and back in.

Uses plain sqlite3 (no ORM) so it's easy to read line-by-line in a viva.
"""

import sqlite3
import os
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app_data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_price REAL NOT NULL,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()


# ---------------------- User operations ----------------------

def create_user(username, email, password):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username.strip(), email.strip().lower(), generate_password_hash(password),
             datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
        return dict(user), None
    except sqlite3.IntegrityError:
        return None, "That username or email is already taken."
    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def verify_password(user, password):
    return check_password_hash(user["password_hash"], password)


# ---------------------- Holdings operations ----------------------

def save_holdings(user_id, holdings_df):
    """Replaces the user's saved holdings with a new upload."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("DELETE FROM holdings WHERE user_id = ?", (user_id,))
    for _, row in holdings_df.iterrows():
        conn.execute(
            "INSERT INTO holdings (user_id, symbol, quantity, avg_price, uploaded_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, row["symbol"], float(row["quantity"]), float(row["avg_price"]), now),
        )
    conn.commit()
    conn.close()


def get_saved_holdings(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT symbol, quantity, avg_price, uploaded_at FROM holdings WHERE user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

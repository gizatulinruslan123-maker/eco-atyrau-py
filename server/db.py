# Подключение к базе данных SQLite и функции для работы с ней.
# SQLite используется вместо PostgreSQL/PostGIS для простоты запуска —
# не требует установки отдельного сервера БД.

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'eco.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id TEXT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    rating INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK(type IN ('dump','cleaned','recycling','shop','tree')),
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    description TEXT,
    photo_path TEXT,
    user_id INTEGER,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(type);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def get_or_create_user(telegram_id, username=None, first_name=None):
    telegram_id = str(telegram_id)
    conn = get_conn()
    try:
        row = conn.execute(
            'SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)
        ).fetchone()
        if row is None:
            conn.execute(
                'INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)',
                (telegram_id, username, first_name or 'Волонтёр'),
            )
            conn.commit()
            row = conn.execute(
                'SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)
            ).fetchone()
        return dict(row)
    finally:
        conn.close()


def insert_report(type_, lat, lon, description, photo_path, user_id):
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO reports (type, lat, lon, description, photo_path, user_id, status)
               VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
            (type_, lat, lon, description, photo_path, user_id),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_approved_reports(type_=None):
    conn = get_conn()
    try:
        query = """
            SELECT reports.*, users.first_name AS author_name, users.username AS author_username
            FROM reports LEFT JOIN users ON reports.user_id = users.id
            WHERE reports.status = 'approved'
        """
        params = []
        if type_:
            query += ' AND reports.type = ?'
            params.append(type_)
        query += ' ORDER BY reports.created_at DESC'
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_pending_reports():
    conn = get_conn()
    try:
        rows = conn.execute(
            """SELECT reports.*, users.first_name AS author_name, users.username AS author_username
               FROM reports LEFT JOIN users ON reports.user_id = users.id
               WHERE reports.status = 'pending' ORDER BY reports.created_at ASC"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def approve_report(report_id):
    conn = get_conn()
    try:
        report = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
        if report is None:
            return False
        conn.execute("UPDATE reports SET status = 'approved' WHERE id = ?", (report_id,))
        if report['type'] == 'cleaned' and report['user_id']:
            conn.execute(
                'UPDATE users SET rating = rating + 1 WHERE id = ?', (report['user_id'],)
            )
        conn.commit()
        return True
    finally:
        conn.close()


def reject_report(report_id):
    conn = get_conn()
    try:
        report = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
        if report is None:
            return False
        conn.execute("UPDATE reports SET status = 'rejected' WHERE id = ?", (report_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def get_leaderboard():
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT first_name, username, rating FROM users WHERE rating > 0 ORDER BY rating DESC LIMIT 50'
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

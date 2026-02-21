"""
SQLite database initialization and helper functions.
"""
import os
import sqlite3
from config import DB_DIR

DB_PATH = os.path.join(DB_DIR, "forecasts.db")

def get_db():
    """Get a database connection."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS forecast_requests (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                forecast_start  TEXT    NOT NULL,
                forecast_end    TEXT    NOT NULL,
                input_start     TEXT    NOT NULL,
                input_end       TEXT    NOT NULL,
                peak_load       REAL,
                peak_hour       TEXT,
                avg_load        REAL,
                min_load        REAL,
                status          TEXT    DEFAULT 'processing',
                error_message   TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS forecasted_results (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id      INTEGER NOT NULL,
                hour_offset     INTEGER NOT NULL,
                timestamp       TEXT    NOT NULL,
                predicted_load  REAL    NOT NULL,
                xgb_load        REAL,
                dl_residual     REAL,
                FOREIGN KEY (request_id) REFERENCES forecast_requests(id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_results_request
            ON forecasted_results(request_id)
        """)
    print("✅ Database initialized")

def save_forecast_request(forecast_start, forecast_end, input_start, input_end):
    """Save a new forecast request. Returns the request ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO forecast_requests
                (forecast_start, forecast_end, input_start, input_end, status)
            VALUES (?, ?, ?, ?, 'processing')
        """, (forecast_start, forecast_end, input_start, input_end))
        return cursor.lastrowid

def save_forecast_results(request_id, results):
    """Save forecast results and update request status."""
    loads = [r["predicted_load"] for r in results]
    peak_load = max(loads)
    peak_idx = loads.index(peak_load)
    peak_hour = results[peak_idx]["timestamp"]
    avg_load = sum(loads) / len(loads)
    min_load = min(loads)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO forecasted_results
                (request_id, hour_offset, timestamp, predicted_load, xgb_load, dl_residual)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [(
            request_id,
            r["hour_offset"],
            r["timestamp"],
            r["predicted_load"],
            r.get("xgb_load"),
            r.get("dl_residual")
        ) for r in results])

        cursor.execute("""
            UPDATE forecast_requests
            SET status = 'completed',
                peak_load = ?, peak_hour = ?,
                avg_load = ?, min_load = ?
            WHERE id = ?
        """, (peak_load, peak_hour, avg_load, min_load, request_id))

def update_request_error(request_id, error_msg):
    """Mark a request as failed."""
    with get_db() as conn:
        conn.execute("""
            UPDATE forecast_requests
            SET status = 'failed', error_message = ?
            WHERE id = ?
        """, (error_msg, request_id))

def get_all_requests():
    """Get all forecast requests, newest first."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM forecast_requests
            ORDER BY created_at DESC
        """).fetchall()
        return [dict(r) for r in rows]

def get_request_with_results(request_id):
    """Get a single request with its forecast results."""
    with get_db() as conn:
        req = conn.execute(
            "SELECT * FROM forecast_requests WHERE id = ?", (request_id,)
        ).fetchone()
        if req is None:
            return None

        results = conn.execute("""
            SELECT * FROM forecasted_results
            WHERE request_id = ?
            ORDER BY hour_offset
        """, (request_id,)).fetchall()

        return {
            "request": dict(req),
            "results": [dict(r) for r in results]
        }

def delete_request(request_id):
    """Delete a forecast request and its results."""
    with get_db() as conn:
        conn.execute("DELETE FROM forecast_requests WHERE id = ?", (request_id,))

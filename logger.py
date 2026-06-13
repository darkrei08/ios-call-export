import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_FILE = Path(__file__).parent / "app_debug.sqlite"


class SQLiteHandler(logging.Handler):
    """
    Custom Logging Handler to save logs into a fast SQLite database.
    This makes it incredibly easy to query for errors or specific events.
    """

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        # Create table if it doesn't exist
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    level TEXT,
                    module TEXT,
                    line INTEGER,
                    message TEXT,
                    exc_text TEXT
                )
            """)
            # Limit the database to ~10,000 logs to prevent it from growing indefinitely
            # Clean up old logs asynchronously or when starting
            conn.execute("""
                DELETE FROM logs WHERE id NOT IN (
                    SELECT id FROM logs ORDER BY id DESC LIMIT 10000
                )
            """)
            conn.commit()

    def emit(self, record):
        try:
            timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            level = record.levelname
            module = record.module
            line = record.lineno
            message = self.format(record)

            exc_text = None
            if record.exc_info:
                exc_text = self.formatter.formatException(record.exc_info)

            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                conn.execute(
                    """
                    INSERT INTO logs (timestamp, level, module, line, message, exc_text)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (timestamp, level, module, line, message, exc_text),
                )
                conn.commit()
        except Exception:
            self.handleError(record)


def get_logger(name="ios_export"):
    logger = logging.getLogger(name)

    # If logger already has handlers, avoid duplicates
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # Formatter for the console (optional, just in case we run in terminal)
    formatter = logging.Formatter("[%(levelname)s] %(module)s:%(lineno)d - %(message)s")

    # SQLite Handler
    sqlite_handler = SQLiteHandler(DB_FILE)
    sqlite_handler.setLevel(logging.DEBUG)

    # We override format to only format the message itself since SQLite has columns for the rest
    class SimpleFormatter(logging.Formatter):
        def format(self, record):
            return record.getMessage()

    sqlite_handler.setFormatter(SimpleFormatter())
    logger.addHandler(sqlite_handler)

    # Console Handler for real-time terminal debug
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def dump_latest_logs(limit=100) -> str:
    """Restituisce gli ultimi N log formattati con stack trace, pronti da copiare."""
    try:
        with sqlite3.connect(DB_FILE, timeout=5.0) as conn:
            rows = conn.execute(
                "SELECT timestamp, level, module, line, message, exc_text FROM logs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

        dump = []
        for row in reversed(rows):
            timestamp, level, module, line, message, exc_text = row
            entry = f"[{timestamp}] [{level}] [{module}:{line}] {message}"
            if exc_text:
                entry += f"\n--- STACK TRACE ---\n{exc_text}\n-------------------"
            dump.append(entry)
        return "\n".join(dump)
    except Exception as e:
        return f"Impossibile leggere il database di debug: {e}"


# Singleton default instance
app_logger = get_logger()

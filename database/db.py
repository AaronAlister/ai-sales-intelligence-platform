import sqlite3
from pathlib import Path

# =====================================================
# Database Configuration
# =====================================================

DB_PATH = Path("data/sales.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    """
    Creates and returns a connection to the SQLite database.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    """
    Creates all required database tables.
    """

    conn = get_connection()
    cursor = conn.cursor()

    # =====================================================
    # Sales Table
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        record_hash TEXT,

        invoice TEXT NOT NULL,

        item_code TEXT NOT NULL,

        item_name TEXT NOT NULL,

        item_group TEXT,

        customer TEXT NOT NULL,

        place_of_supply TEXT,

        posting_date DATE NOT NULL,

        stock_qty REAL NOT NULL,

        discount_percent REAL,

        rate REAL NOT NULL,

        amount REAL NOT NULL,

        transaction_type TEXT NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    );
    """)

    # =====================================================
    # Upload History
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS upload_history (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        upload_timestamp TIMESTAMP NOT NULL,

        file_name TEXT NOT NULL,

        file_hash TEXT NOT NULL,

        rows_read INTEGER NOT NULL,

        rows_after_preprocessing INTEGER NOT NULL,

        rows_inserted INTEGER NOT NULL,

        rows_skipped INTEGER NOT NULL,

        duplicate_file BOOLEAN NOT NULL DEFAULT 0,

        status TEXT NOT NULL,

        message TEXT

    );
    """)

    conn.commit()
    conn.close()

    print("✅ Database created successfully.")


if __name__ == "__main__":
    create_database()
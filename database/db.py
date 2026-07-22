import sqlite3
from pathlib import Path

# Database location
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
    Creates the sales table if it does not already exist.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        invoice TEXT UNIQUE NOT NULL,

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

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    );
    """)

    conn.commit()
    conn.close()

    print("✅ Database created successfully.")


if __name__ == "__main__":
    create_database()
import pandas as pd
from database.db import get_connection


class BaseEngine:
    """
    Base class for all analytics engines.

    Provides:
        • Database connection
        • SQL execution
        • Input validation
        • Refresh hook
        • Cleanup
    """

    def __init__(self):
        self.conn = get_connection()

    # =====================================================
    # Utility Methods
    # =====================================================

    def query(self, sql: str, params=None) -> pd.DataFrame:
        """
        Execute a SQL query and return a DataFrame.
        """
        if params is None:
            params = ()

        return pd.read_sql_query(sql, self.conn, params=params)

    def _validate_limit(self, limit: int):
        """
        Validate the limit parameter.
        """
        if not isinstance(limit, int):
            raise TypeError("limit must be an integer.")

        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

    def refresh(self):
        """
        Refresh cached data.

        Child classes should override this.
        """
        pass

    def close(self):
        """
        Close the database connection.
        """
        self.conn.close()
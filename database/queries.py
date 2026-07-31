import pandas as pd

from database.db import get_connection


class SalesQueries:

    @staticmethod
    def customer_sales():
        """
        Returns all sales transactions.
        """

        conn = get_connection()

        query = """
        SELECT *
        FROM sales
        """

        df = pd.read_sql_query(query, conn)

        conn.close()

        return df
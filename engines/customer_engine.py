from hashlib import new
from importlib import abc

from matplotlib.pylab import pareto
import pandas as pd

from database.queries import SalesQueries


class CustomerEngine:
    """
    Customer Intelligence Engine

    Responsible for analyzing customer purchasing behavior.
    """

    def __init__(self):
        self.refresh()

    def refresh(self):
        """Reload all cached customer datasets."""

        df = SalesQueries.customer_sales()

        # Cache complete dataset
        self.customer_df = df

        # Sales only
        self.sales_df = df[df["transaction_type"] == "Sale"].copy()

        # Returns only
        self.returns_df = df[df["transaction_type"] == "Return"].copy()

        self.customer_summary_df = None

    def customer_summary(self):
        """
        Returns summary statistics for every customer.
        """

        if self.customer_summary_df is not None:
            return self.customer_summary_df

        df = self.sales_df

        summary = (
            df.groupby("customer")
            .agg(
                Revenue=("amount", "sum"),
                Quantity=("stock_qty", "sum"),
                Orders=("invoice", "nunique"),
                First_Purchase=("posting_date", "min"),
                Last_Purchase=("posting_date", "max"),
            )
            .reset_index()
        )

        summary["Average_Order_Value"] = (
            summary["Revenue"] / summary["Orders"]
        )

        summary = summary.sort_values(
            by="Revenue",
            ascending=False
        ).reset_index(drop=True)

        self.customer_summary_df = summary

        return summary

    def top_customers_by_revenue(self, n=10):
        return (
            self.customer_summary()
            .sort_values("Revenue", ascending=False)
            .head(n)
        )

    def top_customers_by_quantity(self, n=10):
        return (
            self.customer_summary()
            .sort_values("Quantity", ascending=False)
            .head(n)
        )

    def customer_revenue(self):
        return self.customer_summary()[["customer", "Revenue"]]

    def customer_sales(self):
        return self.customer_summary()[["customer", "Orders"]]

    def repeat_customers(self, sort_by="Orders", ascending=False):
        """
        Returns customers with more than one order.
        """

        summary = self.customer_summary()

        return (
            summary[summary["Orders"] > 1]
            .sort_values(sort_by, ascending=ascending)
            .reset_index(drop=True)
        )    

    def one_time_customers(self):
        """
        Returns customers with exactly one order.
        """

        summary = self.customer_summary()

        return (
            summary[summary["Orders"] == 1]
            .sort_values("Revenue", ascending=False)
            .reset_index(drop=True)
        )

    def purchase_frequency(self):
        """
        Calculates the average number of days between purchases.
        """

        summary = self.customer_summary().copy()

        summary["First_Purchase"] = pd.to_datetime(summary["First_Purchase"])
        summary["Last_Purchase"] = pd.to_datetime(summary["Last_Purchase"])

        summary["Days_Active"] = (
            summary["Last_Purchase"] -
            summary["First_Purchase"]
        ).dt.days

        summary["Purchase_Frequency_Days"] = summary.apply(
            lambda row:
            round(row["Days_Active"] / (row["Orders"] - 1), 2)
            if row["Orders"] > 1 else None,
            axis=1
        )

        return summary[
            [
                "customer",
                "Orders",
                "Purchase_Frequency_Days"
            ]
        ]

    def average_order_value(self):
        """
        Returns the average order value for each customer.
        """

        summary = self.customer_summary()

        return summary[
            [
                "customer",
                "Average_Order_Value"
            ]
        ]

    def customer_contribution(self):
        """
        Returns each customer's contribution to total revenue.
        """

        summary = self.customer_summary().copy()

        total_revenue = summary["Revenue"].sum()

        summary["Contribution_Percentage"] = (
            summary["Revenue"] / total_revenue * 100
        )

        return summary[
            [
                "customer",
                "Revenue",
                "Contribution_Percentage"
            ]
        ]

    def highest_customer_contributors(self, n=10):
        """
        Returns the top customers contributing the most revenue.
        """

        contribution = self.customer_contribution()

        return (
            contribution
            .sort_values(
                "Contribution_Percentage",
                ascending=False
            )
            .head(n)
            .reset_index(drop=True)
        )

    def pareto_customers(self):
        """
        Returns customer contribution with cumulative percentage
        for Pareto (80/20) analysis.
        """

        contribution = self.customer_contribution().copy()

        contribution = contribution.sort_values(
            "Contribution_Percentage",
            ascending=False
        ).reset_index(drop=True)

        contribution["Cumulative_Contribution"] = (
            contribution["Contribution_Percentage"]
            .cumsum()
        )

        return contribution.round(2)

    def pareto_summary(self):
        """
        Returns customers contributing to the first 80%
        of total revenue.
        """

        pareto = self.pareto_customers()

        cutoff = int(pareto["Cumulative_Contribution"].ge(80).idxmax())

        top_customers = pareto.iloc[:cutoff + 1]

        return {
            "Total_Customers": len(pareto),
            "Pareto_Customers": len(top_customers),
            "Pareto_Percentage": round(len(top_customers) / len(pareto) * 100, 2),
            "Revenue_Covered": round(
                top_customers["Contribution_Percentage"].sum().item(),
                2
            )
        }

    def abc_customer_analysis(self):
        """
        Classifies customers into A, B and C
        based on cumulative revenue contribution.
        """

        pareto = self.pareto_customers().copy()

        # Customer that reaches/exceeds 80%
        a_cutoff = int(
            pareto["Cumulative_Contribution"]
            .ge(80)
            .idxmax()
        )

        # Customer that reaches/exceeds 95%
        b_cutoff = int(
            pareto["Cumulative_Contribution"]
            .ge(95)
            .idxmax()
        )

        pareto["Category"] = "C"

        # First 80%
        pareto.loc[:a_cutoff, "Category"] = "A"

        # Next 15%
        pareto.loc[a_cutoff + 1:b_cutoff, "Category"] = "B"

        return pareto

    def abc_summary(self):
        """
        Returns summary statistics for ABC classification.
        """

        abc = self.abc_customer_analysis()

        summary = (
            abc.groupby("Category")
            .agg(
                Customers=("customer", "count"),
                Revenue=("Revenue", "sum"),
                Contribution=("Contribution_Percentage", "sum")
            )
            .reset_index()
        )

        summary["Customer_Percentage"] = (
            summary["Customers"]
            / summary["Customers"].sum()
            * 100
        ).round(2)

        return summary

    def active_customers(self, days=90):
        """
        Returns customers who purchased
        within the last 'days' days.
        """

        summary = self.customer_summary().copy()
        summary["Last_Purchase"] = pd.to_datetime(
            summary["Last_Purchase"]
        )

        latest_date = summary["Last_Purchase"].max()

        summary["Days_Since_Last_Purchase"] = (
            latest_date -
            summary["Last_Purchase"]
            ).dt.days

        active = (
            summary[
                summary["Days_Since_Last_Purchase"] <= days
            ]
            .sort_values(
                ["Last_Purchase", "Revenue"],
                ascending=[False, False]
            )
            .reset_index(drop=True)
        )

        return active[
            [
                "customer",
                "Revenue",
                "Orders",
                "Last_Purchase",
                "Days_Since_Last_Purchase"
            ]
        ]

    def dormant_customers(self, days=90):
        """
        Returns customers who have not purchased
        within the last 'days' days.
        """

        summary = self.customer_summary().copy()

        summary["Last_Purchase"] = pd.to_datetime(
            summary["Last_Purchase"]
        )

        latest_date = summary["Last_Purchase"].max()

        summary["Days_Since_Last_Purchase"] = (
            latest_date -
            summary["Last_Purchase"]
        ).dt.days

        dormant = (
            summary[
                summary["Days_Since_Last_Purchase"] > days
            ]
            .sort_values(
                ["Days_Since_Last_Purchase", "Revenue"],
                ascending=[False, False]
            )
            .reset_index(drop=True)
        )

        return dormant[
            [
                "customer",
                "Revenue",
                "Orders",
                "Last_Purchase",
                "Days_Since_Last_Purchase"
            ]
        ]

    def new_customers(self, days=30):
        """
        Returns customers whose first purchase
        was within the last 'days' days.
        """

        summary = self.customer_summary().copy()

        # Convert to datetime
        summary["First_Purchase"] = pd.to_datetime(
            summary["First_Purchase"]
        )

        # Latest transaction date in the dataset
        latest_date = pd.to_datetime(
            self.sales_df["posting_date"]
        ).max()

        # Calculate days since customer acquisition
        summary["Days_Since_First_Purchase"] = (
            latest_date -
            summary["First_Purchase"]
        ).dt.days

        # Filter new customers
        new = (
            summary[
                summary["Days_Since_First_Purchase"] <= days
            ]
            .sort_values(
                ["First_Purchase", "Revenue"],
                ascending=[False, False]
            )
            .reset_index(drop=True)
        )

        return new[
            [
                "customer",
                "Revenue",
                "Orders",
                "First_Purchase",
                "Days_Since_First_Purchase"
            ]
        ]

    def monthly_customer_growth(self):
        """
        Returns the number of new customers acquired each month.
        """

        summary = self.customer_summary().copy()

        summary["First_Purchase"] = pd.to_datetime(
            summary["First_Purchase"]
        )

        # Create monthly period
        summary["Month"] = (
            summary["First_Purchase"]
            .dt.to_period("M")
        )

        growth = (
            summary.groupby("Month")
            .agg(
                New_Customers=("customer", "count")
            )
            .reset_index()
            .sort_values("Month")
            .reset_index(drop=True)
        )

        # Format after sorting
        growth["Month"] = (
            growth["Month"]
            .dt.strftime("%b %Y")
        )

        return growth

    def customer_details(self, customer_name):
        """
        Returns a complete profile for a given customer.
        """

        customer_name = customer_name.strip()

        # Filter sales for the customer (case-insensitive, trimmed)
        customer_sales = self.sales_df[
            self.sales_df["customer"]
            .str.strip()
            .str.lower()
            == customer_name.lower()
        ].copy()

        if customer_sales.empty:
            raise ValueError(
                f"No customer found with name '{customer_name}'"
            )

        # Use the actual stored name for display going forward
        actual_customer_name = customer_sales["customer"].iloc[0]

        # Basic Metrics
        revenue = customer_sales["amount"].sum()
        quantity = customer_sales["stock_qty"].sum()
        orders = customer_sales["invoice"].nunique()
        avg_order_value = revenue / orders if orders else 0

        first_purchase = customer_sales["posting_date"].min()
        last_purchase = customer_sales["posting_date"].max()

        # Purchase Frequency
        first = pd.to_datetime(first_purchase)
        last = pd.to_datetime(last_purchase)

        if orders > 1:
            purchase_frequency = (
                (last - first).days / (orders - 1)
            )
        else:
            purchase_frequency = None

        # Contribution Percentage
        contribution_df = self.customer_contribution()

        contribution = contribution_df[
            contribution_df["customer"]
            .str.strip()
            .str.lower()
            == customer_name.lower()
        ]

        contribution_percentage = contribution["Contribution_Percentage"].iloc[0]

        # ABC Category
        abc_df = self.abc_customer_analysis()

        abc = abc_df[
            abc_df["customer"]
            .str.strip()
            .str.lower()
            == customer_name.lower()
        ]

        abc_category = abc["Category"].iloc[0]

        # Active / Dormant Status
        latest_date = pd.to_datetime(
            self.sales_df["posting_date"]
        ).max()

        days_since_last = (
            latest_date - last
        ).days

        status = (
            "Active"
            if days_since_last <= 90
            else "Dormant"
        )

        return {
            "Customer": actual_customer_name,
            "Revenue": round(revenue, 2),
            "Quantity": quantity,
            "Orders": orders,
            "Average Order Value": round(avg_order_value, 2),
            "First Purchase": first_purchase,
            "Last Purchase": last_purchase,
            "Purchase Frequency (Days)": (
                round(purchase_frequency, 2)
                if purchase_frequency is not None
                else "N/A"
            ),
            "Contribution Percentage": round(
                contribution_percentage, 2
            ),
            "ABC Category": abc_category,
            "Status": status,
            "Days Since Last Purchase": days_since_last
        }
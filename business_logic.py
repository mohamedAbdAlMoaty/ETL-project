
import logging
import pandas as pd
from constants import Business
logger = logging.getLogger(__name__)

class BusinessHandler:

    def __init__(self):
        self._df = None

    def _classify_delivery(self,row):
        if pd.isnull(row["shipped_date"]):
            return "Not Shipped"
        if row["shipped_date"] > row["required_date"]:
            return "Late"
        return "On Time"


    def _classify_stock(self,row):
        if row["discontinued"] == 1:
            return "Discontinued"
        if row["units_in_stock"] <= row["reorder_level"]:
            return "Reorder"
        return "OK"


    def _classify_customer(self, total_revenue):
        if total_revenue >= Business.gold_threshold:
            return "Gold"
        if total_revenue >= Business.silver_threshold:
            return "Silver"
        return "Bronze"


    def apply_business_logic(self, df):
        self._df = df.copy()

        # --- calculations ---
        self._df["line_total"] = (self._df["sale_unit_price"] * self._df["quantity"] * (1 - self._df["discount"])).round(2)
        self._df["discount_amount"] = (self._df["sale_unit_price"] * self._df["quantity"] * self._df["discount"]).round(2)
        self._df["order_month"] = self._df["order_date"].dt.to_period("M").astype(str)
        self._df["days_to_ship"] = (self._df["shipped_date"] - self._df["order_date"]).dt.days

        # --- classifications ---
        self._df["delivery_status"] = self._df.apply(self._classify_delivery, axis=1)
        self._df["stock_status"] = self._df.apply(self._classify_stock, axis=1)

        customer_revenue = self._df.groupby("customer_id")["line_total"].sum()
        tier_by_customer = customer_revenue.map(lambda value: self._classify_customer(value))
        self._df["customer_tier"] = self._df["customer_id"].map(tier_by_customer)

        logger.info(
            "business logic: total revenue={:,.2f}; delivery={}; tiers={}".format(
               self._df["line_total"].sum(),
                self._df["delivery_status"].value_counts().to_dict(),
                tier_by_customer.value_counts().to_dict(),
            )
        )
        return self._df


    def build_summaries(self):
    
        summaries = {
            "revenue_by_category": (
                self._df.groupby("category_name")
                .agg(revenue=("line_total", "sum"), units=("quantity", "sum"),
                    orders=("order_id", "nunique"))
                .round(2).sort_values("revenue", ascending=False).reset_index()
            ),
            "revenue_by_country": (
                self._df.groupby("country")
                .agg(revenue=("line_total", "sum"), customers=("customer_id", "nunique"))
                .round(2).sort_values("revenue", ascending=False).reset_index()
            ),
            "revenue_by_month": (
                self._df.groupby("order_month").agg(revenue=("line_total", "sum"))
                .round(2).reset_index()
            ),
            "delivery_performance": (
                self._df.drop_duplicates("order_id")["delivery_status"]
                .value_counts().rename_axis("delivery_status").reset_index(name="orders")
            ),
            "customer_tiers": (
                self._df.groupby(["customer_tier", "customer_id", "company_name"])
                .agg(revenue=("line_total", "sum")).round(2)
                .sort_values("revenue", ascending=False).reset_index()
            ),
        }
        logger.info(f"summaries built: {summaries}")
        return summaries
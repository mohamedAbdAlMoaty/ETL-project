import re
import logging
import pandas as pd
from constants import Names
logger = logging.getLogger(__name__)

class Transformer:

    def __init__(self,tables : dict):
        self._tables = tables
        self._df = None

    def run(self):
      
        for table_name, df in self._tables.items():
            self._df = df
            self._drop_duplicate_rows(table_name)
            for col in df.columns:
                
                col = self._to_snack_case(table_name,col)
                self._trim_whitespace(table_name,col)
                self._cast_date(table_name,col)
                self._cast_numeric(table_name,col)
                self._clean_missing_values(table_name,col)

            self._tables[table_name] = self._df

        # if i want to return all tables    
        # return self._tables       
        one_table = self._merge_tables()    
        return one_table   




    # 'orderID' -> 'order_id', 'unitsInStock' -> 'units_in_stock'
    def _to_snack_case(self, table_name , col):
        
        before = col
        col = re.sub(r"([a-z])([A-Z])", r"\1_\2", col).strip().lower() 
        after = col
        
        self._df.rename(columns={before: after}, inplace=True)
        logger.info(f"to_snake_case | table={table_name} | {before} -> {after}")
        return after



    # trim whitespace in text columns
    def _trim_whitespace(self, table_name,col):
        before_series = self._df[col].astype("string")
        self._df[col] = self._df[col].astype("string").str.strip()
        after_series = self._df[col]

        # Count total characters removed
        chars_trimmed = (before_series.str.len() - after_series.str.len()).sum()
        changed = before_series != after_series
        if changed.any():
            logger.info(f"trim_whitespace | table={table_name} | column={col} | { before_series[changed].tolist()} -> {after_series[changed].tolist()} | Characters trimmed={chars_trimmed}")
        return after_series


    # Remove fully duplicated rows
    def _drop_duplicate_rows(self,table_name):
        before = len(self._df)
        count_duplicates = self._df.duplicated().sum()
        if count_duplicates > 0:
            self._df = self._df.drop_duplicates(keep="first")
            after = len(self._df)
            logger.info(f" duplicate | table={table_name} | rows_before={before} | rows_after={after} | duplicates_removed={count_duplicates}")
  


    def _cast_date(self, table_name, col):
        if col in Names.date_columns:
            before_dtype = self._df[col].dtype
            self._df[col]= pd.to_datetime(self._df[col], errors="coerce")

            logger.info(f"type_cast_date | table={table_name} | "f"total_converted={len(self._df.select_dtypes(include=['datetime']).columns)} | rows={self._df.shape[0]} | columns={self._df.shape[1]}")     



    def _cast_numeric(self, table_name, col):
        if col in Names.numeric_columns:
            before_dtype = self._df[col].dtype
            self._df[col] = pd.to_numeric(self._df[col], errors="coerce")

            logger.info(f"type_cast_date | table={table_name} | "f"total_converted={len(self._df.select_dtypes(include=['number']).columns)} | rows={self._df.shape[0]} | columns={self._df.shape[1]}")  


    def _clean_missing_values(self, table_name, col):
        if col in Names.missing_columns:
            missing_count = self._df[col].isna().sum()
            self._df[col] = self._df[col].fillna("N/A")

            logger.info(f"missing_values | table={table_name} |  total_filled={missing_count}  | rows={self._df.shape[0]} | columns={self._df.shape[1]}")          



    def _merge_tables(self):

        order_details = self._tables["order_details"].rename(columns={"unit_price": "sale_unit_price"})
        orders = self._tables["orders"]
        customers = self._tables["customers"]
        products = self._tables["products"]
        categories = self._tables["categories"]

        merged_df = order_details.merge(orders,on="order_id",how="left")

        merged_df = merged_df.merge(customers,on="customer_id",how="left")

        merged_df = merged_df.merge(products,on="product_id",how="left")

        merged_df = merged_df.merge(categories,on="category_id",how="left")

        nums_rows_before_merge = order_details.shape[0]
        nums_rows_after_merge = merged_df.shape[0]

        if nums_rows_before_merge != nums_rows_after_merge :
            raise ValueError(f"Merge changed row count: {nums_rows_after_merge} -> {nums_rows_before_merge}")

        logger.info(f"rows before merge: {nums_rows_before_merge} rows ")
        logger.info(f"merged table dimentions: {nums_rows_after_merge} rows x {merged_df.shape[1]} columns")
        
        return merged_df
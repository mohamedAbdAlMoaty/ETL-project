from pathlib import Path


class Paths:
    WORK_DIR = Path("downloaded")
    OUT_DIR = Path("output")


class Urls:
    source_base_url = "https://raw.githubusercontent.com/graphql-compose/graphql-compose-examples/master/examples/northwind/data/csv/"


class Names:
    files_names = ["orders", "order_details", "customers", "products", "categories"]
    date_columns = ["order_date", "required_date", "shipped_date"]
    numeric_columns = ["freight","unit_price", "quantity", "discount","unit_price", "units_in_stock", "reorder_level"]
    missing_columns = ["ship_region","ship_postal_code", "region", "postal_code","fax"]


       # business rules - change them here, not deep inside the code
class Business:     
    gold_threshold = 30000
    silver_threshold= 10000
# Northwind ETL Pipeline

> **Python ETL tool** — reads several CSV files, cleans them, merges them, applies business rules,
> saves the results in three formats, and logs every step.

```
Extract  ->  Analyse  ->  Transform  ->  Business logic  ->  Load
(download)   (profile)    (clean+merge)   (calc+classify)    (CSV / Excel / JSON)
                         ───────────── logging runs underneath all steps ─────────────
```

---

## 1. What is this project?

A company's sales data rarely lives in one tidy file. It arrives as **several related files**, with
gaps, duplicates and text where numbers should be. This project turns that into **one trustworthy,
analysis-ready dataset**, in a way that is **repeatable** and **auditable**.

That job is called **ETL** (Extract, Transform, Load). The tool is built with core Python,
`pathlib`, `logging` and `pandas`.

**With one command (`python main.py`) the tool:**

| # | It does this | Using |
|---|---|---|
| 1 | **Downloads** the source CSVs (and skips files already present) | `pd.read_csv`, `pathlib` |
| 2 | **Profiles** every table: shape, dtypes, duplicates, missing values | `glob`, `duplicated`, `isna` |
| 3 | **Cleans** names, whitespace, duplicates, types and missing values | `drop_duplicates`, `to_datetime`, `to_numeric`, `fillna` |
| 4 | **Merges** the five tables into one DataFrame | `pd.merge` |
| 5 | Applies **business logic** (calculations and classifications) | `apply`, `map`, `groupby` |
| 6 | **Saves** the results as **CSV + Excel + JSON** | `to_csv`, `ExcelWriter`, `json` |
| 7 | **Logs** every step to a file and the console | `logging`, a custom context manager |

---

## 2. The data

The pipeline uses the public **Northwind** sample: orders placed with a fictional food-trading company.
Five related tables, connected by ID columns (keys):

```
customers ──< orders ──< order_details >── products >── categories
   1 : many     1 : many                   many : 1      many : 1
```

| File | Rows | What it holds |
|---|---|---|
| `orders.csv` | 831 (830 after cleaning) | One row per order: customer, dates, freight, shipping details |
| `order_details.csv` | 2,155 | One row per **order line**: product, price, quantity, discount |
| `customers.csv` | 91 | Who placed the orders |
| `products.csv` | 77 | What was sold, stock levels, discontinued flag |
| `categories.csv` | 8 | Product categories |

**Read the diagram like this:** one customer has many orders, one order has many order lines,
one product appears on many order lines. The merge starts from the **centre table**
(`order_details`) and attaches everything else to it.

Source: [graphql-compose-examples / northwind](https://github.com/graphql-compose/graphql-compose-examples/tree/master/examples/northwind/data/csv)

---

## 3. Project layout

```
ETL/
├── main.py                   <- ENTRY POINT: runs the whole pipeline
├── extract.py                Extractor: downloads source CSVs
├── transform.py              Transformer: cleaning + merging
├── business_logic.py         BusinessHandler: calculations, classifications, summaries
├── load.py                   Loader: writes CSV / Excel / JSON
├── constants.py              Paths, URL, column lists, business thresholds
├── logging_setup.py          Logging config + log_step() context manager
├── etl_tool.ipynb            Early notebook prototype
├── requirements.txt
│
├── downloaded/               <- INPUT: the 5 CSV files land here
│   ├── orders.csv
│   ├── order_details.csv
│   ├── customers.csv
│   ├── products.csv
│   └── categories.csv
├── output/                   <- OUTPUT: what the tool produces
│   ├── order_lines_clean.csv     (full clean table)
│   ├── etl_report.xlsx           (full table + 5 summary sheets)
│   └── etl_summary.json          (headline numbers + summaries)
└── logs/
    └── pipeline.log          <- the audit trail of every run
```

**Which file does what**

| File | Class / function | Purpose |
|---|---|---|
| `main.py` | `main()` | Runs Extract → Analysis → Transform → Business logic → Load, each wrapped in `log_step` |
| `extract.py` | `Extractor` | Downloads each CSV into `downloaded/`; skips files that already exist |
| `transform.py` | `Transformer` | Cleans every table, then merges them into one |
| `business_logic.py` | `BusinessHandler` | Adds calculated columns and classifications, builds summary tables |
| `load.py` | `Loader` | Saves the final table and summaries to `output/` |
| `constants.py` | `Paths`, `Urls`, `Names`, `Business` | All configuration in one place |
| `logging_setup.py` | `setup_logging`, `log_step` | Console + rotating file log, with START / DONE / FAILED and timing |

---

## 4. How it works

### Step 1: Extract
`Extractor` downloads `orders`, `order_details`, `customers`, `products` and `categories` into
`downloaded/`. If a file is already there it is skipped, so re-runs are fast and work offline.

### Step 2: Analysis
Every CSV in `downloaded/` is read (no hard-coded file names) and its shape, dtypes, duplicate count and
missing values are logged. This is the evidence for the cleaning decisions below.

### Step 3: Transform

Cleaning is judgement, not a reflex. Each decision has a reason:

| Finding | Decision |
|---|---|
| `camelCase` column names | **Rename** to `snake_case` (`orderID` → `order_id`) |
| Stray whitespace in text | **Trim** (e.g. one customer city had a leading space) |
| 1 fully duplicated row in `orders` | **Drop** (831 → 830 rows) |
| Dates stored as text | **Convert** `order_date`, `required_date`, `shipped_date` to real dates |
| Numbers that may be text | **Convert** `freight`, `unit_price`, `quantity`, `discount`, `units_in_stock`, `reorder_level` |
| `region`, `postal_code`, `fax`, `ship_region`, `ship_postal_code` missing | **Fill** with `"N/A"` |
| `shipped_date` missing | **Keep missing**: it means "not shipped yet", and filling it would break the delivery rule |

### Merge safety
Starting from `order_details`, the tool left-joins `orders`, `customers`, `products` and `categories`.

If a lookup table accidentally has duplicate keys, a merge quietly **multiplies rows** and inflates revenue
without crashing. To guard against it, the tool **raises an error if the merged table does not have the same
number of rows as `order_details`** (2,155). A good pipeline fails loudly rather than producing wrong numbers quietly.

### Step 4: Business logic

| New column | Rule |
|---|---|
| `line_total` | `sale_unit_price × quantity × (1 − discount)` |
| `discount_amount` | `sale_unit_price × quantity × discount` |
| `order_month` | Order date as `YYYY-MM` |
| `days_to_ship` | `shipped_date − order_date` (days) |
| `delivery_status` | not shipped → **Not Shipped**; shipped after the required date → **Late**; otherwise **On Time** |
| `stock_status` | discontinued → **Discontinued**; stock at or below reorder level → **Reorder**; otherwise **OK** |
| `customer_tier` | total revenue ≥ 30,000 → **Gold**; ≥ 10,000 → **Silver**; otherwise **Bronze** |

The tier thresholds live in `constants.py` (`Business`), so changing a business rule means changing one line.

Five **summary tables** are also built: revenue by category, revenue by country, revenue by month,
delivery performance, and customer tiers.

### Step 5: Load

| Format | Audience | Contents |
|---|---|---|
| **CSV** | Other tools and pipelines | `order_lines_clean.csv`: full clean order-line table |
| **Excel** | Business users | `etl_report.xlsx`: full table plus one sheet per summary |
| **JSON** | Applications and APIs | `etl_summary.json`: headline numbers plus all summaries |

---

## 5. Quick start

**Requirements:** Python 3.11+ (needed by the pinned pandas version), internet access the first time
(the sample files are downloaded from GitHub).

```bash
cd ETL
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

> Run it **from inside the `ETL/` folder**: all paths (`downloaded/`, `output/`, `logs/`) are relative to where you run it.

### What a successful run looks like
```
... | INFO | __main__ | ========== ETL PIPELINE STARTED ==========
... | INFO | __main__ | START  extract
... | INFO | transform | duplicate | table=orders | rows_before=831 | rows_after=830 | duplicates_removed=1
... | INFO | transform | merged table dimentions: 2155 rows x 40 columns
... | INFO | __main__ | DONE   business logic
... | INFO | load | saved CSV   -> output\order_lines_clean.csv
... | INFO | load | saved Excel -> output\etl_report.xlsx
... | INFO | load | saved JSON  -> output\etl_summary.json
... | INFO | __main__ | ========== ETL PIPELINE COMPLETED ==========
```

### Self-check numbers
If your results differ from these, something earlier in the pipeline is off.

| Metric | Value |
|---|---|
| Order lines | 2,155 |
| Orders | 830 |
| Customers with orders | 89 |
| Total revenue | 1,265,793.02 |
| Delivery (orders) | 772 On Time · 37 Late · 21 Not Shipped |
| Top category | Beverages (267,868.18) |
| Top country | USA (245,584.62) |
| Customer tiers | 7 Gold · 31 Silver · 51 Bronze |

---

## 6. Configuration

Everything configurable is in `constants.py`:

| Setting | What it controls |
|---|---|
| `Paths.WORK_DIR` / `Paths.OUT_DIR` | Input and output folders |
| `Urls.source_base_url` | Where the source CSVs are downloaded from |
| `Names.files_names` | Which files to download |
| `Names.date_columns`, `numeric_columns`, `missing_columns` | Which columns get date / number casting / `"N/A"` filling |
| `Business.gold_threshold`, `silver_threshold` | Customer tier cut-offs (30,000 / 10,000) |

Log level and log file location are set in `setup_logging()` in `logging_setup.py`.
The log is a rotating file (5 MB, 3 backups) so it can never fill the disk.

---

## 7. Common mistakes

| Symptom | Cause | Fix |
|---|---|---|
| `FileNotFoundError: No CSV files found` | Run from the wrong folder | `cd ETL` first, then `python main.py` |
| `KeyError: 'orderDate'` | Columns are renamed to `snake_case` during Transform | Use `order_date` after cleaning |
| `ValueError: Merge changed row count` | A lookup table has duplicate keys | Check the table for duplicate IDs |
| `shipped_date` all filled in | Missing values filled blindly | Fill only columns where a default makes sense |
| Excel save fails | `openpyxl` not installed | `pip install -r requirements.txt` |
| Download fails | No internet | Put the five CSVs in `downloaded/` manually |
| Stale data after changing the source | Existing files are skipped on re-run | Delete the files in `downloaded/` |

---

## 8. Extension ideas

1. Flag orders whose `freight` is above the 90th percentile as `"High Freight"`.
2. Also save the main table as **Parquet** and compare file sizes with the CSV.
3. Write **one CSV per year** into `output/by_year/`.
4. Save a `quality_report.json` from the analysis step.
5. Raise an error if any `line_total` is negative, and show the failure in the log.
6. Add `validate="many_to_one"` to the merges for an even stricter safety check.

---

## 9. Skills this project uses

| Topic | Where it appears here |
|---|---|
| Classes and functions, error handling | Every step is a class; `main()` wraps the run in `try / except` |
| File I/O, `pathlib` | Finding and reading all CSVs; creating folders |
| Context managers | `log_step()` records start, finish and timing |
| `logging` | Audit trail of every step |
| JSON and CSV | Output formats |
| pandas basics | Reading, missing data, types |
| pandas advanced | Merge, groupby, apply and map, writing Excel |

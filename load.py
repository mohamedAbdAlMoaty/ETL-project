
from pathlib import Path
from constants import Paths
import logging
import json
import pandas as pd
logger = logging.getLogger(__name__)

class Loader:
    

    def __init__(self, df :pd.DataFrame, summaries :dict ):

        # final output_df
        self._df = df
        self._summaries = summaries                      


    def save(self):

        out_dir = Paths.OUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        csv_path = out_dir / "order_lines_clean.csv"
        self._df.to_csv(csv_path, index=False)
        logger.info(f"saved CSV   -> {csv_path} ({csv_path.stat().st_size:,} bytes)")


        excel_path = out_dir / "etl_report.xlsx"
        with pd.ExcelWriter(excel_path) as writer:           # context manager again
            self._df.to_excel(writer, sheet_name="order_lines", index=False)
            for sheet_name, summary_df in self._summaries.items():
                summary_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        logger.info(f"saved Excel -> {excel_path} ({excel_path.stat().st_size:,} bytes)")


        json_path = out_dir / "etl_summary.json"
        payload = {
            "total_revenue": round(float(self._df["line_total"].sum()), 2),
            "order_lines": int(len(self._df)),
            "orders": int(self._df["order_id"].nunique()),
            "customers": int(self._df["customer_id"].nunique()),
            "summaries": {
                name: json.loads(s.to_json(orient="records")) for name, s in self._summaries.items()
            },
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info(f"saved JSON  -> {json_path} ({json_path.stat().st_size:,} bytes)")
        return {"csv": csv_path, "excel": excel_path, "json": json_path}


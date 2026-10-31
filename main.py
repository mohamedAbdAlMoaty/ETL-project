from extract import Extractor
from transform import Transformer
from constants import Paths,Urls,Names
from business_logic import BusinessHandler
from load import Loader
import logging
import pandas as pd
from logging_setup import setup_logging,log_step



setup_logging()

logger = logging.getLogger(__name__)


def main():

    logger.info("========== ETL PIPELINE STARTED ==========")

    try:

        # Extract
        with log_step(logger, "extract"):
            
            extractor = Extractor(Urls.source_base_url,Names.files_names)
            extractor.extract()


        # take a look on csv files after extract to know what should you clean
        with log_step(logger, " analysis"):
            get_tables_after_analyze()

        
        # Transform
        with log_step(logger, "Transform"):
            trasform = Transformer(get_tables_after_analyze())
            one_merged_table = trasform.run()


        # business logic
        with log_step(logger, "business logic"):
            handler = BusinessHandler()
            final_output = handler.apply_business_logic(one_merged_table)
            summaries = handler.build_summaries()
            

        # Load
        with log_step(logger, "Load"):
            loader = Loader(final_output, summaries)
            loader.save()
     

        logger.info("========== ETL PIPELINE COMPLETED ==========")

    except Exception:
        logger.exception("ETL pipeline failed")



def get_tables_after_analyze():
    csv_files = list(Paths.WORK_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {Paths.WORK_DIR}")

    tables={}
    for file in csv_files:
        main_df = pd.read_csv(file)
        df = main_df.copy()
        tables[file.stem]=df  # file.stem bring the file name without .csv
        logger.info(f"table {file.name} : {df.head(3)}")
        logger.info(f"read {file.name}: {df.shape[0]} rows x {df.shape[1]} columns")
        logger.info(f"dtypes {file.name}: {df.dtypes}")
        logger.info(f"duplicates {file.name}: {df.duplicated().sum()}")
        logger.info(f"Missing values {file.name}: {df.isna().sum()}")
    return tables


if __name__ == "__main__":
    main()


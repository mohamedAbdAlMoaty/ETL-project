from pathlib import Path
import pandas as pd
from urllib.parse import urlparse
import logging
from logging_setup import setup_logging
from constants import Paths

logger = logging.getLogger(__name__)


class Extractor:

    def __init__(self, base_url , files_names):
        self._base_url = base_url
        self._files_names = files_names
        self._df = None

    def extract(self):

        Paths.WORK_DIR.mkdir(exist_ok=True)

        for file in self._files_names:
            target = Paths.WORK_DIR / f"{file}.csv"
            if target.exists():
                logger.info(f"already downloaded: {target.name}")
                continue
            df = pd.read_csv( self._base_url + f"{file}.csv")
            df.to_csv(target, index=False)
            logger.info(f"downloaded {target.name}: {len(df)} rows")   
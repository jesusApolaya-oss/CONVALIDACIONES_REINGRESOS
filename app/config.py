import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
LEGACY_WORKBOOK_PATH = Path(
    os.getenv(
        "LEGACY_WORKBOOK_PATH",
        str(Path.home() / "Downloads" / "CONVALIDACION Y REINGRESO - v7.61 10.xlsm"),
    )
)

OUTPUT_DIR.mkdir(exist_ok=True)

APP_TITLE = "Convalidaciones y Reingresos"
APP_VERSION = "2.0"

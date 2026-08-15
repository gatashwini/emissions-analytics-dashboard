"""Configuration and environment variables for the dashboard."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "Data" / "ghgrp_oilgas_emissions_sample.csv"

# Enables future API integrations without placing secrets in source code.
load_dotenv(PROJECT_ROOT / ".env")
EMISSIONS_API_KEY = os.getenv("EMISSIONS_API_KEY", "")
EMISSIONS_API_BASE_URL = os.getenv("EMISSIONS_API_BASE_URL", "")

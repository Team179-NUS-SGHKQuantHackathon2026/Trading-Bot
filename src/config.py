import os
from dotenv import load_dotenv

load_dotenv()

ROOSTOO_API_KEY=os.getenv("ROOSTOO_API_KEY")
ROOSTOO_SECRET_KEY=os.getenv("ROOSTOO_SECRET_KEY")
ROOSTOO_BASE_URL = os.getenv("ROOSTOO_BASE_URL")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))
import os
from dotenv import load_dotenv

load_dotenv()

ROOSTOO_API_KEY=os.getenv("ROOSTOO_API_KEY")
ROOSTOO_SECRET_KEY=os.getenv("ROOSTOO_SECRET_KEY")
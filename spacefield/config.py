import os
from dotenv import load_dotenv

load_dotenv()

DATA_DIRECTORY = os.getenv("DATA_PATH", "/spacefield/data")

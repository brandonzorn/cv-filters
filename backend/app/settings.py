import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../data.db")

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"
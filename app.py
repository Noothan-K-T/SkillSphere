import psycopg
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

with psycopg.connect(DATABASE_URL.replace("+psycopg", "")) as conn:
    print(conn.execute("SELECT version();").fetchone())
import psycopg2
import os
def get_connection():
    # Connect to your postgres DB
    return psycopg2.connect(os.getenv("DATABASE_URL"))


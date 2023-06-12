from psycopg2.pool import SimpleConnectionPool
import os

db_pool = None


def init_db_pool():
    global db_pool
    db_url = os.getenv("DATABASE_URL")
    db_pool = SimpleConnectionPool(1, 20, db_url)


def get_conn():
    return db_pool.getconn()


def release_conn(conn):
    db_pool.putconn(conn)

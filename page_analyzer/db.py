from contextlib import contextmanager

from psycopg2.pool import SimpleConnectionPool
import os

db_pool = None


def init_db_pool():
    global db_pool
    db_url = os.getenv("DATABASE_URL")
    db_pool = SimpleConnectionPool(1, 20, db_url)


@contextmanager
def get_conn():
    try:
        conn = db_pool.getconn()
        yield conn
        conn.commit()
    except Exception as error:
        conn.rollback()
        raise error
    finally:
        db_pool.putconn(conn)


def release_conn(conn):
    db_pool.putconn(conn)

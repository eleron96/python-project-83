from page_analyzer.urls import normalize


def get_url_by_name(conn, url):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM urls WHERE name = %s",
                       (normalize(url),))  # используем нормализованный URL
        existing_url = cursor.fetchone()
    return existing_url


def add_url(conn, url):
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO urls(name) VALUES (%s) RETURNING id",
                       (normalize(url),))  # используем нормализованный URL
        url_id = cursor.fetchone()[0]
    return url_id


def get_url_by_id(conn, url_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, created_at FROM urls WHERE id = %s",
                       (url_id,))
        url = cursor.fetchone()
    return url


def get_url_checks_by_id(conn, url_id):
    checks = []
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, url_id, created_at, status_code, h1, description, "
            "title FROM url_checks WHERE url_id = %s ORDER BY created_at DESC",
            (url_id,))
        checks_raw = cursor.fetchall()
        for check in checks_raw:
            checks.append({
                "id": check[0],
                "url_id": check[1],
                "created_at": check[2],
                "status_code": check[3],
                "h1": check[4],
                "description": check[5],
                "title": check[6]
            })
    return checks


def get_all_urls(conn):
    urls = []
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT urls.id, urls.name, checks.created_at, checks.status_code
            FROM urls
            LEFT JOIN (
                SELECT url_id, status_code, created_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY url_id ORDER BY created_at DESC) as rn
                FROM url_checks
            ) checks ON urls.id = checks.url_id
            WHERE checks.rn = 1
            ORDER BY CASE WHEN checks.created_at IS NULL THEN 1 ELSE 0 END,
                checks.created_at DESC
            """)
        urls_raw = cursor.fetchall()
        for url in urls_raw:
            urls.append({
                "id": url[0],
                "name": url[1],
                "created_at": url[2],
                "status_code": url[3]
            })
    return urls


def add_url_check(conn, url_id, status_code, h1, description, title):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO url_checks(url_id, created_at, status_code, h1,
             description, title)
            VALUES (%s, DATE(NOW()), %s, %s, %s, %s)
            RETURNING id
            """, (url_id, status_code, h1, description, title))
        conn.commit()
        check_id = cursor.fetchone()[0]
    return check_id

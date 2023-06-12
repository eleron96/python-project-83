def get_url_id(cursor, normalized_url):
    cursor.execute("""
    SELECT id FROM urls WHERE name = %s
    """, (normalized_url,))
    existing_url = cursor.fetchone()

    if existing_url is None:
        cursor.execute("""
        INSERT INTO urls(name)
        VALUES (%s)
        RETURNING id
        """, (normalized_url,))
        url_id = cursor.fetchone()[0]
    else:
        url_id = existing_url[0]

    return url_id


def get_url_data(cursor, url_id):
    cursor.execute("SELECT id, name, created_at FROM urls WHERE id = %s",
                   (url_id,))
    return cursor.fetchone()


def get_checks_data(cursor, url_id):
    cursor.execute(
        "SELECT id, url_id, created_at, status_code, h1, description, "
        "title FROM url_checks WHERE url_id = %s ORDER BY created_at DESC",
        (url_id,))
    return cursor.fetchall()


def get_urls_list(cursor):
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
    return cursor.fetchall()


def get_url_name(cursor, url_id):
    cursor.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
    return cursor.fetchone()[0]


def insert_url_check(cursor, url_id, response, h1_text, description_text,
                     title_text):
    cursor.execute("""
    INSERT INTO url_checks(
        url_id, created_at, status_code, h1, description, title)
    VALUES (%s, DATE(NOW()), %s, %s, %s, %s)
    RETURNING id
    """, (url_id, response.status_code, h1_text, description_text, title_text))

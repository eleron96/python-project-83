from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from .db import get_connection
from .urls import validate, normilize
import requests

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/urls")
def add_url():
    url = request.form["url"]
    errors = validate(url)
    if errors:
        for error in errors:
            flash(error, "danger")
            return render_template("index.html", url=url), 400

    normalized_url = normilize(url)  # нормализация URL
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id FROM urls WHERE name = %s
    """, (normalized_url,))  # используем нормализованный URL
    existing_url = cursor.fetchone()

    if existing_url is None:
        cursor.execute("""
        INSERT INTO urls(name)
        VALUES (%s)
        RETURNING id
        """, (normalized_url,))  # используем нормализованный URL
        url_id = cursor.fetchone()[0]
        flash("URL успешно добавлен!", "success")
    else:
        url_id = existing_url[0]
        flash("Данный URL уже есть в базе!", "warning")

    conn.commit()
    return redirect(url_for('show_url', url_id=url_id))


@app.route("/urls/<int:url_id>")
def show_url(url_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
    url = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC",
        (url_id,))
    checks = cursor.fetchall()

    return render_template("url.html", id=url[0], name=url[1],
                           created_at=url[2], checks=checks)


@app.route("/urls_list")
def urls_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT urls.id, urls.name, checks.created_at, checks.status_code
    FROM urls
    LEFT JOIN (
        SELECT url_id, status_code, created_at
        FROM (
            SELECT url_id, status_code, created_at,
                ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY created_at DESC) as rn
            FROM url_checks
        ) t
        WHERE t.rn = 1
    ) checks ON urls.id = checks.url_id
    GROUP BY urls.id, checks.created_at, checks.status_code
    ORDER BY CASE WHEN checks.created_at IS NULL THEN 1 ELSE 0 END, checks.created_at DESC
    """)
    urls = cursor.fetchall()
    return render_template("urls_list.html", urls=urls)



@app.route("/urls/<int:url_id>/checks", methods=['POST'])
def check_url(url_id):
    conn = get_connection()
    cursor = conn.cursor()

    # получаем URL по id
    cursor.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
    url = cursor.fetchone()[0]

    # выполняем GET-запрос к URL
    response = requests.get(url)
    status_code = response.status_code  # извлекаем статус код

    cursor.execute("""
    INSERT INTO url_checks(url_id, status_code, created_at)
    VALUES (%s, %s, NOW())
    RETURNING id
    """, (url_id, status_code))  # добавляем статус код в запрос на вставку
    check_id = cursor.fetchone()[0]

    conn.commit()
    flash('URL check created successfully!', 'success')
    return redirect(url_for('show_url', url_id=url_id))






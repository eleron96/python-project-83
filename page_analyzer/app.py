from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from .db import get_connection
from .urls import validate, normilize
import requests
from bs4 import BeautifulSoup


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
        flash("Страница успешно добавлена", "success")
    else:
        url_id = existing_url[0]
        flash("Страница уже существует", "warning")

    conn.commit()
    return redirect(url_for('show_url', url_id=url_id))



@app.route("/urls/<int:url_id>")
def show_url(url_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (url_id,))
    url = cursor.fetchone()

    cursor.execute(
        "SELECT id, url_id, created_at, status_code, h1, description, title FROM url_checks WHERE url_id = %s ORDER BY created_at DESC",
        (url_id,))
    checks_raw = cursor.fetchall()

    checks = []
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

    return render_template("url.html", id=url[0], name=url[1], created_at=url[2], checks=checks)



@app.route("/urls")
def urls_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT urls.id, urls.name, checks.created_at, checks.status_code
    FROM urls
    LEFT JOIN (
        SELECT url_id, status_code, created_at,
            ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY created_at DESC) as rn
        FROM url_checks
    ) checks ON urls.id = checks.url_id
    WHERE checks.rn = 1
    ORDER BY CASE WHEN checks.created_at IS NULL THEN 1 ELSE 0 END, checks.created_at DESC
    """)
    urls_raw = cursor.fetchall()

    urls = []
    for url in urls_raw:
        urls.append({
            "id": url[0],
            "name": url[1],
            "created_at": url[2],
            "status_code": url[3]
        })
    return render_template("urls_list.html", urls=urls)


@app.route("/urls/<int:url_id>/checks", methods=['POST'])
def check_url(url_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
    url = cursor.fetchone()[0]

    try:
        response = requests.get(url)
    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('show_url', url_id=url_id))

    soup = BeautifulSoup(response.content, 'lxml')
    h1_tag = soup.find('h1')
    h1_text = h1_tag.text if h1_tag else ""

    title_tag = soup.find('title')
    title_text = title_tag.text if title_tag else ""

    meta_description_tag = soup.find('meta', attrs={'name': 'description'})
    description_text = meta_description_tag['content'] if meta_description_tag else ""

    cursor.execute("""
    INSERT INTO url_checks(url_id, created_at, status_code, h1, description, title)
    VALUES (%s, DATE(NOW()), %s, %s, %s, %s)
    RETURNING id
    """, (url_id, response.status_code, h1_text, description_text, title_text))
    check_id = cursor.fetchone()[0]
    conn.commit()
    flash('Страница успешно проверена', 'success')
    return redirect(url_for('show_url', url_id=url_id))



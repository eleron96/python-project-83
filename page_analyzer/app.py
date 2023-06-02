from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from .db import get_connection
from .urls import validate, normilize

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


@app.route("/urls/<int:url_id>", methods=['GET', 'POST'])
def show_url(url_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, name, created_at
    FROM urls
    WHERE id = %s
    """, (url_id,))
    url = cursor.fetchone()

    cursor.execute("SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC", (url_id,))
    checks = cursor.fetchall()

    return render_template("url.html", id=url[0], name=url[1], created_at=url[2], checks=checks)


@app.route("/urls_list")
def urls_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT urls.id, urls.name, MAX(url_checks.created_at)
    FROM urls
    LEFT JOIN url_checks ON urls.id = url_checks.url_id
    GROUP BY urls.id
    ORDER BY urls.id DESC
    """)  # выбираем поля id, name и дату последней проверки
    urls = cursor.fetchall()
    return render_template("urls_list.html", urls=urls)


@app.route("/urls/<int:url_id>/checks", methods=['POST'])
def check_url(url_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO url_checks(url_id, created_at)
    VALUES (%s, NOW())
    RETURNING id
    """, (url_id,))
    check_id = cursor.fetchone()[0]
    conn.commit()
    flash('URL check created successfully!', 'success')
    return redirect(url_for('show_url', url_id=url_id))





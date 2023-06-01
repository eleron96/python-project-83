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
    return render_template("url.html", id=url[0], name=url[1], created_at=url[2])


@app.route("/urls_list")
def urls_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM urls ORDER BY id DESC")  # выбираем поля id, name и response_code
    urls = cursor.fetchall()
    return render_template("urls_list.html", urls=urls)







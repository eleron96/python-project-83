from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from .db import get_conn, release_conn, init_db_pool
from .urls import validate, normilize
from .database_operations import (get_url_id, get_url_data, get_checks_data,
                                  get_urls_list, get_url_name,
                                  insert_url_check)
import requests
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

init_db_pool()  # Инициализация пула соединений с базой данных


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
            return render_template("index.html", url=url), 422

    normalized_url = normilize(url)  # нормализация URL
    conn = get_conn()
    cursor = conn.cursor()
    try:
        url_id = get_url_id(cursor, normalized_url)  # используем новую функцию

        if url_id is None:
            flash("Страница успешно добавлена", "success")
        else:
            flash("Страница уже существует", "warning")

        conn.commit()
    finally:
        release_conn(conn)

    return redirect(url_for('show_url', url_id=url_id))


@app.route("/urls/<int:url_id>")
def show_url(url_id):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        url = get_url_data(cursor, url_id)
        checks_raw = get_checks_data(cursor, url_id)

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

        return render_template("url.html", id=url[0], name=url[1],
                               created_at=url[2], checks=checks)
    finally:
        release_conn(conn)


@app.route("/urls")
def urls_list():
    conn = get_conn()
    cursor = conn.cursor()
    try:
        urls_raw = get_urls_list(cursor)

        urls = []
        for url in urls_raw:
            urls.append({
                "id": url[0],
                "name": url[1],
                "created_at": url[2],
                "status_code": url[3]
            })
        return render_template("urls_list.html", urls=urls)
    finally:
        release_conn(conn)


@app.route("/urls/<int:url_id>/checks", methods=['POST'])
def check_url(url_id):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        url = get_url_name(cursor, url_id)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('show_url', url_id=url_id))

        soup = BeautifulSoup(response.content, 'lxml')
        h1_tag = soup.find('h1')
        h1_text = h1_tag.text if h1_tag else ""

        title_tag = soup.find('title')
        title_text = title_tag.text if title_tag else ""

        meta_description_tag = soup.find('meta', attrs={'name': 'description'})
        description_text = meta_description_tag['content'] \
            if meta_description_tag else ""

        insert_url_check(cursor, url_id, response, h1_text, description_text,
                         title_text)
        conn.commit()
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('show_url', url_id=url_id))
    finally:
        release_conn(conn)

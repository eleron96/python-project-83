from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from .db import get_conn, init_db_pool
from .db_queries import get_url_by_name, add_url, get_url_by_id, \
    get_url_checks_by_id, get_all_urls, add_url_check
from .urls import validate, normalize
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
def add_url_route():
    url = request.form["url"]
    errors = validate(url)
    if errors:
        for error in errors:
            flash(error, "danger")
        return render_template("index.html", url=url), 422

    normalized_url = normalize(url)  # нормализация URL
    with get_conn() as conn:
        existing_url = get_url_by_name(conn, normalized_url)

        if existing_url is None:
            url_id = add_url(conn, normalized_url)
            flash("Страница успешно добавлена", "success")
        else:
            url_id = existing_url[0]
            flash("Страница уже существует", "warning")

    return redirect(url_for('show_url', url_id=url_id))


@app.route("/urls/<int:url_id>")
def show_url(url_id):
    with get_conn() as conn:
        url = get_url_by_id(conn, url_id)
        checks = get_url_checks_by_id(conn, url_id)
    return render_template("url.html", id=url[0], name=url[1],
                           created_at=url[2], checks=checks)


@app.route("/urls")
def urls_list():
    with get_conn() as conn:
        urls = get_all_urls(conn)
    return render_template("urls_list.html", urls=urls)


@app.route("/urls/<int:url_id>/checks", methods=['POST'])
def check_url(url_id):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
        url = cursor.fetchone()[0]

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
        description_text = meta_description_tag[
            'content'] if meta_description_tag else ""

        check_id = add_url_check(conn, url_id, response.status_code, h1_text,
                                 description_text, title_text)
        print(check_id)
        flash('Страница успешно проверена', 'success')

    return redirect(url_for('show_url', url_id=url_id))

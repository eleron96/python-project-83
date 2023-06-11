from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_migrate import Migrate
from .urls import validate, normilize
import requests
from bs4 import BeautifulSoup
from .models import db
from .db_queries import *

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:14081991@localhost:5433/dev_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'

db.init_app(app)
migrate = Migrate(app, db)

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

    normalized_url = normilize(url)
    existing_url = get_url_by_name(db.session, normalized_url)

    if existing_url is None:
        new_url = Urls(name=normalized_url)
        add_new_url(db.session, new_url)
        flash("Страница успешно добавлена", "success")
        url_id = new_url.id
    else:
        url_id = existing_url.id
        flash("Страница уже существует", "warning")

    return redirect(url_for('show_url', url_id=url_id))

@app.route("/urls/<int:url_id>")
def show_url(url_id):
    url = get_url_by_id(db.session, url_id)
    checks = get_checks_by_url_id(db.session, url_id)
    return render_template("url.html", id=url.id, name=url.name, created_at=url.created_at, checks=checks)

@app.route("/urls")
def urls_list():
    urls = get_all_urls(db.session)
    return render_template("urls_list.html", urls=urls)

@app.route("/urls/<int:url_id>/checks", methods=['POST'])
def check_url(url_id):
    url = get_url_by_id(db.session, url_id).name

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
    description_text = meta_description_tag['content'] if meta_description_tag else ""

    created_at = db.func.current_timestamp()
    status_code = response.status_code

    add_new_check(db.session, url_id, created_at, status_code, h1_text, description_text, title_text)
    flash('Страница успешно проверена', 'success')
    return redirect(url_for('show_url', url_id=url_id))


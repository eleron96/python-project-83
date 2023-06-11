from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .urls import validate, normilize
import requests
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:14081991@localhost:5433/dev_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['SECRET_KEY'] = 'secret'


class Urls(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    checks = db.relationship('UrlChecks', backref='url', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class UrlChecks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('urls.id'))
    created_at = db.Column(db.DateTime)
    status_code = db.Column(db.Integer)
    h1 = db.Column(db.String)
    description = db.Column(db.String)
    title = db.Column(db.String)

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
    existing_url = Urls.query.filter_by(name=normalized_url).first()

    if existing_url is None:
        new_url = Urls(name=normalized_url)
        db.session.add(new_url)
        db.session.commit()
        flash("Страница успешно добавлена", "success")
        url_id = new_url.id
    else:
        url_id = existing_url.id
        flash("Страница уже существует", "warning")

    return redirect(url_for('show_url', url_id=url_id))

@app.route("/urls/<int:url_id>")
def show_url(url_id):
    url = Urls.query.get(url_id)
    checks = UrlChecks.query.filter_by(url_id=url_id).order_by(UrlChecks.created_at.desc()).all()
    return render_template("url.html", id=url.id, name=url.name, created_at=url.created_at, checks=checks)

@app.route("/urls")
def urls_list():
    urls = Urls.query.all()
    return render_template("urls_list.html", urls=urls)

@app.route("/urls/<int:url_id>/checks", methods=['POST'])
def check_url(url_id):
    url = Urls.query.get(url_id).name

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

    check = UrlChecks(url_id=url_id, created_at=db.func.current_timestamp(), status_code=response.status_code, h1=h1_text, description=description_text, title=title_text)
    db.session.add(check)
    db.session.commit()
    flash('Страница успешно проверена', 'success')
    return redirect(url_for('show_url', url_id=url_id))

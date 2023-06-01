from dotenv import load_dotenv
from flask import Flask, render_template, request
from .db import get_connection

load_dotenv()

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


from flask import redirect, url_for

@app.post("/urls")
def add_url():
    url = request.form["url"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id FROM urls WHERE name = %s
    """, (url,))
    existing_url = cursor.fetchone()
    if existing_url is None:
        cursor.execute("""
        INSERT INTO urls(name)
        VALUES (%s)
        RETURNING id
        """, (url,))
        url_id = cursor.fetchone()[0]
    else:
        url_id = existing_url[0]
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




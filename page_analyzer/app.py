from dotenv import load_dotenv
from flask import Flask, render_template, request
from .db import get_connection

load_dotenv()

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.post("/urls")
def add_url():
    url = request.form["url"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO urls(name)
    VALUES (%s)
    RETURNING id
    """, (url,))
    cursor.fetchone()
    conn.commit()
    return render_template("index.html")

# @app.post("/urls/<int:url_id>")
# def show_url(url_id):


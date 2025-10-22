# app.py

from flask import Flask, request, redirect, render_template
from scraper import collect_channels_to_csv
import os

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run_scraper():
    raw_queries = request.form["queries"]
    # queries = [q.strip() for q in raw_queries.strip().split("\n") if q.strip()]
    queries = [q.strip() for q in raw_queries.strip().split(", ") if q.strip()]

    output_file = "static/youtube_channels.csv"

    collect_channels_to_csv(queries, per_query=12, output_file=output_file)

    return redirect("/save.php")


@app.route("/save.php")
def save_page():
    return """
    <h2>✅ Scraping complete!</h2>
    <a href="/static/youtube_channels.csv" download>📥 Download CSV</a>
    """


if __name__ == "__main__":
    app.run(debug=True)

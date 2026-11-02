
from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from pathlib import Path
from datetime import date

app = Flask(__name__)
DB_PATH = Path(__file__).with_name("campusfind.db")

CATEGORIES = [
    "Electronics", "Bags", "Books", "Accessories", "Clothing", "Other"
]


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                report_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                report_date TEXT NOT NULL
            )
        """)


# Ensure the schema exists when the app is loaded by a production server such
# as Gunicorn, where this module is imported instead of run as __main__.
init_db()


@app.route("/", methods=["GET", "POST"])
def home():
    with get_db() as db:
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            category = request.form.get("category", "")
            location = request.form.get("location", "").strip()
            description = request.form.get("description", "").strip()
            report_type = request.form.get("report_type", "")

            if (
                not title or len(title) > 100
                or not location or len(location) > 100
                or not description or len(description) > 500
                or category not in CATEGORIES
                or report_type not in ("Lost", "Found")
            ):
                return "Invalid input. Check the form and try again.", 400

            db.execute("""
                INSERT INTO items
                (title, category, location, description,
                 report_type, status, report_date)
                VALUES (?, ?, ?, ?, ?, 'Open', ?)
            """, (
                title, category, location, description,
                report_type, date.today().isoformat()
            ))
            return redirect(url_for("home"))

        query = request.args.get("q", "").strip()[:100]
        category_filter = request.args.get("category", "")
        type_filter = request.args.get("type", "")
        status_filter = request.args.get("status", "Open")

        sql = "SELECT * FROM items WHERE 1=1"
        params = []

        if query:
            sql += " AND (title LIKE ? OR location LIKE ? OR description LIKE ?)"
            pattern = f"%{query}%"
            params.extend([pattern, pattern, pattern])

        if category_filter in CATEGORIES:
            sql += " AND category = ?"
            params.append(category_filter)

        if type_filter in ("Lost", "Found"):
            sql += " AND report_type = ?"
            params.append(type_filter)

        if status_filter in ("Open", "Resolved", "All"):
            if status_filter != "All":
                sql += " AND status = ?"
                params.append(status_filter)

        sql += " ORDER BY id DESC"
        items = db.execute(sql, params).fetchall()

        total = db.execute(
            "SELECT COUNT(*) FROM items"
        ).fetchone()[0]
        open_count = db.execute(
            "SELECT COUNT(*) FROM items WHERE status = 'Open'"
        ).fetchone()[0]
        resolved_count = db.execute(
            "SELECT COUNT(*) FROM items WHERE status = 'Resolved'"
        ).fetchone()[0]

    return render_template_string(PAGE,
        items=items, categories=CATEGORIES, query=query,
        category_filter=category_filter, type_filter=type_filter,
        status_filter=status_filter, total=total,
        open_count=open_count, resolved_count=resolved_count
    )


@app.route("/resolve/<int:item_id>", methods=["POST"])
def resolve_item(item_id):
    with get_db() as db:
        db.execute(
            "UPDATE items SET status = 'Resolved' WHERE id = ?",
            (item_id,)
        )
    return redirect(url_for("home"))


@app.route("/reopen/<int:item_id>", methods=["POST"])
def reopen_item(item_id):
    with get_db() as db:
        db.execute(
            "UPDATE items SET status = 'Open' WHERE id = ?",
            (item_id,)
        )
    return redirect(url_for("home"))


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    with get_db() as db:
        db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    return redirect(url_for("home"))


PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CampusFind | Lost & Found</title>
<style>
* { box-sizing: border-box; }
body {
    margin: 0; font-family: "Segoe UI", Arial, sans-serif;
    color: #202b3c; background: #f5f7fb; line-height: 1.6;
}
nav {
    padding: 18px 7%; display: flex; justify-content: space-between;
    align-items: center; background: white; border-bottom: 1px solid #e7edf5;
}
.logo { font-size: 24px; font-weight: 800; color: #202b3c; }
.logo span { color: #2878e5; }
nav a { text-decoration: none; color: #46556b; }
.hero {
    padding: 65px 20px; text-align: center;
    background: linear-gradient(135deg, #eaf3ff, white);
}
.eyebrow {
    font-size: 12px; font-weight: 800; letter-spacing: 2px; color: #2878e5;
}
h1 { font-size: clamp(36px, 6vw, 56px); line-height: 1.12; margin: 12px 0; }
h1 span { color: #2878e5; }
.hero p { color: #68768a; }
.container { max-width: 1100px; margin: auto; padding: 35px 20px; }
.stats {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;
}
.stat, .panel, .item {
    background: white; border: 1px solid #e5ebf3;
    border-radius: 14px; padding: 20px;
}
.stat strong { display: block; font-size: 27px; }
.stat span { color: #718096; font-size: 13px; }
h2 { margin: 0 0 15px; }
.layout {
    display: grid; grid-template-columns: 340px minmax(0, 1fr);
    gap: 22px; margin-top: 25px; align-items: start;
}
label { display: block; font-size: 13px; font-weight: 650; margin: 12px 0 5px; }
input, select, textarea {
    width: 100%; padding: 11px; border: 1px solid #dce4ef;
    border-radius: 8px; font: inherit; background: white;
}
textarea { resize: vertical; min-height: 85px; }
button, .btn {
    display: inline-block; padding: 10px 14px; border: 0;
    border-radius: 8px; cursor: pointer; font: inherit;
    text-decoration: none; background: #2878e5; color: white;
}
.submit { width: 100%; margin-top: 16px; }
.secondary { background: #eaf1fb; color: #28568e; }
.danger { background: #fff0ee; color: #b33b32; }
.filters {
    display: grid; grid-template-columns: 2fr 1fr 1fr 1fr auto;
    gap: 8px; margin-bottom: 18px;
}
.item { margin-bottom: 13px; padding: 18px; }
.item-top { display: flex; justify-content: space-between; gap: 12px; }
.item h3 { margin: 5px 0; }
.item p { margin: 7px 0; color: #68768a; font-size: 14px; }
.pill {
    display: inline-block; padding: 4px 9px; border-radius: 20px;
    background: #eaf1fb; font-size: 12px; color: #315780;
}
.pill.lost { background: #fff0e7; color: #a95121; }
.pill.found { background: #e4f8ec; color: #21834a; }
.pill.resolved { background: #e8edf2; color: #566273; }
.actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.actions button { font-size: 13px; }
.empty { text-align: center; padding: 35px; color: #718096; }
footer { text-align: center; padding: 25px; color: #718096; font-size: 13px; }
@media(max-width: 850px) {
    .layout { grid-template-columns: 1fr; }
    .filters { grid-template-columns: 1fr 1fr; }
}
@media(max-width: 500px) {
    .stats { grid-template-columns: 1fr; }
    nav { padding: 15px 5%; }
    .filters { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<nav>
    <a class="logo" href="/">Campus<span>Find</span></a>
    <a href="#report">+ Report an item</a>
</nav>

<header class="hero">
    <div class="eyebrow">YOUR CAMPUS, CONNECTED</div>
    <h1>Lost something?<br><span>Let's find it.</span></h1>
    <p>Report lost belongings, discover found items, and help them get home.</p>
</header>

<main class="container">
    <div class="stats">
        <div class="stat"><strong>{{ total }}</strong><span>Total reports</span></div>
        <div class="stat"><strong>{{ open_count }}</strong><span>Open reports</span></div>
        <div class="stat"><strong>{{ resolved_count }}</strong><span>Resolved reports</span></div>
    </div>

    <div class="layout">
        <section class="panel" id="report">
            <h2>Report an item</h2>
            <p style="color:#718096;font-size:14px">Share enough information to help identify the item.</p>
            <form method="post">
                <label for="title">Item name</label>
                <input id="title" name="title" maxlength="100" required
                       placeholder="e.g. Black backpack">

                <label for="report_type">Report type</label>
                <select id="report_type" name="report_type" required>
                    <option value="Lost">I lost an item</option>
                    <option value="Found">I found an item</option>
                </select>

                <label for="category">Category</label>
                <select id="category" name="category" required>
                    {% for c in categories %}
                    <option value="{{ c }}">{{ c }}</option>
                    {% endfor %}
                </select>

                <label for="location">Campus location</label>
                <input id="location" name="location" maxlength="100"
                       required placeholder="e.g. Library, Block A">

                <label for="description">Description</label>
                <textarea id="description" name="description" maxlength="500"
                          required placeholder="Describe the item and when it was last seen..."></textarea>

                <button class="submit" type="submit">Submit report</button>
            </form>
        </section>

        <section>
            <h2>Community board</h2>
            <form class="filters" method="get" action="/">
                <input name="q" value="{{ query }}" placeholder="Search items...">
                <select name="category">
                    <option value="">All categories</option>
                    {% for c in categories %}
                    <option value="{{ c }}" {% if category_filter == c %}selected{% endif %}>{{ c }}</option>
                    {% endfor %}
                </select>
                <select name="type">
                    <option value="">Lost & Found</option>
                    <option value="Lost" {% if type_filter == 'Lost' %}selected{% endif %}>Lost</option>
                    <option value="Found" {% if type_filter == 'Found' %}selected{% endif %}>Found</option>
                </select>
                <select name="status">
                    <option value="Open" {% if status_filter == 'Open' %}selected{% endif %}>Open</option>
                    <option value="Resolved" {% if status_filter == 'Resolved' %}selected{% endif %}>Resolved</option>
                    <option value="All" {% if status_filter == 'All' %}selected{% endif %}>All statuses</option>
                </select>
                <button type="submit">Filter</button>
            </form>

            {% for item in items %}
            <article class="item">
                <div class="item-top">
                    <div>
                        <span class="pill {{ item['report_type']|lower }}">{{ item['report_type'] }}</span>
                        <span class="pill {% if item['status'] == 'Resolved' %}resolved{% endif %}">{{ item['status'] }}</span>
                    </div>
                    <span style="color:#718096;font-size:12px">{{ item['report_date'] }}</span>
                </div>
                <h3>{{ item['title'] }}</h3>
                <p>{{ item['category'] }} · {{ item['location'] }}</p>
                <p>{{ item['description'] }}</p>
                <div class="actions">
                    {% if item['status'] == 'Open' %}
                    <form method="post" action="{{ url_for('resolve_item', item_id=item['id']) }}">
                        <button class="secondary" type="submit">Mark resolved</button>
                    </form>
                    {% else %}
                    <form method="post" action="{{ url_for('reopen_item', item_id=item['id']) }}">
                        <button class="secondary" type="submit">Reopen</button>
                    </form>
                    {% endif %}
                    <form method="post" action="{{ url_for('delete_item', item_id=item['id']) }}"
                          onsubmit="return confirm('Delete this report permanently?')">
                        <button class="danger" type="submit">Delete</button>
                    </form>
                </div>
            </article>
            {% else %}
            <div class="panel empty">
                <h3>No reports found</h3>
                <p>Try changing your filters or submit a new report.</p>
            </div>
            {% endfor %}
        </section>
    </div>
</main>
<footer>CampusFind · A student community project built with Python and SQLite</footer>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(debug=True)

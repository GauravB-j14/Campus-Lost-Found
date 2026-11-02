# CampusFind

A campus lost-and-found board built with Flask and SQLite. Students can report lost or found items, filter reports by category and status, and mark reports as resolved or reopen them.

## Run locally

Requires Python 3.10 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000/>. The app creates `campusfind.db` in the project folder on first run. That local database is ignored by Git.

## Features

- Submit lost and found reports
- Filter the community board by category, report type, and status
- Resolve, reopen, or delete a report
- SQLite storage with no external service required

## Project files

- `app.py` — Flask application and page templates
- `requirements.txt` — Python dependencies
- `.gitignore` — excludes local environments, databases, and secrets

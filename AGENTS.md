# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview
A lightweight couple interaction website built with Flask + SQLite + native CSS/JS. Features include login, timeline, photo gallery, and love letters wall. Designed for local deployment with no external CDN dependencies or complex infrastructure.

## Common Commands

**Start development server:**
```bash
python app.py
```
Runs on `http://127.0.0.1:5000` with debug mode enabled.

**Install dependencies:**
```bash
pip install -r requirements.txt
```
Only Flask and Werkzeug are required.

**Production deployment:**
```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```
For server deployment, set `debug=False` in `app.py` before running.

## Architecture & Data Flow

### Backend Structure
- **app.py**: Single Flask application file containing all routes, database logic, and utility functions
  - Routes: `/login`, `/logout`, `/`, `/photos`, `/letters`, `/timeline/delete`
  - Database: SQLite with three tables (`users`, `photos`, `letters`)
  - Timeline data: Stored in `data/timeline.json` (not in database)

### Data Storage
- **SQLite database** (`site.db`): User accounts, photos metadata (filename, uploader, timestamp), and love letters
- **JSON file** (`data/timeline.json`): Timeline events (id, event_date, title, content) - primary source of truth for timeline data
- **File system** (`static/uploads/`): Photo files with naming pattern `YYYYMMDDHHMMSS_username.ext`

### Frontend Structure
- **Base template** (`templates/base.html`): Navigation, flash message display, data attributes for timers
- **Page templates**: `login.html`, `index.html`, `photos.html`, `letters.html`
- **CSS** (`static/css/style.css`): Tailwind-style utility classes, no external dependencies
- **JavaScript** (`static/js/main.js`): Timers (love duration counter, anniversary countdown), lightbox, modals, photo preview

### Key Flows
1. **Photo upload**: File saved to `static/uploads/` → metadata inserted into `photos` table → displayed via static route
2. **Timeline management**: Data read from JSON → sorted by date (reverse) → displayed on index → deletion writes back to JSON
3. **Session management**: Login stores user_id in Flask session → `login_required` decorator protects routes → logout clears session

## Configuration
Edit these in `app.py` (top section, lines 27-45):
- `LOVE_START_DATE` / `ANNIVERSARY_DATE`: Date strings in YYYY-MM-DD format
- `USERS`: Dictionary of username → {password, display_name}
- `SECRET_KEY`: Change in production to a random string
- `ALLOWED_EXTENSIONS`: Permitted image formats
- `MAX_CONTENT_LENGTH`: Max upload size (default 8MB)

Initial timeline events can be added to `data/timeline.json` before first run, or via UI after login.

## Important Implementation Details
- Timeline JSON is the source of truth; old database `timeline` table is deprecated
- Photo filenames include timestamp and username for uniqueness
- No external API calls or CDN dependencies
- Werkzeug's `secure_filename()` sanitizes uploaded filenames
- Password hashing uses werkzeug.security
- Both users are static (configured in code, not dynamically created)
- All timestamps are stored in ISO format (YYYY-MM-DD HH:MM:SS)

## Deployment Checklist
Before pushing to production:
1. Change `USERS` passwords and display names
2. Change `SECRET_KEY` to a random string
3. Populate `data/timeline.json` with initial events
4. Set `debug=False` in the final `app.run()` call
5. Back up `site.db` and `static/uploads/` for existing deployments
6. Ensure `static/uploads/` directory is writable by the web process

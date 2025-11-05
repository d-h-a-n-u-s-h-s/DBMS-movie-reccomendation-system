# Movie Review & Recommendation System

A Flask + MySQL web app for reviewing movies and TV shows, managing friendships, and exploring recommendations based on user preferences and activity. The project includes a complete SQL schema with stored procedures, functions, triggers, and views.

## Highlights

- User accounts with roles: admin, verified_user, normal_user
- Movies and TV shows with reviews and ratings
- Friends network (add/remove, recommendations influenced by friends)
- Search & filter
  - Movies: filter by title and genre
  - Shows: filter by title and genre
  - Friends: simple search by name/email
- Admin screens to manage content
- Analytics: popular and top-rated content, active users, friendship network
- Complete MySQL schema and sample data with stored procedures, functions, triggers, and views

## Tech stack

- Backend: Flask (Python)
- Database: MySQL 8+
- ORM/DB access: mysql-connector-python (direct SQL + stored procedures)
- Templates/Frontend: Jinja2, Bootstrap, Font Awesome
- Config: python-dotenv (.env)

## Repository structure

```
. 
├─ app.py                         # Flask app with routes
├─ models.py                      # Database connection, models, analytics
├─ movie_review_system_complete.sql  # Full DB schema, procedures, functions, triggers, sample data
├─ requirements.txt               # Python dependencies
├─ static/
│  ├─ css/style.css
│  └─ js/main.js
├─ templates/                     # Jinja templates (pages)
│  ├─ base.html
│  ├─ home.html
│  ├─ movies.html                 # Now supports q & genre filter
│  ├─ shows.html                  # Now supports q & genre filter
│  ├─ movie_detail.html
│  ├─ show_detail.html
│  ├─ friends.html                # Now supports simple search
│  ├─ recommendations.html
│  ├─ register.html, login.html
│  ├─ admin_*.html                # Admin pages for content and users
│  └─ 404.html, 500.html
├─ docs/
│  └─ sql_invocations.md          # Examples to call procedures/functions and exercise triggers
└─ movie/                         # Local virtual environment (optional, can use your own venv)
```

Note: The `movie/` folder is a local virtual environment. You can ignore it and create your own venv.

## Setup

### Prerequisites

- Python 3.12 or newer
- MySQL 8.x server
- pip

### 1) Clone and enter the project

```bash
git clone <your-repo-url>
cd dbproj
```

### 2) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment variables

Create a `.env` file in the project root with your settings:

```dotenv
# Flask
SECRET_KEY=change-me

# MySQL
DB_HOST=localhost
DB_PORT=3306
DB_NAME=movie_review_system
DB_USER=root
DB_PASSWORD=your_mysql_password
```

### 5) Initialize the database

Run the full schema and sample data script (this will create the database, tables, procedures, functions, triggers, and insert sample rows):

```bash
mysql -u $DB_USER -p -h $DB_HOST -P $DB_PORT < movie_review_system_complete.sql
```

Alternatively, connect in your SQL client and execute the contents of `movie_review_system_complete.sql`.

### 6) Run the app

```bash
python app.py
```

Visit http://localhost:5000.

## Usage overview

- Home page shows recent reviews, popular and top-rated sections.
- Movies (/movies) and Shows (/shows)
  - Search by title with `q`
  - Filter by genre with `genre` (dropdown in UI)
- Friends (/friends)
  - Simple search field to filter your current friends list by name/email
  - “Add Friends” widget to search all users (excluding current user and existing friends)
- Recommendations (/recommendations)
  - Movie recommendations and suggested friends
- Admin (/admin)
  - Manage users, movies, shows, genres, celebrities, production companies

## Database features

This project ships with a full MySQL setup including:

- Stored procedures: user creation, friendships, reviews, content creation/update with details, populating and querying user preferences, analytics queries
- Functions: average ratings, user roles, content liked checks, user similarity, popularity scores
- Triggers: validate review scores, update timestamps on content and user, and update user preferences after new reviews
- Views: popular/top-rated content and active users/friendship network

See `docs/sql_invocations.md` for ready-to-run examples calling procedures/functions and for exercising triggers.

## Configuration notes

- The app uses `.env` variables via python-dotenv. Ensure the `.env` file exists before running.
- If you prefer another database host/port/name/credentials, adjust your `.env` and rerun the SQL under the correct database name.

## Troubleshooting

- “.env file not found!” in logs: Create a `.env` file (see above) and restart.
- MySQL access denied: Confirm `DB_USER`/`DB_PASSWORD`, host, and that the user has rights to create/use the database.
- Port in use: If port 5000 is busy, set `FLASK_RUN_PORT` or edit `app.py` to run on a different port.
- Schema changes: If you tweak the schema, re-run `movie_review_system_complete.sql` or apply targeted DDL/DDL+data updates.


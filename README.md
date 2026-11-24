# Portfolio

A personal portfolio website built with Django. All content (profile, education, experience,
skills, projects, certifications, blog, research, etc.) is managed from the Django admin. Nothing
is hard-coded in the templates.

## Features

- **Design**: sidebar app-shell layout with a dark/light theme toggle. It is fully responsive
  (360px–1920px) and works with Bootstrap 5 and Bootstrap Icons.
- **Homepage**: 12 dynamic sections: Hero, About, Education, Experience, Skills, Projects,
  Achievements, Certifications, Training, Blog, Research, Contact.
- **Projects**: split into Client and Personal projects. Each project supports a technology
  filter, multiple images, a detail page and GitHub/live links.
- **Skills**: grouped into Technical, Project Management and Soft skills. Subcategories can be
  edited in the admin.
- **Experience**: timeline with company logo and URL, plus an auto-calculated duration.
- **Certifications**: a dedicated page. Certificates are previewed in a modal (image or PDF).
- **Blog**: categories, tags, search, pagination and reading time. Drafts and future-dated posts
  are hidden.
- **Research**: type filter, abstract and detail pages, PDF download.
- **CV**: in-browser preview (`/cv/`) plus a download link (`/cv/download/`).
- **Contact**: a validated form that saves messages to the database. It is protected by CSRF and
  a honeypot spam trap.

## Tech stack

| Layer    | Tools                                                      |
|----------|------------------------------------------------------------|
| Backend  | Python 3, Django 6                                         |
| Frontend | HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, vanilla JS    |
| Database | PostgreSQL. SQLite is used as a fallback when no `DATABASE_URL` is set |
| Other    | Pillow, python-decouple, dj-database-url, psycopg 3        |

## Project structure

```
portfolio/
├── config/              # settings, root urls, wsgi/asgi
├── apps/
│   ├── core/            # Profile, homepage, CV views, shared utils, seed_demo command, tests
│   ├── education/  experience/  skills/  projects/  achievements/
│   ├── certifications/  training/  blogs/  research/  contact/
├── templates/           # base.html, components/, and per-app templates
├── static/              # css/main.css, css/responsive.css, js/main.js
├── media/               # uploaded files (git-ignored)
├── requirements.txt
└── .env.example
```

## Getting started (Windows)

```powershell
git clone https://github.com/ovibinzia1885/Portfolio.git
cd Portfolio
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # then edit .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ for the site and http://127.0.0.1:8000/admin/ for the admin.

On macOS/Linux, activate the virtual environment with `source venv/bin/activate` and copy the
config file with `cp .env.example .env`.

## Environment variables (`.env`)

| Variable        | Example                                                  | Notes                              |
|-----------------|----------------------------------------------------------|------------------------------------|
| `SECRET_KEY`    | `change-me`                                              | Required                           |
| `DEBUG`         | `True`                                                   | Use `False` in production          |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost`                                    | Comma-separated                    |
| `TIME_ZONE`     | `Asia/Dhaka`                                             |                                    |
| `DATABASE_URL`  | `postgres://user:password@localhost:5432/portfolio`      | Optional. If omitted, SQLite is used |

Production-only variables are used when `DEBUG=False`:

| Variable | Notes |
|---|---|
| `SECRET_KEY` | Must be at least 50 random characters, or the app refuses to start |
| `CSRF_TRUSTED_ORIGINS` | e.g. `https://example.com` |
| `ADMIN_URL` | Hard-to-guess admin path, e.g. `manage-7f3k/`. Default `admin/` |
| `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` | HTTPS settings. Secure defaults are used if these are unset |
| `MAX_UPLOAD_MB` | Upload size limit per file. Default 10 |

All of them are listed in `.env.example`.

`.env` is git-ignored. Do not commit it.

## Sample content

Run this command to load demo data:

```powershell
python manage.py seed_demo
```

Every demo record starts with `[Sample]`. To remove all demo records and files, run:

```powershell
python manage.py seed_demo --clear
```

The `--clear` option leaves your own records untouched.

## Tests

```powershell
python manage.py test
```

The test suite has 117 tests and covers models, views, URLs, forms, admin, security, SEO and
query budgets. Results are in [docs/QA_REPORT.md](docs/QA_REPORT.md).

## SEO

- `/sitemap.xml` and `/robots.txt` are generated automatically.
- Every page has its own title, meta description, canonical URL and Open Graph tags.

## Managing content

Log in to `/admin/` and fill in your content:

1. **Core › Profile**: name, headline, intro, bio, photo, social links and CV (PDF).
2. Education, Experience, Skills, Projects (with images), Certifications, Training, Achievements.
3. Blog posts, categories and tags. Research papers.
4. Messages sent through the contact form appear under **Contact**.

## Status

The site is in development and deployment has not been set up yet. Progress is tracked in
[DEVELOPMENT_PROGRESS.md](DEVELOPMENT_PROGRESS.md).

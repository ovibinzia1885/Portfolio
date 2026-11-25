# Portfolio — Nazmul Hoque Ovy

**Live site: https://nazmulhoqueovy.onrender.com**

A personal portfolio website built with Django. All content (profile, education, experience,
skills, projects, certifications, awards, blog, research, section titles, etc.) is managed from the
Django admin. Nothing is hard-coded in the templates.

> Hosted on a free plan: after a period without visitors the site sleeps, so the first visit can
> take up to about a minute to load. After that it is fast.

## Features

- **Design**: full-width sidebar layout with a dark/light theme toggle. Fully responsive from
  phones (360px) to large monitors (2560px), using Bootstrap 5 and Bootstrap Icons.
- **Homepage**: dynamic sections (About, Education, Experience, Skills, Projects, Awards,
  Certifications, Training, Blog, Research, Contact). Their titles, menu labels, order and
  visibility are edited in the admin. Empty sections are hidden from visitors.
- **Projects**: split into Client and Personal projects. Each project supports a technology
  filter, multiple images, a detail page and GitHub/live links.
- **Skills**: grouped into Technical, Project Management and Soft skills, with level dots.
- **Experience**: timeline with company logo and URL, plus an auto-calculated duration.
- **Certifications and awards**: certificates are previewed in a popup (image or PDF).
- **Blog**: categories, tags, search, pagination and reading time. Drafts and future-dated posts
  are hidden.
- **Research**: type filter, Q1/Q2 indexing badge, abstract and detail pages, PDF download.
- **CV**: in-browser preview (`/cv/`) plus a download link (`/cv/download/`).
- **Contact**: a validated form that saves messages to the database. It is protected by CSRF and
  a honeypot spam trap.
- **Statistics**: privacy-friendly visitor counter (no IP or cookies stored), total page views and
  CV download count. Shown on the admin dashboard; visitors and views also in the footer.

## Tech stack

| Layer    | Tools |
|----------|-------|
| Backend  | Python 3, Django 6 |
| Frontend | HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, vanilla JS |
| Database | PostgreSQL (Neon in production). SQLite is used as a fallback when no `DATABASE_URL` is set |
| Files    | Cloudinary in production, local `media/` folder in development |
| Hosting  | Render (Gunicorn + WhiteNoise) |
| Other    | Pillow, python-decouple, dj-database-url, psycopg 3 |

## Project structure

```
portfolio/
├── config/              # settings, root urls, wsgi/asgi, admin branding
├── apps/
│   ├── core/            # Profile, site sections/settings, homepage, CV, storage, backup/restore, tests
│   ├── education/  experience/  skills/  projects/  achievements/
│   ├── certifications/  training/  blogs/  research/  contact/
│   └── analytics/       # visitor, page view and CV download counters
├── templates/           # base.html, components/, and per-app templates
├── static/              # css/main.css, css/responsive.css, css/admin.css, js/main.js, img/
├── media/               # uploaded files in development (git-ignored)
├── render.yaml          # Render blueprint (web service)
├── build.sh             # build step on every deploy (install, collectstatic, migrate)
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
| `DATABASE_URL` | Neon connection string (`postgresql://…?sslmode=require`) |
| `CLOUDINARY_URL` | `cloudinary://API_KEY:API_SECRET@CLOUD_NAME`. Can instead be saved in **Admin › Site settings** |
| `ADMIN_URL` | Hard-to-guess admin path, e.g. `manage-7f3k/`. Default `admin/` |
| `TRUST_X_FORWARDED_FOR` | `True` behind Render's proxy (real visitor address for the counter) |
| `CSRF_TRUSTED_ORIGINS` | e.g. `https://example.com` (the Render address is added automatically) |
| `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` | HTTPS settings. Secure defaults are used if these are unset |
| `MAX_UPLOAD_MB` | Upload size limit per file. Default 10 |

All of them are listed in `.env.example`. `.env` is git-ignored. Never commit it or any password,
connection string or API key.

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

The test suite has 185 tests and covers models, views, URLs, forms, admin, security, SEO,
query budgets, responsive-safe templates, media storage, deployment settings and backup/restore.
QA reports are in [docs/](docs/).

## SEO

- `/sitemap.xml` and `/robots.txt` are generated automatically.
- Every page has its own title, meta description, canonical URL and Open Graph tags.

## Managing content

Log in to the admin (in production at the private `ADMIN_URL` path) and fill in your content:

1. **Profile & Website › Profile**: name, headline, intro, bio, photo, availability, social links and CV (PDF).
2. **Profile & Website › Site sections**: titles, menu labels, order and visibility of the home sections.
3. **Profile & Website › Site settings**: Cloudinary connection for images and files on the live site.
4. Education, Experience, Skills, Projects (with images), Certifications, Training, Achievements.
5. Blog posts, categories and tags. Research papers.
6. Messages sent through the contact form appear under **Contact**; statistics under **Visitor Statistics**.

## Deployment (free): Render + Neon + Cloudinary

| Part | Service | Notes |
| --- | --- | --- |
| Website | [Render](https://render.com) free web service | https://nazmulhoqueovy.onrender.com — `render.yaml` + `build.sh`, Singapore |
| Database | [Neon](https://neon.tech) free Postgres | AWS Singapore; no expiry, not deleted for inactivity |
| Uploaded files | [Cloudinary](https://cloudinary.com) free | Images from Cloudinary's CDN; PDFs served through `/files/` with a signed download |

**Updating the live site:** push to `main`. Render deploys automatically; `build.sh` runs
`collectstatic` and `migrate`. Content changes need no deploy: edit them in the admin.

**First-time setup (already done for the live site):**

1. Create the Neon project and the Cloudinary account. Keep the Neon connection string and the
   Cloudinary value private.
2. Render: **New › Blueprint**, pick this repository, fill in `SECRET_KEY`
   (`python -c "import secrets; print(secrets.token_urlsafe(64))"`), `DATABASE_URL`, `CLOUDINARY_URL`
   and `ADMIN_URL`.
3. Copy the local site to production:
   ```powershell
   python manage.py backup_site --output backups\to-production.zip   # local database + media
   $env:DATABASE_URL="<Neon connection string>"; $env:CLOUDINARY_URL="<cloudinary://...>"
   python manage.py migrate
   python manage.py restore_site backups\to-production.zip --replace  # empties the new database first
   python manage.py set_cloudinary "<cloudinary://...>"                # optional: store it in Site settings
   ```

**Backups:** `python manage.py backup_site` writes all database rows and uploaded files into one
zip under `backups/` (git-ignored). Run it with `DATABASE_URL` and `CLOUDINARY_URL` set to back up
the live site; restore with `restore_site`. Backup files contain the admin password hash: keep them
private. The Cloudinary secret is never written into a backup.

## Status

**Live** at https://nazmulhoqueovy.onrender.com. Progress is tracked in
[DEVELOPMENT_PROGRESS.md](DEVELOPMENT_PROGRESS.md).

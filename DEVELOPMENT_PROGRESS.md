# Development Progress

## Day 1 — Foundation (completed 2026-11-24)

- [x] Environment check (Python 3.15.2, pip 26.3, VS Code 1.147.0 OK; **Git missing**)
- [x] Project folder `portfolio`, virtualenv `venv/`
- [x] Dependencies: Django 6.1.3, Pillow, python-decouple, dj-database-url (`requirements.txt`)
- [x] `django-admin startproject config .`
- [x] Settings: `.env` config, templates, static, media, SQLite (dev) / PostgreSQL via `DATABASE_URL`
- [x] 11 apps under `apps/`: core, education, experience, skills, projects, achievements,
      certifications, training, blogs, research, contact
- [x] Models + migrations for all apps
- [x] Admin: search, filters, list_display, ordering, image preview, CRUD
- [x] Superuser `admin` created
- [x] Tests: homepage 200, admin login 200, Education/Experience/Skill create/update/delete OK

## Change request 1 (2026-11-24)

- [x] Skills restructured: 3 main categories (Technical / Project Management / Soft)
      + editable `SkillSubcategory` model; 12 technical + 12 PM subcategories seeded
- [x] Projects: single thumbnail replaced by multiple images (`ProjectImage` inline in admin)
- [ ] Soft Skills subcategories: request text was cut off at "Analytical and" - awaiting full list

## Change request 2 (2026-11-24)

- [x] Experience: added `company_url` and `company_logo` (with logo preview in admin)

## Open items
- [ ] Install Git (https://git-scm.com/download/win) and `git init`
- [ ] PostgreSQL production setup: `pip install "psycopg[binary]"` + set `DATABASE_URL`
- [ ] Day 2: public pages, Bootstrap UI, contact form, automated tests

## Run
```
venv\Scripts\activate
python manage.py runserver
```

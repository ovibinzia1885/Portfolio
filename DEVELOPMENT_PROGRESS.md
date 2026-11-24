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

## Day 2 - Frontend & functionality (completed 2026-11-24)

- [x] Design system: premium dark theme + light theme toggle (saved in browser), Inter / Space Grotesk,
      Bootstrap 5.3 + Bootstrap Icons, scroll-reveal animations (respects reduced-motion),
      files: `static/css/main.css`, `static/css/responsive.css`, `static/js/main.js`
- [x] Base frontend: `base.html`, navbar (scroll-spy, mobile menu), footer, messages (toasts),
      reusable components in `templates/components/` (section title, cards, pagination, empty state, contact form)
- [x] Homepage: Hero, About, Education, Experience (timeline), Skills (tabs by category),
      Featured Projects, Achievements, Certifications, Training, Latest Blogs, Research, Contact
      (`templates/core/sections/`) - all data comes from the database
- [x] Projects: technology filter, detail page with image gallery, GitHub + live demo links
- [x] Blog: list, detail, search, categories (`BlogCategory`), tags (`BlogTag`), pagination (6/page),
      drafts and future-dated posts hidden, reading time
- [x] Research: list (+ type filter), detail with abstract, PDF download, DOI/publication links
- [x] Contact: validated form, DB storage, success/error messages, honeypot spam trap, CSRF
- [x] Media: profile photo, project images, certificates, blog images, research PDFs, CV upload + download
      (`/cv/download/`)
- [x] Model additions: `Profile.short_intro`, `BlogCategory`, `BlogTag`, `BlogPost.category/tags`,
      duration helpers on Education/Experience
- [x] Tests: 25 automated tests (`python manage.py test`) - all passing
- [x] Responsive check (Edge headless, real viewports 360/390/820/1024/1366/1920 x 10 pages):
      no horizontal overflow, no broken images. Fixed: project card buttons were pushed outside the card.

### Change request 3 (2026-11-24)
- [x] Projects split into two parts: **Client Projects** and **Personal Projects**
      (`Project.project_type`, optional `client_name`) on the homepage and `/projects/`;
      each part has its own technology filter and empty-state message. 27 tests passing.

### Placeholder content (replace with your own)
All sample records start with `[Sample]` and text says PLACEHOLDER. Created by
`python manage.py seed_demo`; remove everything with `python manage.py seed_demo --clear`
(your own records are never touched). Placeholder images are generated gradients.
Hero/About fallback texts (shown only when Profile is empty) also tell you what to fill in.

## Open items
- [ ] Install Git (https://git-scm.com/download/win) and `git init`
- [ ] PostgreSQL production setup: `pip install "psycopg[binary]"` + set `DATABASE_URL`
- [ ] Contact: no email notification yet (messages are stored; read them in admin)
- [ ] Blog content is plain text (no rich editor / markdown)
- [ ] Deployment (not started, per instructions)

## Run
```
venv\Scripts\activate
python manage.py runserver
```

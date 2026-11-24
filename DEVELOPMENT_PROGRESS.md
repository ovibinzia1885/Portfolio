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

### Change request 4 - PostgreSQL (2026-11-24)
- [x] PostgreSQL 18 installed locally (winget, service `postgresql-x64-18`, port 5432)
- [x] Database `portfolio`, role `portfolio_user` (CREATEDB for tests); credentials only in `.env` (git-ignored)
- [x] `psycopg[binary]` added; settings now read `DATABASE_URL` from `.env` (fixed: previously ignored `.env`)
- [x] All existing SQLite data migrated (89 objects, counts verified); `db.sqlite3` kept as a local backup
- [x] 27 tests pass on PostgreSQL
- To switch back to SQLite: remove the `DATABASE_URL` line from `.env`

### Change request 5 - CV preview + download (2026-11-24)
- [x] `/cv/` preview page (PDF embedded in an iframe) with Download and Open-in-new-tab buttons
- [x] `/cv/view/` serves the PDF inline, `/cv/download/` serves it as attachment
- [x] "Preview CV" buttons in Hero, About and Footer (only when the CV is a PDF; non-PDF files fall back to download)
- [x] 30 tests passing

### Change request 6 - Redesign (2026-11-24)
Design direction inspired by a reference portfolio (style only; no text, images or branding copied):
- [x] New "terminal shell" theme: near-black + lime accent, dotted page background, JetBrains Mono body,
      Space Grotesk headings, `// label` eyebrows; light theme kept
- [x] Layout: framed app-shell with a left sidebar (numbered nav, availability, socials, theme toggle) on
      screens >= 1200px; fixed top bar + off-canvas menu below that
- [x] Hero: large headline, mono intro with caret, skill chips, framed grayscale photo
- [x] New `/certifications/` page: provider/latest/proof strip, certificate cards with image, issuer tag,
      "Credential available" status, Verify + Preview (modal for image or PDF)
- [x] `seed_demo`: real viewer-compatible sample PDFs; `--clear` now also deletes sample files
- [x] 36 tests passing; no horizontal overflow at 360-1920px on 10 pages
- [ ] PDF certificate preview in the modal could not be confirmed visually (headless browser limitation) -
      check once in a normal browser

### Change request 7 - Real CV content (2026-11-24)
- [x] All sample data removed; Profile, Education, Experience (2), Skills (11 groups / 29 skills),
      Projects (2 client + 1 personal), Certifications (6) filled from the CV; CV PDF uploaded as resume
- [x] `Certification.issue_date` is now optional (CV has no dates)
- Left empty for manual entry: photo, company logos, project images, achievements, training, blog,
  research, soft skills, certification dates/files

## Day 3 - QA & production preparation (completed 2026-11-24)
Full report: [docs/QA_REPORT.md](docs/QA_REPORT.md)
- [x] Automated tests: 36 -> **117** (models, views, URLs, forms, admin for every app); all passing
- [x] Functional: admin CRUD, search, filters, pagination, file upload, CV download verified by tests
- [x] Responsive: 8 widths (360-1920) x 10 pages, real + sample data, 0 issues (fixed 4px mobile overflow)
- [x] Security: production HTTPS/HSTS/secure cookies, strong-SECRET_KEY guard, configurable `ADMIN_URL`,
      upload type + size validation on all files, read-only contact messages, git history checked for secrets
- [x] SEO: per-page title/description, Open Graph, canonical URLs, `/sitemap.xml`, `/robots.txt`,
      research slug URLs (old numeric URLs 301-redirect)
- [x] Performance: N+1 fixed (blog tags), query-budget test, automatic image resize (max 1920px),
      lazy/async images, hashed static files in production
- [x] 9 defects found and fixed (D1-D9 in the QA report)

### Placeholder content (replace with your own)
All sample records start with `[Sample]` and text says PLACEHOLDER. Created by
`python manage.py seed_demo`; remove everything with `python manage.py seed_demo --clear`
(your own records are never touched). Placeholder images are generated gradients.
Hero/About fallback texts (shown only when Profile is empty) also tell you what to fill in.

## Open items
- [x] Git installed; repo pushed to https://github.com/ovibinzia1885/Portfolio
- [x] README.md added (features, setup, env vars, sample data, tests)
- [ ] PostgreSQL production setup: set `DATABASE_URL` on the server
- [ ] Contact: no email notification yet (messages are stored; read them in admin)
- [ ] Blog content is plain text (no rich editor / markdown)
- [ ] Deployment (not started, per instructions): decide hosting, then media/static serving,
      `collectstatic`, production `.env` (see `.env.example`)
- [ ] Admin login rate limiting (see QA report, remaining risks)

## Run
```
venv\Scripts\activate
python manage.py runserver
```

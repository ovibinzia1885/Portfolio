# QA Report — Day 3 (Quality Assurance & Production Preparation)

**Date:** 2026-11-24  
**Build:** `main` + Day 3 changes  
**Stack under test:** Django 6.1.3, Python 3.15, PostgreSQL 18 (local), Bootstrap 5.3  
**Final result:** 117 automated tests: **117 passed, 0 failed**. `check --deploy`: 2 accepted warnings.
Responsive check: **0 issues**.

---

## 1. Automated testing

Run with `python manage.py test`. Tests use a separate test database and a temporary `MEDIA_ROOT`,
so real data and uploads are never touched.

| Suite | File | Tests | Covers |
|---|---|---:|---|
| Site / Day 2 functional | `apps/core/tests.py` | 36 | All pages, link crawler, CV preview/download, seed/clear, certifications |
| Platform | `apps/core/test_platform.py` | 19 | Admin for every model, admin access control, upload validation, SEO, security settings, query budgets |
| Education | `apps/education/tests.py` | 10 | Model rules, duration, homepage, admin CRUD + file upload |
| Experience | `apps/experience/tests.py` | 6 | Duration, current job, validation, admin CRUD + logo upload |
| Skills | `apps/skills/tests.py` | 6 | Category/subcategory rules, grouping, admin CRUD/search/filter |
| Projects | `apps/projects/tests.py` | 12 | Slugs, URLs, groups, filters, detail, admin with multiple images, image resize |
| Blogs | `apps/blogs/tests.py` | 10 | Publishing, search, category/tag, pagination, XSS escaping, admin CRUD |
| Research | `apps/research/tests.py` | 6 | Slug URLs, legacy redirect, PDF download, type filter, admin + PDF validation |
| Contact | `apps/contact/tests.py` | 12 | Form rules, honeypot, CSRF, messages, read-only admin, XSS in admin |
| **Total** | | **117** | |

Areas covered: models, views, URLs, forms and admin for each app.

## 2. Functional test scenarios

| # | Scenario | Expected result | Actual result | Status |
|---|---|---|---|---|
| F1 | Add record in admin (Education, Experience, Skill, Project, Blog post, Research) | Saved, redirect to list | As expected | Pass |
| F2 | View record on site (home sections, detail pages) | Data rendered | As expected | Pass |
| F3 | Update record in admin | Change visible | As expected | Pass |
| F4 | Delete record in admin | Removed; project images cascade | As expected | Pass |
| F5 | Admin search (`?q=`) on every model with search fields | 200, matching rows | As expected | Pass |
| F6 | Admin list filters (type, status, category, read/unread) | Filtered rows | As expected | Pass |
| F7 | Project technology filter buttons | One button per technology | As expected | Pass |
| F8 | Blog search, category, tag | Correct posts only; unknown category → 404 | As expected | Pass |
| F9 | Blog pagination (6/page) | Page 2 works; page 99 → 404 | As expected | Pass |
| F10 | Research type filter; invalid type | Filtered; invalid value ignored | As expected | Pass |
| F11 | Upload PDF/image (certificate, logo, cover, project images) | Stored | As expected | Pass |
| F12 | Upload wrong type (.exe, .html, .svg, fake .png) | Rejected with form error | As expected | Pass |
| F13 | Upload larger than `MAX_UPLOAD_MB` | Rejected | As expected | Pass |
| F14 | CV preview `/cv/`, inline `/cv/view/`, download `/cv/download/` | PDF inline / attachment; 404 when no CV | As expected | Pass |
| F15 | Contact form valid / invalid / spam / no CSRF token | Saved + message / errors / silently dropped / 403 | As expected | Pass |
| F16 | Drafts and future-dated posts | Hidden from list, detail (404) and sitemap | As expected | Pass |
| F17 | Old research URL `/research/<id>/` | 301 to the new slug URL | As expected | Pass |

## 3. Responsive testing

Tool: headless Microsoft Edge. Each page was loaded at real viewport widths and checked for
horizontal overflow and broken images. Screenshots were reviewed for desktop, tablet and mobile.

| Device class | Widths | Pages | Real data | Sample data |
|---|---|---|---|---|
| Mobile | 360, 390, 414 | 10 | Pass (after fix D1) | Pass |
| Tablet | 768, 820, 1024 | 10 | Pass | Pass |
| Laptop / Desktop | 1366, 1920 | 10 | Pass | Pass |

Pages checked:
- Home, projects list, 2 project details
- Blog list, blog page 2, blog search, blog detail
- Research list, research detail
- Certifications, CV, contact, 404

## 4. Security review

| Item | Finding / action | Status |
|---|---|---|
| CSRF | Middleware on, token in every form, tested with `enforce_csrf_checks` (403 without token) | Pass |
| SECRET_KEY | Read from environment only. App **refuses to start** with DEBUG=False and a weak or default key (tested) | Pass |
| DEBUG | Defaults to `False` when not set | Pass |
| ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS | From environment | Pass |
| Environment variables | `.env` git-ignored. Git history scanned: no DB password, SECRET_KEY or account password present | Pass |
| HTTPS | When DEBUG=False: SSL redirect, secure cookies, HSTS (30 days), proxy SSL header (tested) | Pass |
| Security headers | nosniff, Referrer-Policy, X-Frame-Options SAMEORIGIN (tested) | Pass |
| File uploads | Extension allow-list per field, size limit (`MAX_UPLOAD_MB`, default 10), Pillow verifies real images. HTML/SVG not accepted | Pass (fixed D3) |
| Admin | Configurable `ADMIN_URL`, login required, non-staff blocked, 8-hour session. Contact messages read-only and cannot be created | Pass (fixed D4) |
| XSS | No `\|safe`/`mark_safe` anywhere. Blog content and contact data escaped (tested) | Pass |
| Database credentials | Only in `DATABASE_URL` (env). Not in code, docs or git | Pass |
| `check --deploy` | W019 (SAMEORIGIN needed for CV/PDF preview iframe) and W021 (HSTS preload is opt-in) accepted | Accepted |

## 5. SEO

| Item | Implementation | Status |
|---|---|---|
| Dynamic meta title | Per page, e.g. `Project title \| Name` | Pass |
| Meta description | Profile intro / project summary / post excerpt / paper abstract | Pass |
| Open Graph + Twitter card | `og:title`, `og:description`, `og:type` (article for posts/papers), `og:url`, `og:image` (cover or profile photo) | Pass |
| Canonical URL | Absolute, query strings dropped (keeps `?page=N`) | Pass |
| Sitemap | `/sitemap.xml`: static pages, projects, published posts, research | Pass |
| robots.txt | `/robots.txt` with sitemap link. Search result pages, contact page and 404 are `noindex` | Pass |
| SEO-friendly URLs | Slugs everywhere. Research moved from `/research/5/` to `/research/<title-slug>/` with 301 redirect | Pass (D5) |

## 6. Performance

| Item | Result |
|---|---|
| ORM queries | Measured on every page. No query grows with content size; a test enforces this. Home page: 17–18 queries. Other pages: 1–7 |
| N+1 fixed | Blog tags on home "Latest posts" and on blog detail "related posts" (D2) |
| Images | Uploads over 1920 px are resized and compressed automatically on save. `loading="lazy"` + `decoding="async"` on below-the-fold images. Hero photo uses `fetchpriority="high"` |
| Static files | `ManifestStaticFilesStorage` in production (hashed names, long-term caching). Bootstrap/fonts from CDN |
| Templates | Cached template loader is on automatically when DEBUG=False |

## 7. Defects found and fixed

| ID | Severity | Defect | Fix |
|---|---|---|---|
| D1 | Medium | Home page scrolled sideways by 4 px on phones (360–414 px). `g-5` row gutter was wider than the container padding | Smaller gutter below 768 px (`responsive.css`) |
| D2 | Medium | N+1 queries: one extra query per blog post for tags (home + blog detail) | `prefetch_related("tags")` |
| D3 | High | CV field accepted any file type. No upload size limit on any field. Image fields accepted any image type | Shared validators (`apps/core/validators.py`) on every file and image field |
| D4 | Medium | Contact messages from visitors could be edited, or created, in admin | Read-only fields, add permission removed |
| D5 | Low | Research used numeric URLs (not SEO-friendly) | Slug field + data migration + 301 redirect from old URLs |
| D6 | Low | `seed_demo --clear` left 5 empty sample skill subcategories behind | Clear removes empty sample subcategories |
| D7 | Low | Education accepted end date before start date, and CGPA above the scale | `Education.clean()` validation |
| D8 | Low | Certification required an issue date (CV has none) | Field made optional; page shows "—" |
| D9 | Low | Contact message had no maximum length | Limited to 5,000 characters |

## 8. Remaining risks / recommendations

| Risk | Impact | Recommendation |
|---|---|---|
| No login rate limiting on admin | Brute-force attempts possible | Strong password + custom `ADMIN_URL`. Add host-level rate limiting, or `django-axes` if allowed |
| Media files in production | Django does not serve `/media/` when DEBUG=False | Configure the web server or host (or object storage) to serve `media/` at deployment |
| Static files in production | Need `collectstatic` and a static server | Decide at deployment (web server or WhiteNoise) |
| PDF certificate preview modal | Not verified visually (headless browser cannot render PDFs) | Check once in a real browser |
| No email notification for contact messages | Messages are only visible in admin | Add SMTP settings when deploying |
| Sample-data clear matches subcategory names | A real, *empty* subcategory with the same name as a sample one would be removed by `seed_demo --clear` | Low. Only affects empty subcategories |
| CDN dependency (Bootstrap, fonts) | Styling degrades if the CDN is unreachable | Acceptable. Self-host later if needed |
| Real content gaps | Achievements, training, blog, research, soft skills, logos, certificate dates/files are empty | Owner to fill in via admin |

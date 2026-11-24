# Final QA Report — Release Candidate

**Date:** 2026-11-24  
**Tester role:** Senior SQA (full regression + exploratory)  
**Build:** `main` + all changes up to and including the admin redesign and favicon  
**Environment:** Windows 10, Python 3.15.2, Django 6.1.3, PostgreSQL 18.7 (local, real content), Microsoft Edge (headless) for rendering  
**Earlier report:** [QA_REPORT.md](QA_REPORT.md) (Day 3)

## Verdict

**Ready for release (deployment preparation).** No open blocker, critical or major defects.

- **Defects:** 6 were found in this cycle. All 6 are fixed and covered by regression tests or re-checks.
- **Remaining items:** these are configuration and content tasks, listed in section 6.

| Area | Result |
|---|---|
| Automated tests | **130 / 130 passed** (128 before this cycle + 2 new) |
| System / migration checks | `check`: 0 issues · `makemigrations --check`: no pending changes |
| Public pages crawled (real data) | 26 URLs, **0 broken** (one intentional 404 test) |
| Assets (images, PDFs, CSS/JS, icons) | 24, **0 missing** |
| Admin pages opened (real data) | **190**: dashboard, every list/search/filter/add/edit/history page. **0 errors**, none slower than 800 ms |
| External links | 21: 18 OK. 3 are blocked by the remote site for bots (MDPI ×2, LinkedIn). Those links were verified manually (DOI via Crossref), so they are not defects |
| Responsive (8 widths × 21 pages) | 360, 390, 414, 768, 820, 1024, 1366, 1920 px: **0 overflow, 0 broken images** |
| Colour contrast (WCAG AA) | 14 colour pairs, light and dark theme plus admin. **All ≥ 4.5 : 1** (lowest 5.31) |
| Security (`check --deploy`) | 2 accepted warnings (W019, W021). No secrets in git history or tracked files |
| Performance | Max 15 DB queries per page (home), and the count does not grow with content. Home HTML 63 KB |

## 1. Scope and approach

1. **Regression:**
   - Full unit and integration suite (`python manage.py test`).
   - System checks and a check for missing migrations.
2. **Functional crawl on real data:**
   - Every link reachable from the home page was followed. 26 pages, read-only.
   - Every image, PDF, CSS and JS file was resolved.
3. **HTML quality:**
   - Image alt text, duplicate IDs, one h1 per page, heading order.
   - Form labels, links and buttons without a name, `target=_blank` without `noopener`.
4. **SEO:**
   - Title and description present and within length (≤ 70 / ≤ 160 characters).
   - Duplicates, canonical URL, Open Graph tags, sitemap, robots.txt.
5. **Admin:** all registered models, read-only.
   - Changelist, search, boolean filters and add form.
   - Change form and history for every record.
   - Password change page.
6. **External links:** live HTTP check.
7. **Responsive and visual:**
   - Overflow, broken images and tap-target sizes at 8 viewport widths.
   - Screenshots reviewed for desktop, mobile, light theme, certificate preview and award popup.
8. **Accessibility:**
   - WCAG AA contrast calculation.
   - Focus outline, skip link and reduced-motion support.
   - Tap target size 2.5.8.
9. **Security:**
   - `check --deploy` with production settings.
   - User and role review.
   - Scan for tracked secrets and temporary files.

## 2. Test scenarios and results

| # | Scenario | Expected | Actual | Status |
|---|---|---|---|---|
| S1 | Open every public page | 200, correct content | 26/26 as expected | Pass |
| S2 | Unknown URL | 404 page, `noindex` | 404 | Pass |
| S3 | CV preview / inline / download | Inline PDF, attachment | Inline PDF + attachment (186 KB) | Pass |
| S4 | Certificate Preview (image, PDF + preview image) | Popup shows the image; Download gives the original file | As expected, checked by screenshot | Pass |
| S5 | Award photo / certificate popup | Opens in the shared popup | As expected | Pass |
| S6 | Research: slug URLs, old numeric URL, PDF download | 200 / 301 / attachment | As expected | Pass |
| S7 | Projects: client/personal groups, technology filter, detail pages | Correct grouping and links | As expected | Pass |
| S8 | Blog: empty state, search, pagination (covered by tests) | Empty state now; tests pass | As expected | Pass |
| S9 | Contact form: valid, invalid, honeypot, CSRF (tests) | Saved / errors / dropped / 403 | As expected | Pass |
| S10 | Admin: dashboard, all list/edit/history pages | 200, no server error | 190 pages, 0 errors | Pass |
| S11 | Admin: contact message add | Blocked by design | 403 | Pass |
| S12 | Sitemap / robots.txt | Valid, no drafts, admin path not exposed | As expected | Pass |
| S13 | Browser icon, `/favicon.ico` | Bug icon; `/favicon.ico` redirects | As expected | Pass |
| S14 | Hero photo | Colour by default, B&W on hover | As expected | Pass |
| S15 | Light / dark theme | Readable, contrast AA | All pairs ≥ 4.5 : 1 | Pass |
| S16 | Mobile 360–414 px on all pages | No sideways scroll | 0 after fix QA2-01 | Pass |

## 3. Defects found in this cycle (all fixed)

| ID | Severity | Defect | Fix | Verified by |
|---|---|---|---|---|
| QA2-01 | Medium | At 360 px, the research page "QA in CI/CD…" scrolled sideways by 6 px. The long word "Integration/Continuous" could not wrap | New `soft_wrap` filter allows a break after "/" in titles. Headings use `overflow-wrap: break-word` | Responsive re-run: 0 issues. Screenshot |
| QA2-02 | Low | The first fix for QA2-01 (`overflow-wrap: anywhere`) broke words mid-word ("Continuou-s"). Found by visual review | Replaced by the break-after-"/" approach | Screenshot |
| QA2-03 | Low (a11y) | Heading levels skipped from h1 to h3 on `/projects/` and `/certifications/` | Project group heading level is now configurable (h2 on the projects page). Hidden h2 added on the certifications page | New test `test_heading_outline_has_no_skipped_levels` |
| QA2-04 | Low (SEO) | 10 research page titles were 92–139 characters and 2 descriptions were 198–210 characters. Search results cut them off | Title truncated to 50 characters + site name. Descriptions limited to 155 characters (research, blog, project detail) | Crawl re-run: 0 length issues |
| QA2-05 | Low (a11y) | "Verify / Download / Preview" links and breadcrumbs were smaller than 24 px tap targets on phones | `.link-arrow` min-height 32 px, extra padding on breadcrumbs | Responsive re-run |
| QA2-06 | Low (UI) | The mobile top bar showed the letter "N" while the desktop sidebar showed the profile photo | Top bar uses the profile photo, with the letter as fallback | Screenshot |

## 4. Observations (not defects)

- **Inline links under 24 px** (email, phone, DOI, company name) remain. They are inline text links, which WCAG 2.5.8 exempts.
- **External links that block bots:** `mdpi.com` and `doi.org/10.3390/…` return 403 to automated requests, and LinkedIn times out. All three open normally in a browser. The DOI was confirmed through Crossref.
- **Large PDFs:** two certificate PDFs are about 1 MB each (ISTQB 0.94 MB, Django 1.06 MB). They download only on demand, and the cards use preview JPEGs, so page load is not affected.
- **Deploy warnings:**
  - W019 (`X_FRAME_OPTIONS = SAMEORIGIN`) is needed for the CV and certificate preview iframes.
  - W021 (HSTS preload) is intentionally opt-in.

## 5. Accounts review

| User | Role | Note |
|---|---|---|
| `admin` | Superuser | Works. **Recommendation:** change the username to something hard to guess. Use a strong password: the first password was shown once during setup |
| `ovy` | Regular user (not staff), never logged in | Not needed by the site. **Recommendation:** delete it in Admin › Users, or keep it inactive |

## 6. Remaining risks and recommendations before going live

| # | Item | Owner action |
|---|---|---|
| R1 | No admin login rate limiting | Strong password and custom `ADMIN_URL`. Add rate limiting at the host, or `django-axes` if allowed |
| R2 | Media and static files in production | Decide the hosting, then serve `media/` and run `collectstatic` (WhiteNoise or web server) |
| R3 | Contact messages only visible in admin | Optionally configure SMTP for email notifications |
| R4 | Content gaps | Blog posts, training, soft skills, research abstracts (9 papers), the Information Security certificate file, the exact award date, higher-resolution award images, and the SIMEC designation |
| R5 | Research abstract for the 2023 JMR paper is a draft | Replace it with the real abstract |
| R6 | Browser coverage | Rendering was checked in Chromium (Edge). Also do a quick manual check in Firefox and Safari (iOS) |

## 7. Artifacts

- **Tests:** `apps/*/tests.py`, `apps/core/test_platform.py` (130 tests).
- **QA scripts:** crawl, admin sweep, external links, responsive and contrast. They were run from a scratch folder and are not part of the repository, because they use local data.
- **Temporary QA pages:** `static/_vp_*.html` were created for rendering checks and **deleted**. A temporary admin session was created for screenshots and **deleted**.

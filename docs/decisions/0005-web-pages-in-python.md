# 0005 The web app: server-rendered pages in FastAPI

**Decision.** The Week 2 web app is rebuilt as pages served by the same FastAPI app, under `/app`. Jinja2 templates, the Week 2 CSS, no JavaScript framework.

**Why not keep the Next.js front end.** The brief fixes the stack to Python with FastAPI and says the front end is not part of the project. A server-rendered version keeps one language, one container and one command. The old front end would also have needed a CORS setting and a rewritten API client.

**Layers.** The page routes read a form, validate it with the existing schemas, call a service and render a template. They do not touch the database, and the API routes are unchanged. Everything under `app/web/` can be deleted without affecting the API.

**Sessions.** A form post cannot send an Authorization header, so the JWT the API issues is stored in a cookie. It is HttpOnly (page scripts cannot read it) and SameSite=Lax (browsers do not send it on cross-site form posts, which is the protection against CSRF). It is not marked Secure because the project runs on plain http://localhost. Behind HTTPS it should be.

**Details worth knowing.**
- After every form post the page redirects (303) to a GET, so refreshing does not re-submit the form.
- The notice after an action comes from a short code in the address (`?msg=added`) that maps to a fixed text, so nobody can put their own words on the page.
- Jinja escapes everything by default. A title like `<script>` is shown as text. There is a test for this.
- Search and sort happen in `app/web/views.py`, because the API only filters by status. They are plain functions with their own tests.
- The only JavaScript is a confirm box before delete. Without it, delete still works.

**Trade-off.** It is more to explain and more to test, and the brief says extra features earn no credit. It is the first thing on the cut list.

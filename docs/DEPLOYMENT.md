# Deployment & Debugging Guide

How this app runs in production, and how to figure out what's wrong when
something breaks — **starting with the things you can do yourself, without
needing access to the server.**

---

## 1. The big picture

When you push to `main`, your app deploys automatically to a Linux server
("WEB02") that Dan runs. Here's the whole shape of it:

```
  You push to main
        │
        ▼
  GitHub Actions ──SSH──▶  WEB02 (Ubuntu server)
                            │
                            ├─ nginx            ← the web server; the front door
                            │    ├─ /       → your web page (frontend/index.html)
                            │    ├─ /api/*  → your FastAPI app
                            │    └─ /health → your FastAPI app
                            │
                            ├─ openmat.service  ← your FastAPI app, run by uvicorn
                            │                     (a Linux "systemd service")
                            │
                            └─ (no database here)
                                      │
                                      ▼
                            Neon  ← your Postgres database, hosted separately
```

Two things to internalize:

- **The database is not on the server.** It lives on [Neon](https://neon.tech).
  The app talks to it over the network.
- **nginx is the front door.** Every request hits nginx first, and nginx
  decides whether to serve a static file (your web page) or hand the request
  to your Python app (`/api/...`).

---

## 2. What happens on a deploy

Every push to `main` triggers `.github/workflows/deploy.yml`, which connects
to the server and runs, in order:

1. `git reset --hard origin/main` — grab your latest code.
2. `pip install -r requirements.txt` — install any new Python dependencies.
3. `rsync frontend/ → webroot` — publish your web page.
4. Write the database URL (from a GitHub secret) into the app's config file.
5. Restart the app and check `/health`.

**If any step fails, the deploy goes red in the Actions tab** — so a broken
deploy is loud, not silent.

### What auto-updates, and what doesn't

| Changes when you push | Does **not** change on its own |
|---|---|
| Python code (`api/`) | Database schema / tables |
| Web page (`frontend/`) | Database data (seeds) |
| Python dependencies (`requirements.txt`) | Secrets / environment variables |

Database migrations and seed data are **not** run by the deploy. If you change
the schema or need to load data, you do that yourself against Neon from your
own machine (you have the connection string). Ask Dan if you'd like a migration
step added to the deploy.

---

## 3. Config & secrets

The app reads its database URL from an environment variable. That value comes
from a **GitHub Actions secret** named `DATABASE_URL_UNPOOLED`
(Settings → Secrets and variables → Actions).

> **Why "unpooled"?** Neon gives you two connection strings — a "pooled" one
> (goes through Neon's own connection pooler) and an "unpooled"/"direct" one.
> This app runs its *own* connection pool, so it needs the **unpooled** URL.
> Using the pooled one causes subtle breakage. If you ever rotate the Neon
> password, update this secret with the **unpooled** string.

**To add a new environment variable** (say an API key) you need two things, and
the second one needs Dan (or someone with server access):

1. Add a new GitHub secret (you can do this — you own the repo).
2. Update `deploy.yml` so the deploy writes that secret into the app's config
   file. (Copy the pattern already used for `DATABASE_URL_UNPOOLED`.)

---

## 4. Debugging — what you can do **without** server access

Try these in order. Most problems are solvable right here.

### a. Did the deploy actually succeed?
Open the **Actions** tab in GitHub. A red ✗ means the deploy failed — click in
and read the failing step. A green ✓ means your code is live on the server.

### b. Is the app up at all?
Visit **https://openmat.hirebekah.com/health** — it should say
`{"status":"ok"}`. If that works, the app is running and nginx is routing to it.

### c. Reproduce the failing request
Open your browser's **DevTools → Network tab**, use the site, and watch the
failing request. The **status code** tells you a lot:

- **500** — the app crashed handling the request (a bug, or a database
  problem — see the Neon note below).
- **404** — nginx couldn't find it (wrong path, or the frontend didn't publish).
- **502 / 503** — the app isn't running (check `/health`).

You can also reproduce from a terminal:

```bash
curl -i "https://openmat.hirebekah.com/api/search?lat=30.2672&lng=-97.7431&radius_km=25"
```

### d. ⚠️ The Neon "cold start" gotcha (known issue)
On the **free Neon tier, the database auto-suspends after ~5 minutes of no
activity.** The very first request after an idle period can fail with a 500,
then work fine on a retry. In the logs this looks like:

```
psycopg.errors.AdminShutdown: terminating connection due to administrator command
```

This is **not your code being wrong** — it's the app holding a database
connection that Neon quietly closed during suspend. **A fix is in progress**
(validating each connection before use). Until it ships, if you see a single
500 right after the site's been quiet, **retry once** — it should recover.

---

## 5. Server internals (reference)

You don't need these day-to-day, but here's where things live, so the logs and
paths make sense:

| Thing | Where |
|---|---|
| App code | `/opt/openmat/app` |
| Python virtualenv | `/opt/openmat/venv` |
| Config file (holds the DB URL) | `/opt/openmat/openmat.env` (locked down, `0600`) |
| The service | `openmat.service` (systemd), run by user `openmat`, on `127.0.0.1:8000` |
| Web page files | `/var/www/openmat.hirebekah.com/` |
| Logs | `journalctl -u openmat` (needs server access) |

The app is run as a locked-down user with a hardened service config (no extra
privileges, filesystem mostly read-only to it). The config file holding the
database password is readable only by that user.

---

## 6. Reading the live server logs yourself

The real-time application logs — every request and full error traceback — live
on the server. You can get your **own read-only access** to them: a login that
does exactly one thing, show this app's live logs, and nothing else (no shell,
no other sites, no database password). It's safe by design.

Setting it up is a one-time, three-step process.

### Step 1 — Create an SSH key (or reuse one you have)

An SSH key is a pair of files: a **private** key (stays secret on your computer —
*never* share it) and a **public** key (safe to share — it's what lets the server
recognize you).

If you already have one — for example the key you use with GitHub, usually at
`~/.ssh/id_ed25519.pub` — you can skip to Step 2 and use that.

Otherwise, generate one. On **macOS/Linux** open Terminal, or on **Windows** open
PowerShell, and run:

```bash
ssh-keygen -t ed25519 -C "openmat logs"
```

Press Enter to accept the default location. A passphrase is optional (press Enter
twice to skip it). This creates two files in your `.ssh` folder:

- `id_ed25519`      ← your **private** key — keep secret, never send it
- `id_ed25519.pub`  ← your **public** key — this is the one you share

### Step 2 — Send Dan your **public** key

Print the public key and copy the whole line it outputs:

```bash
cat ~/.ssh/id_ed25519.pub                      # macOS / Linux
# Windows PowerShell:
type $env:USERPROFILE\.ssh\id_ed25519.pub
```

It looks like `ssh-ed25519 AAAAC3Nza... openmat logs`. Send **that entire line**
to Dan (Slack or email is fine — a public key is not a secret). He installs it
and tells you when it's ready.

> ⚠️ **Only ever send the `.pub` one.** If a file's contents start with
> `-----BEGIN OPENSSH PRIVATE KEY-----`, that's your **private** key — never send
> that to anyone, ever.

### Step 3 — Connect and watch the logs

Once Dan confirms your key is installed, run:

```bash
ssh bekah@web02.sitedriveinc.com
```

You'll immediately see the most recent log lines, then new ones stream in live as
the app handles requests. Press **Ctrl-C** (or close the window) to stop.

This login drops you straight into the log view — it is **not** a shell. You
can't run other commands, reach other sites, or see the database password. That's
intentional: it's scoped to just this app's logs.

### Reading what you see
- A normal request: `INFO: ... "GET /api/search?... " 200 OK`
- An error: a `500` followed by a **Traceback** — the *last* line names the real
  error (e.g. the Neon `AdminShutdown` from the cold-start note in Section 4).
- Stuck? Copy the traceback and send it to Dan.

---

## 7. Common tasks

**Change the web page:** edit `frontend/index.html`, push to `main`. It's live
within a minute or two.

**Roll back a bad change:** revert the commit and push.
```bash
git revert <bad-commit-sha>
git push
```
The deploy re-runs and the previous version goes live.

**Add a Python dependency:** add it to `requirements.txt`, push. The deploy
installs it automatically.

**Load / change database data:** connect to Neon from your own machine using
your connection string and run your SQL or migration there. The server doesn't
touch the schema.

---

## 8. Who to contact

- **Deploy failed (red in Actions):** read the failing step first; most are a
  typo or a missing dependency you can fix and re-push.
- **A 500 or odd behavior:** check the live logs yourself (Section 6) — the
  traceback usually names the cause. If it's not clear, send the traceback to Dan.
- **App is fully down (even `/health` fails):** ping Dan.
- **Database (Neon) questions:** that's yours to manage, but Dan can help think
  it through.

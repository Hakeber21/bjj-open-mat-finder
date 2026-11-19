# BJJ Open Mat Finder: Project Context

*Living document. Update it when a decision changes. Anything marked **[DECIDE]** is an open question for the builder. A copy also lives in the "BJJ Open Mats" Claude Project.*

## 1. One-liner
A free, map-based tool that helps BJJ practitioners find open mat sessions near home or while traveling, including at gyms that are hard to find online. **Launch region: Austin, TX.** **Live at: openmat.hirebekah.com** (once deployed).

## 2. Problem
- Open mat info is scattered across gym websites, Instagram stories, Facebook groups and word of mouth.
- Search (Google Maps, etc.) surfaces only the most digitally visible gyms. Small, quality, lineage-focused or garage gyms get missed.
- Travelers can't tell whether a gym welcomes visitors, what it costs, whether it's gi or no-gi, or whether the listed time is still true.
- Cross-training is a core part of BJJ culture, so this is a real, felt problem.

## 3. Users
| User | Need |
|---|---|
| **Traveling practitioner** (primary) | "I'm in a new city for 3 days. Where can I roll Saturday, and will they let me in?" |
| **Local cross-trainer** | Find open mats outside their home gym's schedule. |
| **Gym owner** (secondary) | Get listed and keep their schedule accurate, with minimal effort. |

## 4. Builder goals (equal weight)
1. **Functional.** It works and returns useful results for real places.
2. **Explainable.** Every decision can be defended in an interview: why this data model, why this stack, what was traded off.
3. **Memorable.** A recruiter or hiring manager should remember it, and it should show I understand data, product thinking and AI-native workflows.
4. **Time-efficient.** AI agents do the building so I can spend my time training and building relationships.

## 5. Constraints
- **Cost: $0 or near-$0.** Solo builder. Only free tiers and open-source tools. Verify free-tier limits before committing, because they change.
- **Review comfort:** SQL and Python. I can confidently review those, so keep the core logic in them and keep the frontend thin.
- **Solo maintainer.** Prefer boring, low-maintenance choices.
- **Legal and ethical:** respect each site's ToS and robots.txt, store no sensitive personal data, and credit data sources (OSM requires attribution).

## 6. Scope

### MVP (ship first)
- Search by city or "near me" and see a map and list of gyms with open mats.
- Filters: day of week, gi / no-gi / both, visitor-friendly, free vs. drop-in fee.
- Gym detail: schedule, visitor policy, fee, belt or experience requirements, contact and link, **last verified date**.
- Submit a gym or open mat, and flag outdated info (simple form, moderated).
- **Lightweight owner claim (no accounts):** an owner submits a claim form, and I verify them manually (e.g. email from the gym's own domain or a DM from the gym's Instagram). Verified owners' info is marked `verified_by = 'owner'`. Self-serve owner logins come later.

### Differentiator (what makes it more than a directory)
- **Freshness / confidence score.** Show how recently each listing was confirmed and by whom (owner, visitor, auto-check). Stale data is the main failure mode of this category.
- **Coverage of "invisible" gyms.** Seed from open data, then grow through community submissions.
- **Traveler mode.** "I'm in [city] from [date] to [date]" returns a ranked list of what's open then.

### Non-goals (for now)
User accounts and social features, payments or booking, native mobile app, reviews or ratings, self-serve owner dashboards, coverage beyond Austin on day one.

## 7. Data

### Sources (cheapest first)
1. **OpenStreetMap**: free, open license. Seed gym locations and names via martial-arts or sports tags. Needs attribution.
2. **Community submissions**: the core long-term source.
3. **Gym-owner claims**: the lightweight claim flow above.
4. **Gym websites and public schedules**: scrape only where ToS and robots.txt allow, and always human-verify before publishing.
- Avoid paid APIs. Google Places is the usual option but has costs and strict caching rules, so treat it as out of scope unless a free allowance clearly covers it.

### Draft schema (Postgres; I review in SQL)
```sql
CREATE TABLE gym (
  id            BIGSERIAL PRIMARY KEY,
  name          TEXT NOT NULL,
  address       TEXT,
  city          TEXT,
  country       TEXT,
  lat           DOUBLE PRECISION,
  lng           DOUBLE PRECISION,
  website_url   TEXT,
  instagram     TEXT,
  source        TEXT NOT NULL,            -- 'osm' | 'submission' | 'owner'
  visitor_policy TEXT,                    -- 'welcome' | 'call_first' | 'members_only' | 'unknown'
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE open_mat (
  id            BIGSERIAL PRIMARY KEY,
  gym_id        BIGINT REFERENCES gym(id),
  day_of_week   SMALLINT CHECK (day_of_week BETWEEN 0 AND 6),
  start_time    TIME NOT NULL,
  end_time      TIME,
  format        TEXT CHECK (format IN ('gi','nogi','both')),
  fee_cents     INTEGER,                  -- NULL = unknown, 0 = free
  min_belt      TEXT,
  notes         TEXT,
  last_verified_at TIMESTAMPTZ,
  verified_by   TEXT                      -- 'owner' | 'visitor' | 'agent_check'
);

CREATE TABLE submission (
  id            BIGSERIAL PRIMARY KEY,
  payload       JSONB NOT NULL,
  status        TEXT DEFAULT 'pending',   -- 'pending' | 'approved' | 'rejected'
  created_at    TIMESTAMPTZ DEFAULT now()
);
```
Core query to get right: open mats within radius X, on a given day, filtered by format and visitor policy, ranked by freshness. Austin is a small dataset, so plain-SQL Haversine is enough for MVP; PostGIS is optional later (verify it's available on the chosen host).

## 8. Stack
| Layer | Choice | Why |
|---|---|---|
| Language / API | Python + FastAPI | I can review it |
| Database | **Postgres on a free hosted tier** (see ADR 0001) | SQL-first, easy to explain |
| Map | Leaflet + OpenStreetMap tiles | Free, no API key |
| Frontend | Minimal static page (vanilla JS or a light framework) | Keep the review surface small |
| Hosting | Static host (a friend hosts the main site; DNS is at Hover) + free-tier API host **[DECIDE]** | $0 |
| Domain | `openmat.hirebekah.com`, a CNAME record in Hover DNS pointing at the host | Own domain, free HTTPS from the host |
| CI | GitHub Actions | Free for public repos |
| Repo | Public GitHub repo with a strong README | Recruiters read this first |

### Database decision (checked 2026-11-16; re-verify before relying on it)
- **Neon free:** about 1 GB storage per project; compute scales to zero after 5 minutes idle and wakes in a few hundred milliseconds on the next query. Data is not paused or removed for inactivity.
- **Supabase free:** 500 MB database; **projects pause after 1 week of inactivity** and must be resumed manually.
- **Leaning Neon.** A portfolio site gets sporadic visits, and a paused database would make the demo look broken exactly when a recruiter clicks it. See `docs/decisions/0001-hosted-postgres.md`.

## 9. AI-native operating model: the agent team
The goal is to hand building to agents and keep me as **product owner and reviewer**. Each agent has a defined role, inputs, outputs and a human checkpoint.

**Runner: Claude Code subagents**, defined in `.claude/agents/` (`designer`, `engineer`, `pr`). This doc is the shared context all three read first.

- **Designer:** UX flows, wireframes, copy, visual system. *Checkpoint: I approve the look and flow before the engineer builds it.*
- **Engineer:** schema, ingestion, API, frontend, tests, CI. Small PRs, ADRs for decisions. *Checkpoint: I review all SQL and Python before merge.*
- **Public relations:** README, case study, demo narrative, outreach drafts. Never overclaims; reports only real numbers. *Checkpoint: I approve all public text and send outreach myself.*

### Working agreements for all agents
- Read this doc first. Propose changes to it rather than silently diverging.
- Keep a running **decision log** in `docs/decisions/` (what, why, alternatives rejected). It feeds the PR agent's case study.
- Small steps and visible progress. If blocked or ambiguous, ask rather than guess on anything irreversible.

### Visual identity (for the designer agent)
Two gradients, both supplied by the builder. The HSL values are the source of truth.

**1. Belt gradient (the product's BJJ identity).** Runs through the belt colors: white, blue, purple, brown, black.
```css
/* fallback solid color first, then the gradient */
background: hsla(220, 55%, 68%, 1);
background: linear-gradient(
  90deg,
  hsla(220, 55%, 68%, 1) 0%,    /* white belt — periwinkle, reads as lightest stop; shifted from pure pale-gray for legibility of white text */
  hsla(228, 92%, 47%, 1) 14%,   /* blue belt   (about #0A36E8) */
  hsla(272, 94%, 49%, 1) 35%,   /* purple belt */
  hsla(27, 53%, 25%, 1) 58%,    /* brown belt  */
  hsla(20, 79%, 7%, 1) 81%      /* black belt  */
);
```

**2. hirebekah gradient (the builder's personal brand).** From `#43BECA` to `rebeccapurple` (`#663399`).
```css
background: hsla(185, 56%, 53%, 1);
background: linear-gradient(90deg, hsla(185, 56%, 53%, 1) 0%, hsla(270, 50%, 40%, 1) 100%);
```

Notes for the designer:
- The builder's tool exported older vendor-prefixed versions (`-moz-`, `-webkit-`) and an IE `filter`. Modern browsers don't need them, so use the standard `linear-gradient` above with the solid fallback.
- The belt gradient goes from very light to near black, so **no single text color works on top of it**. Use it as an accent (borders, header strips, dividers, progress bars), not as a background behind text, unless the text sits on a solid panel. Check contrast on anything placed near it.
- Don't rely on belt color alone to carry meaning (for example a minimum-belt badge). Always pair color with a text label.
- Roles: the belt gradient is the product's signature element; the hirebekah gradient is the builder credit ("Built by Rebekah" in the footer, linking back to the portfolio site).

## 10. Milestones
1. **Foundations:** repo, agent definitions, schema, seed data for Austin, a basic API query.
2. **Core search:** map and list, filters, gym detail page.
3. **Trust layer:** submissions, moderation queue, owner claim, last-verified display.
4. **Traveler mode and polish:** date-range search, mobile pass.
5. **Launch:** README, demo, case study, share with Austin gyms and BJJ communities.
6. **Learn:** collect early feedback, iterate.

## 11. Success measures
- **Product:** number of gyms with verified open mats in Austin, and how many were not on Google's first page (the "invisible gym" proof point). Count real submissions and return visits.
- **Career:** a live demo link, a clean repo, a written case study, and at least one concrete story about a trade-off I made.

## 12. Risks
| Risk | Mitigation |
|---|---|
| Stale or wrong schedules | Freshness score, "report outdated" button, verification dates shown prominently |
| Cold start (empty map) | Launch in Austin, and seed it by hand and from OSM |
| Free-tier limits or sleeping hosts | Static-first design, cache aggressively, know the limits up front; Neon wake-up is a few hundred ms |
| Scraping and ToS issues | Prefer open data and submissions; human-verify anything scraped |
| Fake owner claims | Manual verification via the gym's own domain or Instagram before marking `owner` |
| Agents produce code I can't explain | Mandatory review, ADR per major decision, small PRs |
| Scope creep | Hold the non-goals list; ship MVP first |

## 13. Decisions and open questions
| # | Question | Status |
|---|---|---|
| 1 | Launch region | **Decided: Austin, TX** |
| 2 | Database | **Decided: hosted Postgres; leaning Neon free tier** (ADR 0001) |
| 3 | Owner claims in v1 | **Decided: yes, as a lightweight manual-verified flow** (no accounts) |
| 4 | Agent runner | **Decided: Claude Code subagents** |
| 5 | Name and domain | **Decided: BJJ Open Mat Finder at `openmat.hirebekah.com`** (DNS managed at Hover) |
| 6 | Static and API hosting | **[DECIDE]** friend hosts the main site (CNAME target likely `web02.sitedriveinc.com`, to confirm); need to learn whether it can run Python; API host still open, watch for hosts that sleep when idle |

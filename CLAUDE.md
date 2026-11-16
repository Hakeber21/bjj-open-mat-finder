# BJJ Open Mat Finder

A free, map-based tool for finding BJJ open mat sessions near home or while traveling, including at gyms that are hard to find online. Launch region: Austin, TX. Live at openmat.hirebekah.com once deployed.

**Read `docs/context.md` first.** It is the source of truth for goals, scope, constraints, schema and decisions. If you think it should change, propose the edit in your reply. Do not silently diverge from it.

## Who I'm working with
The builder is a solo developer who is comfortable reviewing **SQL and Python**. They want AI agents to do the building so they can spend their time training and building relationships. They review everything before it ships.

## Hard constraints
- **$0 to near-$0.** Free tiers and open-source only. No paid services or APIs without asking.
- **Core logic in Python and SQL.** Keep the frontend thin.
- **Small, reviewable changes.** One concern per branch and PR.
- **Never push to `main`.** Work on a branch and open a PR. The builder merges.
- **No scraping** unless the site's ToS and robots.txt allow it, and a human verifies the data before it is published.
- **No sensitive personal data** stored. Credit OpenStreetMap data (attribution required).

## The agent team
Defined in `.claude/agents/`:
- `designer`: UX flows, wireframes, copy, visual system. Builder approves before the engineer builds.
- `engineer`: schema, ingestion, API, frontend, tests, CI. Builder reviews all SQL and Python before merge.
- `pr`: README, case study, demo narrative, outreach drafts. Builder approves all public text.

## Working agreements
- Record meaningful decisions as short ADRs in `docs/decisions/` (what, why, alternatives rejected). They feed the case study.
- If something is ambiguous or irreversible, ask instead of guessing.
- Report only real numbers. Never invent metrics, users or results.

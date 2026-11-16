# BJJ Open Mat Finder

Find BJJ open mats near home or while traveling, including at the gyms that don't show up on the first page of a search.

> **Status:** early development. Launching in **Austin, TX** first. Planned home: [openmat.hirebekah.com](https://openmat.hirebekah.com).

## The problem
Open mat information is scattered across gym websites, Instagram stories, Facebook groups and word of mouth. Search tends to surface only the most digitally visible gyms, so small and quality gyms get missed. Travelers can't easily tell whether a gym welcomes visitors, what it costs, whether it's gi or no-gi, or whether the listed time is still true.

## What it will do
- Search by city or "near me" and see open mats on a map and list
- Filter by day, gi / no-gi, visitor policy and fee
- Show when each listing was last verified, and by whom, so you know what to trust
- Let anyone submit a gym or flag outdated info, and let owners claim their gym

## Built with
Python and FastAPI, Postgres, Leaflet and OpenStreetMap, and a thin static frontend. Everything runs on free tiers.

## How it's built
This project is built with a small team of AI agents (a designer, an engineer and a public relations agent) defined in [`.claude/agents/`](.claude/agents/). I direct the work and review every change, especially the SQL and Python, before it ships. Design decisions are recorded in [`docs/decisions/`](docs/decisions/).

## Docs
- [Project context](docs/context.md): goals, scope, schema, decisions
- [Decision records](docs/decisions/)

## Data and attribution
Gym locations are seeded from OpenStreetMap data. © OpenStreetMap contributors.

## Author
Built by Rebekah. Questions, corrections and gym submissions are welcome.

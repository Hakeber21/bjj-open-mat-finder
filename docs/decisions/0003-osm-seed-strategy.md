# ADR 0003 — OSM seed strategy for Austin gyms

**Date:** 2026-11-16
**Status:** Accepted

## Context

We need a starting dataset of BJJ and martial-arts gyms in Austin, TX before any
community submissions come in.  Without seed data, the map is empty on day one and
the app looks broken to anyone who visits early.

We need to decide:
1. Where to get the data.
2. Whether to fetch it at startup or commit a static snapshot.
3. How to keep it fresh over time.

## Decision

### Source: OpenStreetMap via the Overpass API

Fetch gym data from OpenStreetMap using the free, unauthenticated Overpass API.
The script (`scripts/fetch_osm_austin.py`) queries for nodes and ways in Austin's
bounding box (30.098, -97.928, 30.516, -97.579) using:

- `sport=martial_arts` and `sport=judo` tags (judo is sometimes used for BJJ clubs)
- `leisure=sports_centre` combined with `sport=martial_arts`
- Name-based regex: "BJJ", "jiu-jitsu", "grappling", "MMA", "martial arts"

### Format: static SQL seed file, not a startup query

The Overpass query result is committed as `seeds/austin_gyms.sql`.  The API is
only called when a human explicitly re-runs the script and reviews the diff.

### Data quality note

OSM coverage of BJJ gyms in Austin is uneven.  The initial run returned 17
entries — a useful starting point, but not a complete picture.  Some entries have
addresses and websites; others have only a name and coordinates.  All rows have
`visitor_policy = NULL` and `source = 'osm'` because OSM does not carry that
information.  A human must verify each listing before anything beyond `NULL` can
be set for `visitor_policy`.

The name-based query also surfaces gyms that are primarily kickboxing, krav maga,
or other martial arts; these may or may not host BJJ open mats and require manual
review.

Community submissions (the `submission` table) are the primary long-term data
source.  The OSM seed is a cold-start aid, not a complete or authoritative dataset.

### Attribution

The ODbL 1.0 license requires attribution.  Every generated seed file includes the
header:

```
-- DATA SOURCE: OpenStreetMap contributors
-- LICENSE   : Open Database License (ODbL) 1.0
--             https://www.openstreetmap.org/copyright
-- ATTRIBUTION REQUIRED: Geodata © OpenStreetMap contributors.
```

Attribution must also appear in the app's UI (footer or about page) before launch.

### How to refresh

1. Run `python3 scripts/fetch_osm_austin.py` from the repo root.
2. Review the diff in `seeds/austin_gyms.sql`.  Look for new entries, removed
   entries (a gym that has been deleted from OSM), and changed coordinates or
   names.
3. If the diff looks correct, commit it on a branch and open a PR.  Never commit
   a refresh directly to `main`.

The script uses no third-party packages (stdlib only) and exits with a non-zero
code if the Overpass API is unreachable, so it is safe to run in CI if we ever
want to automate a freshness check.

## Alternatives rejected

| Alternative | Reason rejected |
|---|---|
| Google Places API | Paid beyond a free tier; strict caching rules; explicitly out of scope in `docs/context.md` |
| Scraping gym websites | Each site has different ToS and robots.txt; requires per-site maintenance; a human must verify anyway |
| Fetching OSM data at API startup | Non-deterministic (OSM data changes); adds a network dependency to every cold start; makes the seed unreviewed and hard to audit; slower startup |
| Nominatim geocoding | Nominatim finds addresses, not venue categories; not the right tool for discovering gyms |
| Foursquare / Yelp free tiers | Free tiers are limited and subject to change; adds a third-party dependency; data would need the same human verification step anyway |
| Running the Overpass query at deploy time | Same problem as startup fetch — non-deterministic and unreviewed |

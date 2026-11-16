# ADR 0002 — Initial schema design

**Date:** 2026-11-16
**Status:** Accepted

## Context

We need a Postgres schema to store BJJ gyms, their recurring open mat sessions, and
unverified community submissions. The schema must support the core query: open mats
within a radius, on a given day, filtered by format and visitor policy, ranked by
freshness.

## Decision

Three tables: `gym`, `open_mat`, and `submission`. Details below.

### Tables and constraints

- `gym` holds location and contact data. `source` and `visitor_policy` carry
  `CHECK` constraints that enforce the allowed string values listed in
  `docs/context.md`. An unconstrained text column would let bad values slip in
  silently; `CHECK` makes the database the last line of defense.
- `open_mat` links to `gym` and stores one row per recurring session. `format`,
  `verified_by`, and `day_of_week` are all constrained to their documented allowed
  values.
- `submission` stores the raw form payload as JSONB so the form shape can change
  without a migration. Rows sit in the moderation queue until a human sets
  `status = 'approved'` or `'rejected'`.

### Indexes

| Index | Columns | Purpose |
|---|---|---|
| `idx_gym_lat_lng` | `(lat, lng)` | Bounding-box pre-filter before Haversine |
| `idx_open_mat_gym_day` | `(gym_id, day_of_week)` | Day-filter join in the core query |
| `idx_open_mat_freshness` | `last_verified_at DESC NULLS LAST` | ORDER BY freshness |
| `idx_submission_status` | `status` | Fetch the pending moderation queue |

### Haversine over PostGIS

Plain SQL Haversine is used for the distance calculation instead of PostGIS for MVP:

- PostGIS requires the `postgis` extension to be available on the host, which is not
  guaranteed on free tiers (Neon does offer it, but it adds a decision point and a
  setup step we do not need yet).
- Austin is a small dataset. Even without a spatial index, a bounding-box pre-filter
  on `(lat, lng)` cuts the rows that need Haversine down to a few dozen at most.
- The formula is short, readable SQL that any reviewer can verify without PostGIS
  knowledge.
- PostGIS remains an easy upgrade path if the project expands beyond Austin.

### `fee_cents INTEGER` over `NUMERIC`

- Integer cents avoids floating-point rounding issues when comparing or summing fees.
- `NULL` means the fee is unknown (not zero); `0` means free. This distinction is
  important for the "free only" filter: `fee_cents = 0` is unambiguous, while a
  `NUMERIC` default or a boolean `is_free` flag would require more care to handle
  the unknown case.

## Alternatives rejected

| Alternative | Reason rejected |
|---|---|
| PostGIS for spatial queries | Extension availability not guaranteed on free tiers; overkill for MVP dataset size |
| `NUMERIC` for fee | Integer cents is simpler and avoids floating-point edge cases |
| `BOOLEAN is_free` | Loses the ability to store actual fee amounts and obscures the unknown state |
| Single `schedule` JSONB column instead of `open_mat` rows | Harder to query and filter by day or format in SQL; relational rows are more reviewable |
| Storing submissions directly in `gym`/`open_mat` | Mixes unverified data with curated data; a separate queue makes moderation explicit |

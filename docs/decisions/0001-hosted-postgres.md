# 0001: Use hosted Postgres (leaning Neon free tier)

Status: accepted (provider to be re-verified before setup)
Date: 2026-11-16

## Context
The project needs a SQL database, must cost $0, and the builder reviews SQL most confidently. The demo will be visited sporadically (recruiters, gym owners), so it must still work after long quiet periods.

## Decision
Use Postgres on a free hosted tier. Lean toward Neon.

## Why
- Neon's free plan has about 1 GB of storage per project. Compute suspends after 5 minutes idle and wakes in a few hundred milliseconds on the next query, and data is not paused for inactivity.
- Supabase's free plan has a 500 MB database and pauses projects after a week of inactivity, which would leave the demo broken the first time someone visits after a quiet week.
- Austin's dataset is tiny and fits easily in either limit. Supabase's extra features (auth, storage) aren't needed for the MVP.

## Alternatives rejected
- **SQLite in the repo:** simplest, but doesn't give the builder a realistic Postgres setup to explain, and complicates concurrent writes from submissions.
- **Supabase free:** pause-on-inactivity risk.

## Consequences
- First request after idle has a short wake-up delay.
- Free-tier limits can change, so re-check them before setup.

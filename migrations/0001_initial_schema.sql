-- Migration : 0001_initial_schema
-- Date       : 2026-11-16
-- Description: Create the three core tables (gym, open_mat, submission) and
--              supporting indexes for the radius + day + format + visitor-policy
--              query, ranked by freshness.

-- ---------------------------------------------------------------------------
-- gym
-- Represents a gym that may host open mat sessions.
-- source values: 'osm' (OpenStreetMap seed), 'submission' (community form),
--                'owner' (manually verified owner claim).
-- visitor_policy values: 'welcome', 'call_first', 'members_only', 'unknown'.
-- ---------------------------------------------------------------------------
CREATE TABLE gym (
    id             BIGSERIAL PRIMARY KEY,
    name           TEXT NOT NULL,
    address        TEXT,
    city           TEXT,
    country        TEXT,
    lat            DOUBLE PRECISION,
    lng            DOUBLE PRECISION,
    website_url    TEXT,
    instagram      TEXT,
    source         TEXT NOT NULL
                       CHECK (source IN ('osm', 'submission', 'owner')),
    visitor_policy TEXT
                       CHECK (visitor_policy IN ('welcome', 'call_first', 'members_only', 'unknown')),
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- Pre-filter bounding box before Haversine calculation.
-- A composite index on (lat, lng) lets the planner cut the scan to the rough
-- square around the user before the more expensive distance math runs.
CREATE INDEX idx_gym_lat_lng ON gym (lat, lng);


-- ---------------------------------------------------------------------------
-- open_mat
-- A recurring open mat session at a gym.
-- day_of_week: 0 = Sunday, 6 = Saturday (ISO-like; document in app layer).
-- fee_cents  : NULL = unknown cost; 0 = free; positive integer = drop-in fee.
-- verified_by: 'owner' | 'visitor' | 'agent_check'
-- ---------------------------------------------------------------------------
CREATE TABLE open_mat (
    id               BIGSERIAL PRIMARY KEY,
    gym_id           BIGINT REFERENCES gym (id),
    day_of_week      SMALLINT CHECK (day_of_week BETWEEN 0 AND 6),
    start_time       TIME NOT NULL,
    end_time         TIME,
    format           TEXT CHECK (format IN ('gi', 'nogi', 'both')),
    fee_cents        INTEGER,          -- NULL = unknown, 0 = free
    min_belt         TEXT,
    notes            TEXT,
    last_verified_at TIMESTAMPTZ,
    verified_by      TEXT
                         CHECK (verified_by IN ('owner', 'visitor', 'agent_check'))
);

-- Join key + day filter: used in every core query.
CREATE INDEX idx_open_mat_gym_day ON open_mat (gym_id, day_of_week);

-- Freshness sort: ORDER BY last_verified_at DESC.
CREATE INDEX idx_open_mat_freshness ON open_mat (last_verified_at DESC NULLS LAST);


-- ---------------------------------------------------------------------------
-- submission
-- Holds unverified community submissions until a human approves or rejects
-- them. The payload is kept as JSONB so the form shape can evolve without
-- a migration.
-- status values: 'pending', 'approved', 'rejected'.
-- ---------------------------------------------------------------------------
CREATE TABLE submission (
    id         BIGSERIAL PRIMARY KEY,
    payload    JSONB NOT NULL,
    status     TEXT DEFAULT 'pending'
                   CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Moderation queue: fetch all pending rows.
CREATE INDEX idx_submission_status ON submission (status);

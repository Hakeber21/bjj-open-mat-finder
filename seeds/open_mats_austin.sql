-- =============================================================================
-- seeds/open_mats_austin.sql
--
-- Open mat session data for Austin, TX BJJ gyms.
--
-- SOURCES (accessed 2026-11-18):
--   findopenmats.com/austin
--   openmatlocator.com/open-mats/texas/austin
--   vowbjj.com/schedule
--
-- IMPORTANT: This data was found via web research and should be human-verified
-- before being treated as authoritative. Schedules change — always check
-- with the gym before showing up.
--
-- verified_by = 'agent_check' throughout; a human verifying with the gym
-- directly should update verified_by to 'visitor' or 'owner'.
--
-- day_of_week: ISO 8601 — 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat, 7=Sun
-- fee_cents: NULL=unknown, 0=free, positive=drop-in fee in cents
--
-- SAFETY: This script is NOT idempotent. Run it once on a database that has
-- already had 0001_initial_schema.sql and austin_gyms.sql applied.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Update visitor_policy for gyms with confirmed drop-in policy
-- ---------------------------------------------------------------------------

-- VOW BJJ: website says "Non-Member drop-ins are welcomed!"
UPDATE gym SET visitor_policy = 'welcome' WHERE name = 'VOW BJJ' AND city = 'Austin';

-- Paragon: findopenmats lists open open mat — policy unconfirmed, leave as NULL


-- ---------------------------------------------------------------------------
-- 2. Open mats for gyms already in the database (from austin_gyms.sql)
-- ---------------------------------------------------------------------------

-- VOW BJJ — 5555 N Lamar Blvd, Austin, TX 78751
-- Source: findopenmats.com + vowbjj.com/schedule
-- Sunday all-levels open mat: 2–4 PM, No-Gi, Free
INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 7, '14:00', '16:00', 'nogi', 0,
       'All levels welcome. Drop-in visitors welcome.',
       '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'VOW BJJ' AND g.city = 'Austin';

-- Paragon Jiu-Jitsu Academy Austin — 6800 West Gate Blvd, Austin, TX 78745
-- Source: findopenmats.com
-- Friday open mat: 6–7:30 PM (format and fee unconfirmed)
INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 5, '18:00', '19:30', NULL, NULL,
       NULL,
       '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'Paragon Jiu-Jitsu Academy Austin' AND g.city = 'Austin';


-- ---------------------------------------------------------------------------
-- 3. New gyms found via findopenmats.com / openmatlocator.com
--    source='submission' — not from OSM, not from an owner claim
--    Coordinates geocoded from street address via Nominatim (OSM)
-- ---------------------------------------------------------------------------

INSERT INTO gym (name, address, city, country, lat, lng, website_url, instagram, source, visitor_policy)
VALUES
  ('Renzo Gracie Austin',
   '4631 Airport Blvd STE 114', 'Austin', 'US',
   30.305965, -97.715119,
   NULL, NULL, 'submission', NULL),

  ('East Austin Jiu Jitsu Parlor',
   '979 Springdale Rd #111', 'Austin', 'US',
   30.262862, -97.696185,
   NULL, NULL, 'submission', NULL),

  ('Gracie Humaitá Austin',
   '321 W Ben White Blvd Suite 108', 'Austin', 'US',
   30.223595, -97.767183,
   NULL, NULL, 'submission', NULL),

  ('Modern Art Jiu Jitsu',
   '8127 Mesa Dr #A105', 'Austin', 'US',
   30.372698, -97.755571,
   NULL, NULL, 'submission', NULL),

  ('Austin Submission Fighting',
   '11940 Menchaca Rd #104', 'Austin', 'US',
   30.143598, -97.833094,
   NULL, NULL, 'submission', NULL),

  ('Integração Jiu Jitsu',
   '1600 W Stassney Ln', 'Austin', 'US',
   30.213600, -97.792643,
   NULL, NULL, 'submission', NULL);


-- ---------------------------------------------------------------------------
-- 4. Open mats for the new gyms
--    Referenced by name+city to avoid hardcoded IDs
-- ---------------------------------------------------------------------------

-- Renzo Gracie Austin — Sat + Sun 2–4 PM, Gi & No-Gi
-- Source: findopenmats.com
INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 6, '14:00', '16:00', 'both', NULL, NULL, '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'Renzo Gracie Austin' AND g.city = 'Austin';

INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 7, '14:00', '16:00', 'both', NULL, NULL, '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'Renzo Gracie Austin' AND g.city = 'Austin';

-- East Austin Jiu Jitsu Parlor — Fri 7–8 PM and Sat 11 AM–1 PM, No-Gi, $40
-- Source: findopenmats.com
INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 5, '19:00', '20:00', 'nogi', 4000, '$40 drop-in', '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'East Austin Jiu Jitsu Parlor' AND g.city = 'Austin';

INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 6, '11:00', '13:00', 'nogi', 4000, '$40 drop-in', '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'East Austin Jiu Jitsu Parlor' AND g.city = 'Austin';

-- Gracie Humaitá Austin — Fri 7–8 PM (fee unconfirmed) and Sat 9–10 AM ($30)
-- Source: findopenmats.com + openmatlocator.com
INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 5, '19:00', '20:00', NULL, NULL, NULL, '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'Gracie Humaitá Austin' AND g.city = 'Austin';

INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 6, '09:00', '10:00', NULL, 3000, '$30 drop-in', '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'Gracie Humaitá Austin' AND g.city = 'Austin';

-- Modern Art Jiu Jitsu — Sat 1 PM and Sun 12 PM, No-Gi, Free
-- Source: findopenmats.com
INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 6, '13:00', NULL, 'nogi', 0, NULL, '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'Modern Art Jiu Jitsu' AND g.city = 'Austin';

INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 7, '12:00', NULL, 'nogi', 0, NULL, '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'Modern Art Jiu Jitsu' AND g.city = 'Austin';

-- Austin Submission Fighting — Sun 11 AM–1 PM and Sun 6–8 PM
-- Source: findopenmats.com + openmatlocator.com
INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 7, '11:00', '13:00', NULL, NULL, NULL, '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'Austin Submission Fighting' AND g.city = 'Austin';

INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 7, '18:00', '20:00', NULL, NULL, 'Evening session', '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'Austin Submission Fighting' AND g.city = 'Austin';

-- Integração Jiu Jitsu — Fri 6:45–7:45 PM and Sat 1–2 PM
-- Source: findopenmats.com
INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 5, '18:45', '19:45', NULL, NULL, NULL, '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'Integração Jiu Jitsu' AND g.city = 'Austin';

INSERT INTO open_mat (gym_id, day_of_week, start_time, end_time, format, fee_cents, notes, last_verified_at, verified_by)
SELECT g.id, 6, '13:00', '14:00', NULL, NULL, NULL, '2026-11-18 00:00:00+00', 'agent_check'
FROM gym g WHERE g.name = 'Integração Jiu Jitsu' AND g.city = 'Austin';

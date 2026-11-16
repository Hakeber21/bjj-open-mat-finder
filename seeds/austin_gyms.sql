-- =============================================================================
-- seeds/austin_gyms.sql
--
-- Seed data: BJJ / martial-arts gyms in Austin, TX.
--
-- DATA SOURCE: OpenStreetMap contributors
-- LICENSE   : Open Database License (ODbL) 1.0
--             https://www.openstreetmap.org/copyright
-- ATTRIBUTION REQUIRED: Geodata © OpenStreetMap contributors.
--
-- Generated : 2026-11-16T22:27:28Z
-- Script    : scripts/fetch_osm_austin.py
--
-- All rows have source='osm' and visitor_policy=NULL because OSM data does
-- not include visitor policy.  A human must verify each listing before the
-- visitor_policy field can be set to anything other than NULL.
--
-- To refresh: re-run scripts/fetch_osm_austin.py and review the diff before
-- committing the updated seed file.
-- =============================================================================

INSERT INTO gym (name, address, city, country, lat, lng,
                 website_url, instagram, source, visitor_policy)
VALUES
  ('Austin Jiu-Jitsu', NULL, 'Austin', 'US', 30.274481, -97.7809714, NULL, NULL, 'osm', NULL),
  ('Impact Martial Arts', NULL, 'Austin', 'US', 30.4254769, -97.7536161, NULL, NULL, 'osm', NULL),
  ('Impact Martial Arts', NULL, 'Austin', 'US', 30.4449619, -97.789474, NULL, NULL, 'osm', NULL),
  ('Brazilian Fight Factory', '11150 Research Boulevard', 'Austin', 'US', 30.4067687, -97.7469381, 'https://brazilianfightfactory.com/', NULL, 'osm', NULL),
  ('Black Widow MMA', '2007 Kramer Lane', 'Austin', 'US', 30.388225, -97.7101372, 'https://blackwidowmma.com/', NULL, 'osm', NULL),
  ('Mu Sool Won Family Martial Arts Center', '13584 Pond Springs Road', 'Austin', 'US', 30.4535524, -97.7902392, 'https://www.musoolwon.com/', NULL, 'osm', NULL),
  ('Tiger-Rock Martial Arts', '12112 Ranch Road 620 North', 'Austin', 'US', 30.4563478, -97.8220695, 'https://northaustinmaf.com/', NULL, 'osm', NULL),
  ('VOW BJJ', '5555 Lamar Boulevard', 'Austin', 'US', 30.3235282, -97.7252513, NULL, NULL, 'osm', NULL),
  ('Life Ki-do Martial Arts & Personal Development', '3636 Bee Caves Road', 'Austin', 'US', 30.279239, -97.8058231, 'https://www.lifekido.com', 'lifekido', 'osm', NULL),
  ('Fighting Fit Kickboxing & Jiu Jitsu', '1779 Wells Branch Parkway', 'Austin', 'US', 30.4352468, -97.6742861, 'https://www.austinkickboxingandjiujitsu.com/', NULL, 'osm', NULL),
  ('Lions Krav Maga', NULL, 'Austin', 'US', 30.3622437, -97.7422071, 'https://lionskravmaga.com/', NULL, 'osm', NULL),
  ('Nunan''s Martial Arts', '2051 Cypress Creek Road', 'Cedar Park', 'US', 30.4762764, -97.8413442, 'https://www.nunansmartialarts.com/', NULL, 'osm', NULL),
  ('The Mat Martial Arts', '2100 Cypress Creek Road', 'Cedar Park', 'US', 30.4744925, -97.841417, 'https://themataustin.com/', NULL, 'osm', NULL),
  ('Jiu Jitsu', NULL, 'Austin', 'US', 30.4545492, -97.7927074, NULL, NULL, 'osm', NULL),
  ('Paragon Jiu-Jitsu Academy Austin', '6800 West Gate Boulevard', 'Austin', 'US', 30.2093036, -97.8156715, 'https://www.paragonaustin.com', NULL, 'osm', NULL),
  ('Gracie Barra Brazilian Jiu Jitsu', NULL, 'Austin', 'US', 30.3690507, -97.7206547, NULL, NULL, 'osm', NULL),
  ('Premier Martial Arts Pflugerville', '1420 Wells Branch Parkway', 'Pflugerville', 'US', 30.4419585, -97.6628492, 'https://premiermartialarts.com', NULL, 'osm', NULL)
ON CONFLICT DO NOTHING;

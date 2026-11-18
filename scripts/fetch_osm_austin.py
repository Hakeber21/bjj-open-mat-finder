#!/usr/bin/env python3
"""
fetch_osm_austin.py
-------------------
Query the OpenStreetMap Overpass API for martial-arts and BJJ gyms in Austin, TX,
then write a SQL seed file at seeds/austin_gyms.sql.

Data source: OpenStreetMap contributors (ODbL 1.0).
Attribution is required by the ODbL license; it appears at the top of the
generated SQL file and in the INSERT comment below.

Usage:
    python3 scripts/fetch_osm_austin.py

No third-party packages required — only the Python standard library.
"""

import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Overpass API endpoints tried in order.  The primary (overpass-api.de) is the
# canonical public instance; the others are well-known public mirrors that can
# be used as fallbacks when the primary is under load or in maintenance.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Bounding box for Austin, TX: south, west, north, east
AUSTIN_BBOX = (30.098, -97.928, 30.516, -97.579)

# Output path is relative to this script's parent directory (the repo root).
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(REPO_ROOT, "seeds", "austin_gyms.sql")

# Two gyms are considered duplicates if they share the same name (case-
# insensitive) OR if they are within ~50 m of each other and have the same
# name after normalisation.  50 m ≈ 0.00045 degrees latitude at this latitude.
DEDUP_RADIUS_DEG = 0.00045

# HTTP request timeout in seconds.  Overpass can be slow under load; 90 s is
# generous but still bounded so the script doesn't hang indefinitely.
REQUEST_TIMEOUT = 90

# ---------------------------------------------------------------------------
# Overpass query
# ---------------------------------------------------------------------------

def build_overpass_query(bbox: tuple) -> str:
    """
    Build an Overpass QL query that returns nodes, ways and relations in the
    Austin bounding box that are likely martial-arts or BJJ venues.

    Strategy:
      1. Tag-based: sport=martial_arts, sport=judo (sometimes used for BJJ),
         and leisure=sports_centre combined with sport=martial_arts.
      2. Name-based: any amenity/leisure/sport node or way whose name contains
         common BJJ/MMA keywords.

    We request `out center` so that ways and relations also carry a lat/lng
    centroid rather than just a list of node references.
    """
    s, w, n, e = bbox
    bbox_str = f"{s},{w},{n},{e}"

    # Keyword list for name-based matching (Overpass regex is case-insensitive).
    name_regex = "BJJ|[Jj]iu[-. ]?[Jj]itsu|[Gg]rappling|MMA|[Mm]artial [Aa]rt"

    query = f"""
[out:json][timeout:60];
(
  // Sport tag: martial arts (nodes)
  node["sport"="martial_arts"]({bbox_str});
  // Sport tag: martial arts (ways)
  way["sport"="martial_arts"]({bbox_str});
  // Sport tag: judo — occasionally used for BJJ clubs
  node["sport"="judo"]({bbox_str});
  way["sport"="judo"]({bbox_str});
  // Sports centres with a martial-arts sport tag
  node["leisure"="sports_centre"]["sport"="martial_arts"]({bbox_str});
  way["leisure"="sports_centre"]["sport"="martial_arts"]({bbox_str});
  // Name-based catch-all: BJJ, jiu-jitsu, grappling, MMA keywords
  node["name"~"{name_regex}"]({bbox_str});
  way["name"~"{name_regex}"]({bbox_str});
);
out center;
""".strip()

    return query


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def fetch_overpass(query: str) -> dict:
    """
    POST the Overpass query and return the parsed JSON response.

    Tries each URL in OVERPASS_URLS in order, moving to the next on HTTP 5xx
    or timeout.  Exits with a non-zero code only if all endpoints fail.
    """
    encoded_data = urllib.parse.urlencode({"data": query}).encode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        # Identify the bot; good practice per Overpass usage policy.
        "User-Agent": "BJJOpenMatFinder/0.1 (openmat.hirebekah.com; seed script)",
    }

    last_error: str = "unknown error"

    for url in OVERPASS_URLS:
        print(f"  Trying {url} …")
        req = urllib.request.Request(url, data=encoded_data, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason}"
            print(f"  Failed: {last_error}", file=sys.stderr)
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = str(exc)
            print(f"  Failed: {last_error}", file=sys.stderr)
            continue

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            last_error = f"JSON parse error: {exc}"
            print(f"  Failed: {last_error}", file=sys.stderr)
            continue

    print(f"\nERROR: All Overpass endpoints failed. Last error: {last_error}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------

def extract_gym(element: dict) -> dict | None:
    """
    Convert a single Overpass element (node, way, or relation) into a dict
    suitable for a gym row.  Returns None if the element has no usable name.

    Coordinate strategy:
      - Nodes carry lat/lon directly.
      - Ways and relations carry a 'center' sub-object when queried with
        'out center'; we use that centroid.
    """
    tags = element.get("tags", {})

    name = tags.get("name", "").strip()
    if not name:
        return None  # Skip unnamed features; they can't be useful listings.

    # Coordinates
    if element["type"] == "node":
        lat = element.get("lat")
        lng = element.get("lon")
    else:
        # 'out center' adds a 'center' key for ways and relations.
        center = element.get("center", {})
        lat = center.get("lat")
        lng = center.get("lon")

    # Address fields
    housenumber = tags.get("addr:housenumber", "").strip()
    street = tags.get("addr:street", "").strip()
    if housenumber and street:
        address = f"{housenumber} {street}"
    elif street:
        address = street
    else:
        address = None

    city = tags.get("addr:city", "Austin").strip() or "Austin"
    country = tags.get("addr:country", "US").strip() or "US"

    # Website: prefer the plain 'website' tag, fall back to contact:website.
    website_url = (
        tags.get("website")
        or tags.get("contact:website")
        or None
    )

    # Instagram: prefer contact:instagram, fall back to instagram.
    instagram = (
        tags.get("contact:instagram")
        or tags.get("instagram")
        or None
    )

    return {
        "name": name,
        "lat": lat,
        "lng": lng,
        "address": address,
        "city": city,
        "country": country,
        "website_url": website_url,
        "instagram": instagram,
    }


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _approx_equal_coords(
    lat1: float | None,
    lng1: float | None,
    lat2: float | None,
    lng2: float | None,
    threshold_deg: float = DEDUP_RADIUS_DEG,
) -> bool:
    """
    Return True if two lat/lng pairs are within threshold_deg of each other
    using simple Euclidean distance in degree-space.

    This is accurate enough for the ~50 m deduplication window; we are not
    doing navigation here.  If either point is missing coordinates, we return
    False (can't conclude they are the same place).
    """
    if None in (lat1, lng1, lat2, lng2):
        return False
    return math.hypot(lat1 - lat2, lng1 - lng2) < threshold_deg


def deduplicate(gyms: list[dict]) -> list[dict]:
    """
    Remove duplicates from the gym list.

    Two entries are duplicates if they share the same normalised name AND are
    within ~50 m of each other.  This handles the common OSM case where both a
    node (the entrance) and a way (the building polygon) describe the same gym.

    When duplicates exist we keep the first occurrence (which may carry more
    complete tag data, as nodes tend to be tagged more thoroughly than ways).
    """
    seen: list[dict] = []

    for gym in gyms:
        norm_name = gym["name"].lower().strip()
        is_dup = False

        for kept in seen:
            same_name = kept["name"].lower().strip() == norm_name
            close_enough = _approx_equal_coords(
                gym["lat"], gym["lng"], kept["lat"], kept["lng"]
            )
            if same_name and close_enough:
                is_dup = True
                break

        if not is_dup:
            seen.append(gym)

    return seen


# ---------------------------------------------------------------------------
# SQL generation
# ---------------------------------------------------------------------------

def _sql_literal(value) -> str:
    """
    Render a Python value as a SQL literal.
      - None   → NULL
      - str    → single-quoted with internal single-quotes doubled (SQL standard)
      - float  → decimal representation
    """
    if value is None:
        return "NULL"
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def build_sql(gyms: list[dict], generated_at: str) -> str:
    """
    Produce a complete SQL seed file as a string.

    Uses INSERT ... ON CONFLICT DO NOTHING so the file is safely re-runnable.
    There is no UNIQUE constraint in the current schema, so ON CONFLICT falls
    back to no-op on duplicate primary key — meaning the seed is idempotent
    only if run on a fresh table.  A future migration could add a unique
    constraint on (name, lat, lng) to make it truly idempotent on re-runs.
    """
    lines = []

    # --- Header / attribution -----------------------------------------------
    lines.append("-- =============================================================================")
    lines.append("-- seeds/austin_gyms.sql")
    lines.append("--")
    lines.append("-- Seed data: BJJ / martial-arts gyms in Austin, TX.")
    lines.append("--")
    lines.append("-- DATA SOURCE: OpenStreetMap contributors")
    lines.append("-- LICENSE   : Open Database License (ODbL) 1.0")
    lines.append("--             https://www.openstreetmap.org/copyright")
    lines.append("-- ATTRIBUTION REQUIRED: Geodata © OpenStreetMap contributors.")
    lines.append("--")
    lines.append(f"-- Generated : {generated_at}")
    lines.append("-- Script    : scripts/fetch_osm_austin.py")
    lines.append("--")
    lines.append("-- All rows have source='osm' and visitor_policy=NULL because OSM data does")
    lines.append("-- not include visitor policy.  A human must verify each listing before the")
    lines.append("-- visitor_policy field can be set to anything other than NULL.")
    lines.append("--")
    lines.append("-- To refresh: re-run scripts/fetch_osm_austin.py and review the diff before")
    lines.append("-- committing the updated seed file.")
    lines.append("-- =============================================================================")
    lines.append("")

    if not gyms:
        lines.append("-- No gyms were returned by the Overpass API for this query.")
        lines.append("-- OSM coverage of BJJ gyms in Austin is sparse; this is expected.")
        lines.append("-- Community submissions (the 'submission' table) are the primary long-term")
        lines.append("-- data source.  Seed this table manually or re-run the script after OSM")
        lines.append("-- contributors have mapped more venues.")
        lines.append("")
        return "\n".join(lines)

    # --- INSERT statements ---------------------------------------------------
    lines.append("INSERT INTO gym (name, address, city, country, lat, lng,")
    lines.append("                 website_url, instagram, source, visitor_policy)")
    lines.append("VALUES")

    value_rows = []
    for gym in gyms:
        row = (
            f"  ("
            f"{_sql_literal(gym['name'])}, "
            f"{_sql_literal(gym['address'])}, "
            f"{_sql_literal(gym['city'])}, "
            f"{_sql_literal(gym['country'])}, "
            f"{_sql_literal(gym['lat'])}, "
            f"{_sql_literal(gym['lng'])}, "
            f"{_sql_literal(gym['website_url'])}, "
            f"{_sql_literal(gym['instagram'])}, "
            f"'osm', "       # source is always 'osm' for this seed
            f"NULL"          # visitor_policy unknown until human verifies
            f")"
        )
        value_rows.append(row)

    lines.append(",\n".join(value_rows))
    lines.append("ON CONFLICT DO NOTHING;")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("BJJ Open Mat Finder — OSM seed script for Austin, TX")
    print("=" * 55)

    # 1. Build and send the Overpass query.
    print("Querying Overpass API … (this may take up to 30 seconds)")
    query = build_overpass_query(AUSTIN_BBOX)
    response = fetch_overpass(query)

    elements = response.get("elements", [])
    raw_count = len(elements)
    print(f"Raw results from Overpass: {raw_count}")

    if raw_count == 0:
        print(
            "\nWARNING: Overpass returned zero elements.\n"
            "Possible reasons:\n"
            "  - OSM coverage of BJJ/martial-arts venues in Austin is sparse.\n"
            "  - The API is temporarily unavailable.\n"
            "  - The bounding box or query tags need adjustment.\n"
            "\nWriting an empty seed file with the attribution header."
        )

    # 2. Extract gym dicts, skipping unnamed elements.
    gyms_raw: list[dict] = []
    for element in elements:
        gym = extract_gym(element)
        if gym is not None:
            gyms_raw.append(gym)

    named_count = len(gyms_raw)
    print(f"Elements with a usable name: {named_count}")

    # 3. Deduplicate.
    gyms = deduplicate(gyms_raw)
    dedup_count = len(gyms)
    print(f"After deduplication: {dedup_count}")

    # 4. Summary list.
    if gyms:
        print("\nGyms found:")
        for gym in gyms:
            coord_str = (
                f"{gym['lat']:.5f}, {gym['lng']:.5f}"
                if gym["lat"] is not None and gym["lng"] is not None
                else "no coordinates"
            )
            print(f"  - {gym['name']}  ({coord_str})")
    else:
        print("\nNo named gyms found.")

    # 5. Write seed file.
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sql = build_sql(gyms, generated_at)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(sql)

    print(f"\nSeed file written to: {OUTPUT_PATH}")
    print(f"  {dedup_count} gym(s) inserted.")

    # Remind the reviewer that OSM data is unverified.
    if dedup_count > 0:
        print(
            "\nNOTE: All rows have visitor_policy=NULL and source='osm'.\n"
            "A human must verify each listing before visitor_policy can be set.\n"
            "OSM data quality for BJJ gyms varies; treat this as a starting point."
        )


if __name__ == "__main__":
    main()

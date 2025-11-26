import requests
import sqlite3
import json
import os
from datetime import datetime, timedelta

from loader import get_env

CACHE_PATH = "/workspace/travelplanner_runpod/cache/aggregator_cache.db"

# ------------------------------------------------
# CACHE INIT
# ------------------------------------------------
def init_cache():
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    con = sqlite3.connect(CACHE_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT,
            timestamp INTEGER
        )
    """)
    con.commit()
    return con

def cache_get(key):
    con = init_cache()
    cur = con.cursor()
    cur.execute("SELECT value FROM cache WHERE key=?", (key,))
    row = cur.fetchone()
    return json.loads(row[0]) if row else None

def cache_set(key, val):
    con = init_cache()
    cur = con.cursor()
    cur.execute("REPLACE INTO cache (key,value,timestamp) VALUES (?, ?, ?)", (key, json.dumps(val), int(datetime.now().timestamp())))
    con.commit()


# ------------------------------------------------
# GEOAPIFY → COORDINATES
# ------------------------------------------------
def geocode_city(city):
    key = get_env("GEOAPIFY_KEY")
    url = f"https://api.geoapify.com/v1/geocode/search?text={city}&limit=1&apiKey={key}"
    res = requests.get(url).json()

    if "features" not in res or not res["features"]:
        return None

    coords = res["features"][0]["geometry"]["coordinates"]
    return {"lon": coords[0], "lat": coords[1]}


# ------------------------------------------------
# WEATHER
# ------------------------------------------------
def fetch_weather(lat, lon, days):
    out = []
    start = datetime.now()
    for i in range(days):
        date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        out.append({
            "date": date,
            "summary": "Data unavailable"   # Replace later with real API
        })
    return out


# ------------------------------------------------
# POIs
# ------------------------------------------------
def fetch_pois(lat, lon):
    key = get_env("GEOAPIFY_KEY")
    url = f"https://api.geoapify.com/v2/places?categories=tourism&filter=circle:{lon},{lat},3000&limit=20&apiKey={key}"
    res = requests.get(url).json()

    pois = []
    for f in res.get("features", []):
        props = f["properties"]
        pois.append({
            "name": props.get("name"),
            "address": props.get("formatted"),
            "categories": props.get("categories", [])
        })

    return pois


# ------------------------------------------------
# EVENTS
# ------------------------------------------------
def fetch_events(city, days, lat=None, lon=None):
    key = get_env("TICKETMASTER_KEY")

    # build date range
    start = datetime.now()
    end = start + timedelta(days=days - 1)

    start_iso = start.strftime("%Y-%m-%dT00:00:00Z")
    end_iso = end.strftime("%Y-%m-%dT23:59:59Z")

    # Use lat/lon if available (more reliable)
    geo_filter = ""
    if lat is not None and lon is not None:
        geo_filter = f"&latlong={lat},{lon}&radius=50"

    url = (
        "https://app.ticketmaster.com/discovery/v2/events.json"
        f"?apikey={key}"
        f"{geo_filter}"
        f"&size=50"
        f"&startDateTime={start_iso}"
        f"&endDateTime={end_iso}"
        "&sort=date,asc"
    )

    try:
        res = requests.get(url).json()
    except:
        return []

    events = []
    if "_embedded" not in res:
        return events

    for e in res["_embedded"]["events"]:
        dates = e.get("dates", {}).get("start", {})
        venue_block = e.get("_embedded", {}).get("venues", [{}])[0]

        events.append({
            "title": e.get("name"),
            "date": dates.get("localDate"),
            "time": dates.get("localTime"),
            "venue": venue_block.get("name"),
            "address": venue_block.get("address", {}).get("line1"),
            "url": e.get("url")
        })

    return events



# ------------------------------------------------
# FULL PIPELINE
# ------------------------------------------------
def run_aggregator_pipeline(city, days):
    key = f"{city}_{days}"
    cached = cache_get(key)
    if cached:
        return cached

    coords = geocode_city(city)
    if not coords:
        coords = {"lat": 0, "lon": 0}

    weather = fetch_weather(coords["lat"], coords["lon"], days)
    pois = fetch_pois(coords["lat"], coords["lon"])
    events = fetch_events(city, days, coords["lat"], coords["lon"])


    bundle = {
        "location": city,
        "coordinates": coords,
        "date_range": [
            datetime.now().strftime("%Y-%m-%d"),
            (datetime.now() + timedelta(days=days - 1)).strftime("%Y-%m-%d"),
        ],
        "context_blocks": {
            "weather": weather,
            "pois": pois,
            "events": events,
        },
    }

    cache_set(key, bundle)
    return bundle

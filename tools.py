"""
tools.py — Real data fetchers used by the Claude agent.

Each function maps to a Claude tool definition.
Uses:
  • Google Places API  → restaurants & attractions
  • Google Maps Distance Matrix API → travel time / cost estimates
  • SerpAPI (or fallback scrape) → current movies on BookMyShow
"""

import os
import httpx
import re
from datetime import datetime

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SERPAPI_KEY    = os.getenv("SERPAPI_KEY", "")

# ── Hyderabad geocenter ────────────────────────────────────────────────────────
HYD_LAT, HYD_LNG = 17.3850, 78.4867

PLACES_BASE  = "https://places.googleapis.com/v1/places"
MAPS_BASE    = "https://maps.googleapis.com/maps/api/distancematrix"
SERPAPI_BASE = "https://serpapi.com/search"


# ─────────────────────────────────────────────────────────────────────────────
# 1. RESTAURANTS
# ─────────────────────────────────────────────────────────────────────────────
async def search_restaurants(
    area: str,
    max_budget_per_person: int,
    cuisine: str = "",
    limit: int = 5,
) -> list[dict]:
    """
    Search Google Places for restaurants in <area>, Hyderabad.
    Returns list of {name, address, rating, price_level, maps_url, estimated_cost}.
    """
    if not GOOGLE_API_KEY:
        return _mock_restaurants(area, max_budget_per_person)

    query = f"{cuisine} restaurant in {area} Hyderabad"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{PLACES_BASE}/textsearch/json",
            params={
                "query": query,
                "key": GOOGLE_API_KEY,
                "type": "restaurant",
            },
        )
    data = r.json()
    results = []
    for p in data.get("results", [])[:limit]:
        price_level = p.get("price_level", 2)          # 1-4 Google scale
        # Rough INR estimate per person
        cost_map = {1: 150, 2: 350, 3: 600, 4: 1200}
        est_cost = cost_map.get(price_level, 350)
        if est_cost > max_budget_per_person * 0.45:      # skip if too pricey
            continue
        results.append({
            "name":           p.get("name"),
            "address":        p.get("formatted_address", area),
            "rating":         p.get("rating", 4.0),
            "price_level":    price_level,
            "estimated_cost": est_cost,
            "maps_url": f"https://www.google.com/maps/place/?q=place_id:{p.get('place_id')}",
            "place_id":       p.get("place_id"),
        })
    return results or _mock_restaurants(area, max_budget_per_person)


def _mock_restaurants(area: str, budget: int) -> list[dict]:
    """Fallback mock data when no API key provided."""
    all_restaurants = [
        {"name": "Paradise Biryani", "address": "MG Road, Secunderabad", "rating": 4.4,
         "estimated_cost": 320, "maps_url": "https://maps.google.com/?q=Paradise+Biryani+Hyderabad"},
        {"name": "Bawarchi Restaurant", "address": "RTC X Roads, Hyderabad", "rating": 4.3,
         "estimated_cost": 280, "maps_url": "https://maps.google.com/?q=Bawarchi+Hyderabad"},
        {"name": "Rayalaseema Ruchulu", "address": "Banjara Hills, Hyderabad", "rating": 4.2,
         "estimated_cost": 350, "maps_url": "https://maps.google.com/?q=Rayalaseema+Ruchulu+Hyderabad"},
        {"name": "AB's – Absolute Barbecues", "address": "Jubilee Hills, Hyderabad", "rating": 4.5,
         "estimated_cost": 700, "maps_url": "https://maps.google.com/?q=AB%27s+Absolute+Barbecues+Hyderabad"},
        {"name": "Ohri's Jiva Imperia", "address": "Basheer Bagh, Hyderabad", "rating": 4.1,
         "estimated_cost": 600, "maps_url": "https://maps.google.com/?q=Ohri%27s+Hyderabad"},
        {"name": "Shah Ghouse Cafe", "address": "Tolichowki, Hyderabad", "rating": 4.5,
         "estimated_cost": 200, "maps_url": "https://maps.google.com/?q=Shah+Ghouse+Hyderabad"},
        {"name": "Chutneys", "address": "Banjara Hills, Hyderabad", "rating": 4.3,
         "estimated_cost": 250, "maps_url": "https://maps.google.com/?q=Chutneys+Hyderabad"},
    ]
    return [r for r in all_restaurants if r["estimated_cost"] <= budget * 0.5][:4]


# ─────────────────────────────────────────────────────────────────────────────
# 2. MOVIES
# ─────────────────────────────────────────────────────────────────────────────
async def search_movies(
    preferred_genre: str = "",
    max_ticket_price: int = 400,
    limit: int = 5,
) -> list[dict]:
    """
    Search for current movies showing in Hyderabad via SerpAPI (Google Movies).
    Falls back to curated mock if no key.
    """
    if not SERPAPI_KEY:
        return _mock_movies(preferred_genre, max_ticket_price)

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            SERPAPI_BASE,
            params={
                "engine":    "google",
                "q":         f"movies showing today in Hyderabad cinemas {preferred_genre}",
                "api_key":   SERPAPI_KEY,
                "hl":        "en",
                "gl":        "in",
                "location":  "Hyderabad, Telangana, India",
            },
        )
    data = r.json()

    results = []
    # SerpAPI showtimes_results or knowledge graph
    for m in data.get("showtimes", [])[:limit]:
        results.append({
            "title":    m.get("name", "Unknown"),
            "theatre":  "PVR / INOX / AMB Cinemas",
            "genre":    preferred_genre or "Drama",
            "rating":   m.get("rating", "7.5/10"),
            "ticket_price": _estimate_ticket_price(max_ticket_price),
            "duration": m.get("duration", "2h 30m"),
            "bookmyshow_url": "https://in.bookmyshow.com",
        })

    return results or _mock_movies(preferred_genre, max_ticket_price)


def _estimate_ticket_price(max_price: int) -> int:
    if max_price >= 400:
        return 350   # premium
    elif max_price >= 250:
        return 220   # standard
    return 150       # matinee / balcony


def _mock_movies(genre: str, budget: int) -> list[dict]:
    movies = [
        {"title": "Check BookMyShow for Latest Shows", "theatre": "AMB Cinemas, Gachibowli",
         "genre": "Action", "rating": "8.1/10", "ticket_price": 300, "duration": "2h 25m",
         "bookmyshow_url": "https://in.bookmyshow.com/movies/hyderabad"},
        {"title": "PVR Inorbit – Current Blockbuster", "theatre": "PVR Inorbit Mall, HITEC City",
         "genre": "Thriller", "rating": "7.8/10", "ticket_price": 350, "duration": "2h 10m",
         "bookmyshow_url": "https://in.bookmyshow.com/movies/hyderabad"},
        {"title": "INOX GVK One – Matinee Show", "theatre": "INOX GVK One, Banjara Hills",
         "genre": "Comedy", "rating": "7.2/10", "ticket_price": 200, "duration": "1h 55m",
         "bookmyshow_url": "https://in.bookmyshow.com/movies/hyderabad"},
    ]
    return [m for m in movies if m["ticket_price"] <= budget][:3]


# ─────────────────────────────────────────────────────────────────────────────
# 3. PLACES / ATTRACTIONS
# ─────────────────────────────────────────────────────────────────────────────
async def search_places(
    interests: str = "sightseeing",
    max_entry_fee: int = 200,
    area: str = "Hyderabad",
    limit: int = 6,
) -> list[dict]:
    """
    Search Google Places for tourist spots / attractions in Hyderabad.
    """
    if not GOOGLE_API_KEY:
        return _mock_places(interests, max_entry_fee)

    query = f"{interests} attractions in {area} Hyderabad"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{PLACES_BASE}/textsearch/json",
            params={
                "query": query,
                "key":   GOOGLE_API_KEY,
                "type":  "tourist_attraction",
            },
        )
    data = r.json()
    results = []
    for p in data.get("results", [])[:limit]:
        results.append({
            "name":       p.get("name"),
            "address":    p.get("formatted_address", area),
            "rating":     p.get("rating", 4.0),
            "entry_fee":  _estimate_entry_fee(p.get("name", "")),
            "maps_url":   f"https://www.google.com/maps/place/?q=place_id:{p.get('place_id')}",
            "visit_duration_mins": 60,
        })
    return results or _mock_places(interests, max_entry_fee)


def _estimate_entry_fee(name: str) -> int:
    """Rough entry fee lookup for known Hyderabad spots."""
    fee_map = {
        "golconda": 35, "charminar": 25, "ramoji": 1150,
        "birla": 0, "hussain sagar": 0, "lumbini": 50,
        "nehru zoo": 80, "salar jung": 20, "qutb shahi": 15,
        "snow world": 799, "wonderla": 999,
    }
    name_lower = name.lower()
    for k, v in fee_map.items():
        if k in name_lower:
            return v
    return 50   # default assumption


def _mock_places(interests: str, budget: int) -> list[dict]:
    all_places = [
        {"name": "Hussain Sagar Lake & Tank Bund", "address": "Tank Bund Road, Hyderabad",
         "rating": 4.3, "entry_fee": 0, "visit_duration_mins": 60,
         "maps_url": "https://maps.google.com/?q=Hussain+Sagar+Lake"},
        {"name": "Golconda Fort", "address": "Ibrahim Bagh, Hyderabad",
         "rating": 4.4, "entry_fee": 35, "visit_duration_mins": 90,
         "maps_url": "https://maps.google.com/?q=Golconda+Fort"},
        {"name": "Charminar", "address": "Charminar, Old City, Hyderabad",
         "rating": 4.5, "entry_fee": 25, "visit_duration_mins": 60,
         "maps_url": "https://maps.google.com/?q=Charminar+Hyderabad"},
        {"name": "Lumbini Park", "address": "Secretariat Road, Hyderabad",
         "rating": 4.1, "entry_fee": 50, "visit_duration_mins": 60,
         "maps_url": "https://maps.google.com/?q=Lumbini+Park+Hyderabad"},
        {"name": "Birla Mandir", "address": "Naubath Pahad, Hyderabad",
         "rating": 4.6, "entry_fee": 0, "visit_duration_mins": 45,
         "maps_url": "https://maps.google.com/?q=Birla+Mandir+Hyderabad"},
        {"name": "Inorbit Mall", "address": "HITEC City, Hyderabad",
         "rating": 4.3, "entry_fee": 0, "visit_duration_mins": 120,
         "maps_url": "https://maps.google.com/?q=Inorbit+Mall+Hyderabad"},
    ]
    return [p for p in all_places if p["entry_fee"] <= budget * 0.15][:4]


# ─────────────────────────────────────────────────────────────────────────────
# 4. TRAVEL / DISTANCE
# ─────────────────────────────────────────────────────────────────────────────
async def get_travel_info(
    origin: str,
    destination: str,
) -> dict:
    """
    Get realistic travel time and cab fare estimate between two Hyderabad locations.
    Uses Google Distance Matrix API if key available, else heuristic estimate.
    """
    if not GOOGLE_API_KEY:
        return _mock_travel(origin, destination)

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{MAPS_BASE}/json",
            params={
                "origins":      f"{origin}, Hyderabad",
                "destinations": f"{destination}, Hyderabad",
                "key":          GOOGLE_API_KEY,
                "mode":         "driving",
                "units":        "metric",
            },
        )
    data = r.json()
    try:
        element     = data["rows"][0]["elements"][0]
        distance_km = element["distance"]["value"] / 1000
        duration_min = element["duration"]["value"] // 60
        fare        = _estimate_cab_fare(distance_km)
        return {
            "distance_km":   round(distance_km, 1),
            "duration_mins": duration_min,
            "cab_fare_inr":  fare,
            "mode":          "Uber/Ola",
        }
    except (KeyError, IndexError):
        return _mock_travel(origin, destination)


def _estimate_cab_fare(km: float) -> int:
    """Approx Uber/Ola fare: ₹50 base + ₹12/km."""
    return int(50 + km * 12)


def _mock_travel(origin: str, destination: str) -> dict:
    """Heuristic fallback — assumes average 8km, 20 min in Hyderabad."""
    return {
        "distance_km":   8.0,
        "duration_mins": 20,
        "cab_fare_inr":  130,
        "mode":          "Uber/Ola",
    }


# ─────────────────────────────────────────────────────────────────────────────
# TOOL DEFINITIONS for Claude
# ─────────────────────────────────────────────────────────────────────────────
TOOL_DEFINITIONS = [
    {
        "name": "search_restaurants",
        "description": (
            "Search for restaurants in a specific area of Hyderabad "
            "filtered by cuisine type and budget per person. "
            "Returns name, address, ratings, estimated cost per person, and Google Maps link."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "area":                   {"type": "string", "description": "Area/neighbourhood in Hyderabad, e.g. 'Banjara Hills'"},
                "max_budget_per_person":  {"type": "integer", "description": "Max price per person in INR"},
                "cuisine":                {"type": "string", "description": "Cuisine type, e.g. 'biryani', 'South Indian', 'Chinese'"},
            },
            "required": ["area", "max_budget_per_person"],
        },
    },
    {
        "name": "search_movies",
        "description": (
            "Get currently showing movies in Hyderabad cinemas. "
            "Filtered by preferred genre and max ticket price. "
            "Returns movie name, theatre, genre, rating, ticket price, and BookMyShow link."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "preferred_genre":    {"type": "string", "description": "Genre preference e.g. 'action', 'comedy', 'thriller'"},
                "max_ticket_price":   {"type": "integer", "description": "Max ticket price in INR"},
            },
            "required": ["max_ticket_price"],
        },
    },
    {
        "name": "search_places",
        "description": (
            "Search for tourist attractions, parks, malls, and entertainment "
            "venues in Hyderabad. Returns name, address, rating, entry fee, "
            "estimated visit duration, and Google Maps link."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "interests":      {"type": "string", "description": "Type of place e.g. 'historical', 'nature', 'shopping', 'entertainment'"},
                "max_entry_fee":  {"type": "integer", "description": "Max entry fee willing to pay in INR"},
                "area":           {"type": "string", "description": "Preferred area/zone in Hyderabad"},
            },
            "required": ["max_entry_fee"],
        },
    },
    {
        "name": "get_travel_info",
        "description": (
            "Get travel time and cab fare estimate between two locations in Hyderabad. "
            "Returns distance, duration in minutes, and estimated Uber/Ola fare."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "origin":      {"type": "string", "description": "Starting location name in Hyderabad"},
                "destination": {"type": "string", "description": "Destination location name in Hyderabad"},
            },
            "required": ["origin", "destination"],
        },
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# TOOL EXECUTOR
# ─────────────────────────────────────────────────────────────────────────────
async def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call and return JSON string result."""
    try:
        if tool_name == "search_restaurants":
            result = await search_restaurants(**tool_input)
        elif tool_name == "search_movies":
            result = await search_movies(**tool_input)
        elif tool_name == "search_places":
            result = await search_places(**tool_input)
        elif tool_name == "get_travel_info":
            result = await get_travel_info(**tool_input)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


import json

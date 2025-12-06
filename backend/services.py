import os
import httpx
import google.generativeai as genai
import re
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

async def get_google_places(lat: float, lng: float, query: str = "restaurant"):
    """
    Fetches places from Google Maps Places API (New Text Search).
    """
    if not GOOGLE_MAPS_API_KEY:
        return {"error": "Google Maps API Key missing"}

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.photos"
    }
    
    # We search for the query (e.g., "food", "hotel") near the user's location
    payload = {
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": 5000.0  # 5km radius
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        return {"error": f"Google API Error: {response.text}"}

async def get_ai_recommendation(user_mood: str, places_summary: str):
    """
    Uses Gemini to recommend the best spot based on mood.
    """
    if not GEMINI_API_KEY:
        return "I'm sorry, my AI brain is currently offline (API Key missing)."

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
        You are a travel assistant. 
        The user is feeling: "{user_mood}".
        Here is a list of nearby places found: {places_summary}.
        
        Based on the user's mood, recommend ONE or TWO specific places from the list.
        Explain WHY in a short, friendly sentence. If the mood is 'tired', prioritize hotels or quiet cafes.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

async def generate_itinerary(destination: str, days: int, travel_type: str, budget: str, mood: str, include_pois: bool = True):
    prompt = f"""
    Generate a {days}-day travel itinerary for {destination}.
    The trip style is {travel_type}, with a {budget} budget.
    Mood: {mood}.

    Please format the response clearly with headings like:
    Day 1: <activities>
    Day 2: <activities>

    Keep each day's suggestions to 2-4 short activity bullets or sentences.
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text or ""
        print("🔹 RAW GEMINI RESPONSE:\n", raw)

        # --- parsing (same robust parser you already have) ---
        text = raw.replace("\r\n", "\n").strip()
        text = re.sub(r"\*{1,3}", "", text)
        text = re.sub(r"\u2022", "-", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)

        day_split_regex = re.compile(r"(?:^|\n)(Day\s*\d+[:\-\)]?)", flags=re.IGNORECASE)
        parts = day_split_regex.split(text)

        plan = []
        if len(parts) > 1:
            i = 1
            while i < len(parts):
                marker = parts[i].strip()
                body = parts[i+1].strip() if i+1 < len(parts) else ""
                m = re.search(r"(\d+)", marker)
                day_num = int(m.group(1)) if m else len(plan) + 1
                body = re.sub(r"\n\s*\-\s*", " • ", body)
                body = re.sub(r"\n", " ", body)
                body = " ".join(body.split())
                plan.append({"day": day_num, "summary": body, "places": []})
                i += 2
        else:
            # fallback splitting into sentences (existing fallback)
            sentences = re.split(r'(?<=[.!?])\s+', text)
            if len(sentences) <= days:
                for idx in range(days):
                    summary = sentences[idx].strip() if idx < len(sentences) else ""
                    plan.append({"day": idx+1, "summary": summary, "places": []})
            else:
                chunk_size = max(1, len(sentences) // days)
                for idx in range(days):
                    chunk = sentences[idx*chunk_size:(idx+1)*chunk_size]
                    summary = " ".join(s.strip() for s in chunk)
                    plan.append({"day": idx+1, "summary": summary, "places": []})

        # Ensure list length matches days
        if len(plan) < days:
            for fill_day in range(len(plan)+1, days+1):
                plan.append({"day": fill_day, "summary": "", "places": []})

        # --- ENRICH: resolve destination coords and attach POIs ---
        if include_pois and GOOGLE_MAPS_API_KEY:
            coords = await geocode_place(destination)
            if coords:
                lat, lng = coords
                # For each day, call get_google_places using the day's summary as the query context.
                # The existing get_google_places expects (lat, lng, query)
                for entry in plan:
                    # choose a short search query: prefer 'tourist attraction' if summary suggests sightseeing,
                    # otherwise try the whole summary. Simpler approach: use 'tourist attraction' for now.
                    # You can later improve by detecting keywords like "museum", "restaurant", "fort"
                    query = "tourist attraction"
                    # If the summary mentions 'restaurant' or 'dinner' use restaurant query
                    if re.search(r"\b(restaurant|food|dinner|lunch|breakfast|cafe|snack)\b", entry["summary"], flags=re.IGNORECASE):
                        query = "restaurant"
                    # If summary mentions 'hotel' or 'resort'
                    if re.search(r"\b(hotel|resort|stay|accommodat)\b", entry["summary"], flags=re.IGNORECASE):
                        query = "hotel"

                    entry["places"] = await search_places_with_details(query, lat, lng)
                    attached = []
                    try:
                        results = places_resp.get("places", []) or places_resp.get("results", []) or []
                        # Field names differ by API; try common fields carefully
                        for p in results[:3]:
                            # best-effort extraction
                            name = p.get("displayName") or p.get("name") or p.get("place_name") or p.get("formatted_address")
                            addr = p.get("formattedAddress") or p.get("formatted_address") or p.get("vicinity") or ""
                            location = p.get("location") or p.get("geometry", {}).get("location") or p.get("geometry")
                            latp = None; lngp = None
                            if isinstance(location, dict):
                                latp = location.get("lat") or location.get("latitude") or location.get("latitudeE7")
                                lngp = location.get("lng") or location.get("longitude") or location.get("longitudeE7")
                            rating = p.get("rating") or p.get("userRatingCount") or None
                            attached.append({
                                "name": name,
                                "address": addr,
                                "lat": latp,
                                "lng": lngp,
                                "rating": rating
                            })
                    except Exception as e:
                        attached = []
                    entry["places"] = attached
            else:
                # geocoding failed; leave `places` empty
                pass

        return plan

    except Exception as e:
        return [{"day": 0, "summary": f"Error generating itinerary: {str(e)}", "places": []}]
async def geocode_place(place_name: str):
    """
    Convert a place name into lat/lng using Google Geocoding API.
    Returns (lat, lng) or None on failure.
    """
    if not GOOGLE_MAPS_API_KEY:
        return None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": place_name, "key": GOOGLE_MAPS_API_KEY}

    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, timeout=15.0)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return float(loc["lat"]), float(loc["lng"])
    return None
async def search_places_with_details(query: str, lat: float, lng: float):
    if not GOOGLE_MAPS_API_KEY:
        return {"error": "Missing API key"}

    # 1. TEXT SEARCH (to find place_id)
    text_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": f"{lat},{lng}",
        "radius": 5000,
        "key": GOOGLE_MAPS_API_KEY
    }

    async with httpx.AsyncClient() as client:
        r = await client.get(text_url, params=params)
        results = r.json().get("results", [])[:3]

        final_places = []
        for r in results:
            place_id = r.get("place_id")
            if not place_id:
                continue

            # 2. DETAILS API (richer info)
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            d_params = {
                "place_id": place_id,
                "fields": "name,rating,user_ratings_total,formatted_address,geometry,"
                          "types,photos,website,opening_hours",
                "key": GOOGLE_MAPS_API_KEY
            }
            d = await client.get(details_url, params=d_params)
            det = d.json().get("result", {})

            final_places.append({
                "name": det.get("name"),
                "address": det.get("formatted_address"),
                "lat": det.get("geometry", {}).get("location", {}).get("lat"),
                "lng": det.get("geometry", {}).get("location", {}).get("lng"),
                "rating": det.get("rating"),
                "reviews": det.get("user_ratings_total"),
                "website": det.get("website"),
                "types": det.get("types", []),
                "photos": det.get("photos", [])
            })

        return final_places
async def search_places_with_details(query: str, lat: float, lng: float, radius: int = 5000, max_results: int = 3):
    """
    Text Search -> Place Details pipeline.
    Returns a list of place dicts with name, address, coords, rating, reviews, website, types, photos.
    """
    if not GOOGLE_MAPS_API_KEY:
        return {"error": "Missing Google Maps API key"}

    text_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": f"{lat},{lng}",
        "radius": radius,
        "key": GOOGLE_MAPS_API_KEY
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(text_url, params=params)
        if r.status_code != 200:
            return {"error": f"Places Text Search error: {r.text}"}
        text_results = r.json().get("results", [])[:max_results]

        final_places = []
        for r_item in text_results:
            place_id = r_item.get("place_id")
            if not place_id:
                continue

            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            d_params = {
                "place_id": place_id,
                "fields": "name,rating,user_ratings_total,formatted_address,geometry,types,photos,website,opening_hours",
                "key": GOOGLE_MAPS_API_KEY
            }
            d = await client.get(details_url, params=d_params)
            if d.status_code != 200:
                continue
            det = d.json().get("result", {})

            final_places.append({
                "name": det.get("name"),
                "address": det.get("formatted_address"),
                "lat": det.get("geometry", {}).get("location", {}).get("lat"),
                "lng": det.get("geometry", {}).get("location", {}).get("lng"),
                "rating": det.get("rating"),
                "reviews": det.get("user_ratings_total"),
                "website": det.get("website"),
                "types": det.get("types", []),
                "photos": det.get("photos", [])  # client can request photo using photo_reference via Places Photo API
            })

        return final_places

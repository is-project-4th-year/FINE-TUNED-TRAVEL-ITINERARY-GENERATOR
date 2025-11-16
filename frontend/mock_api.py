import time, uuid

def extract_itinerary(text: str):
    """Fake extractor - returns a simple parsed dict"""
    time.sleep(0.2)
    return {
        "destination": "Nairobi",
        "theme": "museums and markets",
        "dates": ["2025-12-01", "2025-12-03"]
    }

def generate_itinerary(**kwargs):
    """Fake generator - returns a multi-day blueprint text"""
    time.sleep(0.6)
    dest = kwargs.get("destination") or kwargs.get("description", "Unknown")
    days = 1
    try:
        # naive days calc
        days = max(1, (kwargs.get("end_date") - kwargs.get("start_date")).days) 
    except Exception:
        days = kwargs.get("days", 1)

    title = f"{dest} — {kwargs.get('description','Curated trip')}"
    uid = str(uuid.uuid4())[:8]
    body = f"## {title}\n\n**Trip id:** {uid}\n\n"

    for d in range(1, min(days, 7)+1):
        body += f"### Day {d}\n- Morning: Explore local culture and cafes\n- Afternoon: Visit top museum or market\n- Evening: Dinner at a recommended restaurant\n\n"

    body += "\n---\n*This is mock output. Replace `mock_api` with real API calls.*"
    return body

# Simple in-memory store for saved itineraries (for demo)
_STORE = {}
def save_itinerary(title, content):
    key = str(uuid.uuid4())
    _STORE[key] = {"title": title, "content": content}
    return key

def list_itineraries():
    return [{"id": k, "title": v["title"]} for k, v in _STORE.items()]

def get_itinerary(itid):
    return _STORE.get(itid)

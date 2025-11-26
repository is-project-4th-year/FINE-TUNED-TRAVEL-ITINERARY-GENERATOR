import asyncio
import re
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uuid

from loader import flan_extract, hermes_generate, warm_model, debug_model_status

try:
    warm_model(async_spawn=True)
except Exception:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("itinerary")

app = FastAPI()

@app.get("/test")
def test():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_TOKENS = 600
HERMES_TIMEOUT_SECONDS = 500

class ItineraryRequest(BaseModel):
    text: str
    days: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    travelers: Optional[int] = None
    budget: Optional[float] = None

def _safe_int_from_any(value, default=None):
    if value is None:
        return default
    if isinstance(value, int):
        return value
    try:
        m = re.search(r"\d+", str(value))
        if m:
            return int(m.group(0))
    except Exception:
        pass
    return default

def _is_indoor_preferred(summary: str) -> bool:
    return False

CATEGORY_MAP = {
    "museum": "a popular art museum",
    "historic": "a historic landmark",
    "building": "an iconic local building",
    "tower": "a modern observation tower",
    "viewpoint": "a scenic viewpoint",
    "attraction": "a well-known local attraction",
    "neighbourhood": "a lively local neighborhood",
    "natural": "a natural outdoor spot",
}

def _category_to_descriptor(categories):
    if not categories:
        return None
    for c in (categories or []):
        lc = str(c).lower()
        for key, phrase in CATEGORY_MAP.items():
            if key in lc:
                return phrase
    return None

def _pick_poi(pois: List[Dict[str, Any]], used: set, indoor_pref: bool) -> Dict[str, Any]:
    if not pois:
        return {"name": "Unknown POI", "address": "", "categories": []}
    for p in pois:
        name = p.get("name") or ""
        if name in used:
            continue
        used.add(name)
        return p
    first = pois[0]
    used.add(first.get("name", ""))
    return first

def _format_from_json(it_j: Dict[str, Any]) -> str:
    city = it_j.get("city", "your destination")
    days = it_j.get("days", [])
    if not days:
        return f"Here’s a simple plan for exploring {city}."
    trav = it_j.get("travelers")
    budget = it_j.get("budget")
    lines = []
    for d in days:
        lines.append(f"Day {d['day']}")
        for act in d["activities"]:
            tod = act.get("time_of_day", "").capitalize()
            title = act.get("title") or "Unknown location"
            addr = act.get("address")
            desc = act.get("descriptor")
            if tod == "Morning":
                sentence = f"Morning: You'll start your day at the {desc or title}. This is a great place to learn about the history of {city} and the surrounding area. It's also a great place to get some exercise and fresh air. The {title} is located at {addr}."
            elif tod == "Afternoon":
                sentence = f"Afternoon: After you've had your fill of the {desc or title}, you'll head to the {desc or title}. This is a great place to get a bird's eye view of the city and the surrounding area. The {title} is located at {addr}."
            elif tod == "Evening":
                sentence = f"Evening: After you've had your fill of the {desc or title}, you'll head to the {desc or title}. This is a great place to learn about the history of {city} and the surrounding area. The {title} is located at {addr}."
            else:
                sentence = f"{tod}: {title} — {desc} — {addr}"
            lines.append(sentence)
        lines.append("")
    return "\n".join(lines).strip()

async def _run_hermes_with_timeout(prompt: str, timeout_seconds: int = HERMES_TIMEOUT_SECONDS, max_tokens: int = MAX_TOKENS) -> Optional[str]:
    loop = asyncio.get_running_loop()
    def call():
        try:
            return hermes_generate(prompt, max_tokens=max_tokens, sampling=False, temperature=0.0)
        except Exception as e:
            logger.exception("hermes_generate raised")
            return None
    try:
        raw = await asyncio.wait_for(loop.run_in_executor(None, call), timeout=timeout_seconds)
        return raw
    except asyncio.TimeoutError:
        logger.warning("Hermes generation timed out after %s seconds", timeout_seconds)
        return None
    except Exception:
        logger.exception("Hermes unexpected error")
        return None

@app.get("/health")
def health():
    return {"status": "ok", "model_status": debug_model_status()}

@app.post("/itinerary")
async def itinerary(req: ItineraryRequest):
    print("🔥 Incoming request payload:", req.dict())
    loop = asyncio.get_running_loop()
    try:
        extraction = await loop.run_in_executor(None, flan_extract, req.text)
        city = "Unknown"
        if extraction.get("destinations") and isinstance(extraction["destinations"], list):
            d0 = extraction["destinations"][0] if extraction["destinations"] else None
            if isinstance(d0, dict):
                city = d0.get("city") or city
        days = req.days
        if days is None:
            days = _safe_int_from_any(extraction.get("days"), default=2)
        else:
            days = _safe_int_from_any(days, default=None)
        if days is None or days <= 0 or days > 14:
            raise HTTPException(status_code=400, detail="Invalid 'days' value")
        from aggregator import run_aggregator_pipeline
        context = await loop.run_in_executor(None, run_aggregator_pipeline, city, days)
        ctx = context or {}
        blocks = ctx.get("context_blocks", {}) or {}
        pois = blocks.get("pois", []) or []
        events = blocks.get("events", []) or []
        weather_list = blocks.get("weather", []) or []
        date_range = ctx.get("date_range", [])
        used = set()
        day_blocks = []
        for i in range(days):
            date = date_range[i] if i < len(date_range) else None
            p_m = _pick_poi(pois, used, indoor_pref=False)
            d_m = _category_to_descriptor(p_m.get("categories"))
            p_a = _pick_poi(pois, used, indoor_pref=False)
            d_a = _category_to_descriptor(p_a.get("categories"))
            p_e = _pick_poi(pois, used, indoor_pref=False)
            d_e = _category_to_descriptor(p_e.get("categories"))
            day_blocks.append({
                "day": i + 1,
                "date": date,
                "activities": [
                    {"time_of_day": "morning", "title": p_m.get("name"), "address": p_m.get("address"), "descriptor": d_m},
                    {"time_of_day": "afternoon", "title": p_a.get("name"), "address": p_a.get("address"), "descriptor": d_a},
                    {"time_of_day": "evening", "title": p_e.get("name"), "address": p_e.get("address"), "descriptor": d_e},
                ],
            })
        itinerary_json = {
            "city": city,
            "days": day_blocks,
            "travelers": req.travelers,
            "budget": req.budget,
        }
        # Always use the fallback conversational format
        return {"itinerary": _format_from_json(itinerary_json)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("itinerary fatal")
        raise HTTPException(status_code=500, detail=f"itinerary generation failed: {e}")

# -------------------- JOB SYSTEM --------------------
job_store = {}

class JobStatus(str):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"

def start_itinerary_job(job_id: str, req: dict):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    job_store[job_id]["status"] = JobStatus.RUNNING
    try:
        extraction = flan_extract(req["text"])
        city = "Unknown"
        if extraction.get("destinations") and isinstance(extraction["destinations"], list):
            d0 = extraction["destinations"][0] if extraction["destinations"] else None
            if isinstance(d0, dict):
                city = d0.get("city") or city
        days = req.get("days")
        if days is None:
            days = _safe_int_from_any(extraction.get("days"), default=2)
        else:
            days = _safe_int_from_any(days, default=None)
        if days is None or days <= 0 or days > 14:
            job_store[job_id]["status"] = JobStatus.ERROR
            job_store[job_id]["result"] = {"error": "Invalid 'days' value"}
            return
        from aggregator import run_aggregator_pipeline
        context = run_aggregator_pipeline(city, days)
        ctx = context or {}
        blocks = ctx.get("context_blocks", {}) or {}
        pois = blocks.get("pois", []) or []
        events = blocks.get("events", []) or []
        weather_list = blocks.get("weather", []) or []
        date_range = ctx.get("date_range", [])
        used = set()
        day_blocks = []
        for i in range(days):
            date = date_range[i] if i < len(date_range) else None
            p_m = _pick_poi(pois, used, indoor_pref=False)
            d_m = _category_to_descriptor(p_m.get("categories"))
            p_a = _pick_poi(pois, used, indoor_pref=False)
            d_a = _category_to_descriptor(p_a.get("categories"))
            p_e = _pick_poi(pois, used, indoor_pref=False)
            d_e = _category_to_descriptor(p_e.get("categories"))
            day_blocks.append({
                "day": i + 1,
                "date": date,
                "activities": [
                    {"time_of_day": "morning", "title": p_m.get("name"), "address": p_m.get("address"), "descriptor": d_m},
                    {"time_of_day": "afternoon", "title": p_a.get("name"), "address": p_a.get("address"), "descriptor": d_a},
                    {"time_of_day": "evening", "title": p_e.get("name"), "address": p_e.get("address"), "descriptor": d_e},
                ],
            })
        itinerary_json = {
            "city": city,
            "days": day_blocks,
            "travelers": req.get("travelers"),
            "budget": req.get("budget"),
        }
        # Always use the fallback conversational format
        job_store[job_id]["status"] = JobStatus.DONE
        job_store[job_id]["result"] = {"itinerary": _format_from_json(itinerary_json)}
    except Exception as e:
        job_store[job_id]["status"] = JobStatus.ERROR
        job_store[job_id]["result"] = {"error": str(e)}

@app.post("/itinerary/job")
def create_itinerary_job(req: ItineraryRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": JobStatus.PENDING, "result": None}
    background_tasks.add_task(start_itinerary_job, job_id, req.dict())
    return {"job_id": job_id, "status": JobStatus.PENDING}

@app.get("/itinerary/job/{job_id}")
def get_itinerary_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": job["status"], "result": job["result"]}
import asyncio
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# use your existing modules
from loader import flan_extract  # keep hermes_generate available if needed elsewhere
from aggregator import run_aggregator_pipeline

app = FastAPI()


# -------------------------
# Utilities
# -------------------------
class ItineraryRequest(BaseModel):
    text: str
    days: int


def _parse_precip_mm(summary: str) -> Optional[float]:
    """Return precipitation in mm if found, else None."""
    if not summary:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*mm", summary)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            return None
    return None


def _is_indoor_preferred(weather_summary: str) -> bool:
    """Decide if indoor POIs should be preferred based on precipitation."""
    mm = _parse_precip_mm(weather_summary or "")
    if mm is None:
        return False
    return mm > 10.0


def _pick_poi(pois: List[Dict[str, Any]], used: set, indoor_preference: bool) -> Dict[str, Any]:
    """
    Deterministic selection:
    - If indoor_preference, try to pick a POI with 'museum','theatre','indoor','gallery','building' in categories.
    - Else pick the first unused POI.
    - If none unused remain, recycle deterministically.
    """
    if not pois:
        return {"name": "Unknown POI", "address": "", "categories": []}

    def is_indoor(p):
        cats = " ".join(p.get("categories", [])).lower()
        for k in ("museum", "theatre", "gallery", "indoor", "building"):
            if k in cats:
                return True
        return False

    # try to find suitable unused candidate
    for p in pois:
        name = p.get("name") or ""
        if name in used:
            continue
        if indoor_preference:
            if is_indoor(p):
                used.add(name)
                return p
        else:
            used.add(name)
            return p

    # if we reach here, no unused matching; try any unused
    for p in pois:
        name = p.get("name") or ""
        if name not in used:
            used.add(name)
            return p

    # all used: choose the first one deterministically (do not hallucinate)
    first = pois[0]
    used.add(first.get("name", ""))
    return first


def _pick_event_for_date(events: List[Dict[str, Any]], date: Optional[str]) -> Optional[Dict[str, Any]]:
    if not date or not events:
        return None
    for e in events:
        if e.get("date") == date:
            return e
    return None


def _format_poi_description_minimal(poi: Dict[str, Any]) -> str:
    """
    Minimal descriptive template (tone C):
    Examples:
      "Cloud Gate. Located at AT&T Plaza. A short visit to the sculpture."
    Keep short, factual and grounded in provided fields (name, address, categories).
    """
    name = poi.get("name", "Unknown")
    addr = poi.get("address", "")
    categories = poi.get("categories", []) or []
    cats = ", ".join(categories[:2])
    parts = [f"{name}."]
    if addr:
        parts.append(f"Located at {addr}.")
    if cats:
        parts.append(f"Type: {cats}.")
    # keep it compact: join with single space
    return " ".join(parts)


def _format_event_description_minimal(event: Dict[str, Any]) -> str:
    """
    Minimal event description template (tone C).
    Example:
      "Chicago Blackhawks vs. Seattle Kraken @ United Center on 2025-11-20."
    """
    title = event.get("title", "Event")
    venue = event.get("venue")
    date = event.get("date")
    parts = [title]
    if venue:
        parts.append(f"@ {venue}")
    if date:
        parts.append(f"on {date}")
    return " ".join(parts) + "."


# -------------------------
# Health path
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------
# Main itinerary endpoint (deterministic generator)
# -------------------------
@app.post("/itinerary")
async def itinerary(req: ItineraryRequest):
    """
    Deterministic, grounded itinerary builder.
    Does NOT rely on the language model to invent POIs/events.
    Produces minimal, factual descriptions using only context data.
    """
    if req.days <= 0 or req.days > 14:
        raise HTTPException(status_code=400, detail="days must be between 1 and 14")

    loop = asyncio.get_running_loop()

    try:
        # 1) Extract basic trip info (city, days) via flan_extract (or heuristic)
        extraction = await loop.run_in_executor(None, flan_extract, req.text)
        city = "Unknown"
        if extraction.get("destinations") and isinstance(extraction["destinations"], list):
            dest0 = extraction["destinations"][0] if extraction["destinations"] else None
            if isinstance(dest0, dict):
                city = dest0.get("city") or city

        # 2) Run aggregator pipeline to gather weather/pois/events
        context = await loop.run_in_executor(None, run_aggregator_pipeline, city, req.days)
        context_blocks = context.get("context_blocks", {})
        weather_list = context_blocks.get("weather", []) or []
        pois = context_blocks.get("pois", []) or []
        events = context_blocks.get("events", []) or []
        date_range = context.get("date_range", []) or []

        # Safety defaults
        # Ensure weather_list has at least req.days entries (pad with empty summaries)
        while len(weather_list) < req.days:
            weather_list.append({"date": None, "summary": "Data unavailable"})

        # Determine day-specific preferences and selections
        used_pois = set()
        itinerary_lines: List[str] = []

        for day_idx in range(req.days):
            day_num = day_idx + 1
            day_date = date_range[day_idx] if day_idx < len(date_range) else None
            weather_obj = weather_list[day_idx] if day_idx < len(weather_list) else {"summary": "Data unavailable"}
            indoor_pref = _is_indoor_preferred(weather_obj.get("summary", ""))

            # Morning POI
            morning_poi = _pick_poi(pois, used_pois, indoor_preference=False)  # mornings usually outdoor ok
            morning_desc = _format_poi_description_minimal(morning_poi)

            # Afternoon POI (prefer not to repeat)
            afternoon_poi = _pick_poi(pois, used_pois, indoor_preference=indoor_pref)
            afternoon_desc = _format_poi_description_minimal(afternoon_poi)

            # Evening: prefer event on that date; otherwise fallback POI
            event_for_day = _pick_event_for_date(events, day_date)
            if event_for_day:
                evening_desc = _format_event_description_minimal(event_for_day)
            else:
                # fallback: pick a POI (prefer indoor if raining)
                fallback_poi = _pick_poi(pois, used_pois, indoor_preference=indoor_pref)
                evening_desc = _format_poi_description_minimal(fallback_poi)

            # Build day block (minimal tone)
            itinerary_lines.append(f"Day {day_num}")
            itinerary_lines.append(f"Morning (09:00–12:00): {morning_desc}")
            itinerary_lines.append(f"Afternoon (13:00–17:00): {afternoon_desc}")
            itinerary_lines.append(f"Evening (18:00–22:00): {evening_desc}")
            if day_idx < req.days - 1:
                itinerary_lines.append("")  # blank line between days

        itinerary_text = "\n".join(itinerary_lines).strip()

        # Final safety: if empty, return an informative error string (no hallucination)
        if not itinerary_text:
            itinerary_text = "[ERROR] Could not build itinerary from available context."

        return {"itinerary": itinerary_text}

    except Exception as e:
        # return useful debug to user (but not stack traces)
        raise HTTPException(status_code=500, detail=f"itinerary generation failed: {str(e)}")

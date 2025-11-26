# loader.py — robust loader + hermes_generate + flan_extract
import os
import re
import json
import uuid
from typing import Optional

from dotenv import load_dotenv
load_dotenv("/workspace/travelplanner_runpod/.env")

# Environment helper
def get_env(key: str, default=None) -> Optional[str]:
    v = os.getenv(key, default)
    if v is None:
        print(f"WARNING: Missing env var: {key}")
    return v

# Try to import transformers lazily
_transformers_available = False
_tokenizer = None
_model = None
_device = None

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    _transformers_available = True
except Exception as e:
    print("Transformers unavailable:", e)
    _transformers_available = False

def _load_hermes_model():
    """
    Attempts to load the local Hermes model directory (HERMES_MODEL env var).
    Returns True if loaded, False otherwise.
    """
    global _model, _tokenizer, _device

    if not _transformers_available:
        return False

    if _model is not None and _tokenizer is not None:
        return True

    model_path = get_env("HERMES_MODEL")
    if not model_path:
        print("HERMES_MODEL not set. Skipping heavy model load.")
        return False

    try:
        print(f"Loading Hermes model from: {model_path}")
        # AutoTokenizer + AutoModelForCausalLM will pick the correct classes
        _tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        # use device_map auto to use GPU if available
        _model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", trust_remote_code=True)
        # compute device for small fallback ops
        _device = next(_model.parameters()).device
        print("MODEL:", type(_model))
        print("TOKENIZER:", type(_tokenizer))
        return True
    except Exception as e:
        print("Failed to load hermes model:", e)
        _tokenizer = None
        _model = None
        return False

def hermes_generate(prompt: str, max_tokens: int = 600, temperature: float = 0.3, sampling: bool = True, debug: bool = False) -> str:
    """
    Generate text from the Hermes model if available, otherwise fallback deterministic generator.
    Returns the generated string (raw).
    """
    # Try to ensure model is loaded
    loaded = _load_hermes_model()

    if loaded and _model is not None and _tokenizer is not None:
        try:
            if debug:
                print("hermes_generate: using transformers model")
            # Tokenize; ensure truncation safety: set max_length conservatively
            inputs = _tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
            # move inputs to model device
            if _device is not None:
                inputs = {k: v.to(_device) for k, v in inputs.items()}

            gen_kwargs = {
                "max_new_tokens": int(max_tokens),
                "do_sample": bool(sampling),
                "temperature": float(temperature) if sampling else 0.0,
                "top_k": 50,
                "top_p": 0.95,
                # supply eos/pad tokens if available
                "eos_token_id": getattr(_tokenizer, "eos_token_id", None),
                "pad_token_id": getattr(_tokenizer, "pad_token_id", None),
                "use_cache": True,
            }

            if debug:
                print("hermes_generate: gen_kwargs:", gen_kwargs)

            with (torch.no_grad()):
                outputs = _model.generate(**inputs, **{k: v for k, v in gen_kwargs.items() if v is not None})
            text = _tokenizer.decode(outputs[0], skip_special_tokens=True)
            # If model echoes the prompt, try to remove the prompt prefix (naive)
            if text.startswith(prompt):
                text = text[len(prompt):].strip()
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"Hermes generation failed: {e}")
            # fallthrough to fallback below

    # -----------------------
    # Deterministic fallback
    # -----------------------
    if debug:
        print("hermes_generate: fallback deterministic generator")
    # quick heuristic: try to detect requested days
    days = 2
    m = re.search(r"(\d+)[-\s]*day", prompt, re.I)
    if m:
        try:
            days = int(m.group(1))
        except:
            days = 2

    # skeleton fallback — concrete but generic
    parts = []
    for d in range(1, days + 1):
        parts.append(f"Day {d}:")
        parts.append("")
        parts.append(f"- Morning (09:00–12:00): <POI #{d} from context>")
        parts.append(f"- Afternoon (13:00–17:00): <POI #{d+days} from context>")
        parts.append(f"- Evening (18:00–22:00): <event on day {d} or fallback POI>")
        parts.append("")
    return "\n".join(parts).strip()

# -----------------------------------------
# flan_extract: small heuristic extractor
# -----------------------------------------
def flan_extract(text: str, debug: bool = False):
    """
    Fallback extractor: returns a structure used by main.py
    """
    # trip id
    trip_id = str(uuid.uuid4())

    # very lightweight city extraction
    city = None
    m = re.search(r"to\s+([A-Z][a-zA-Z\s\-]{1,40})", text)
    if not m:
        m = re.search(r"in\s+([A-Z][a-zA-Z\s\-]{1,40})", text)
    if m:
        city = m.group(1).strip().strip(",.")
    if not city:
        # last capitalized word fallback
        caps = re.findall(r"\b([A-Z][a-z]{2,})\b", text)
        city = caps[-1] if caps else "Unknown"

    days = 1
    m = re.search(r"(\d+)[-\s]*day", text, re.I)
    if m:
        try:
            days = int(m.group(1))
        except:
            days = 1

    return {
        "trip_id": trip_id,
        "title": f"Trip to {city}",
        "start_date": None,
        "end_date": None,
        "num_travelers": None,
        "destinations": [{"city": city, "country": None}],
        "days": [{} for _ in range(days)],
        "budget_usd": None,
        "raw_text": text
    }

# quick smoke test when run directly
if __name__ == "__main__":
    print("loader.py smoke test")
    print(get_env("HERMES_MODEL"))
    print(flan_extract("Plan a 2-day trip to Dallas", debug=True))
    print(hermes_generate("Write a 2-day itinerary for Dallas. Begin with 'Day 1:'", debug=True))

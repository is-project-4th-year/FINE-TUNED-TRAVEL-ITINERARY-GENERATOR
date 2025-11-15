from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from loader import load_extractor, load_generator
import asyncio
import torch

from loader import load_extractor, load_generator

app = FastAPI(title="TravelPlanner API")

# ----------------------------
# CORS (frontend compatibility)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend origin later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Load models at startup
# ----------------------------
@app.on_event("startup")
async def startup_event():
    print("🔄 Loading models into FastAPI app.state...")
    extractor, tokenizer_ex = load_extractor()
    generator, tokenizer_gen = load_generator()

    app.state.extractor = extractor
    app.state.tokenizer_ex = tokenizer_ex
    app.state.generator = generator
    app.state.tokenizer_gen = tokenizer_gen
    app.state.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("✅ Models loaded into app.state.")


# ----------------------------
# Request Schemas
# ----------------------------
class ExtractRequest(BaseModel):
    text: str

class AggregateRequest(BaseModel):
    location: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class GenerateRequest(BaseModel):
    context: Dict[str, Any]
    length: Optional[int] = 700  # default


# ----------------------------
# Inference functions
# ----------------------------
def run_extraction(prompt: str, max_length: int = 512):
    tok = app.state.tokenizer_ex
    model = app.state.extractor
    inputs = tok(prompt, return_tensors="pt", truncation=True).to(app.state.device)

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_length=max_length
        )

    return tok.batch_decode(out, skip_special_tokens=True)[0]


def run_generation(prompt: str, max_length: int = 700):
    tok = app.state.tokenizer_gen
    model = app.state.generator

    # Ensure pad token is set
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    inputs = tok(prompt, return_tensors="pt").to(app.state.device)

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_length,
            pad_token_id=tok.eos_token_id,
            eos_token_id=tok.eos_token_id,
            do_sample=True,
            temperature=0.85,
            top_p=0.9,
            repetition_penalty=1.1,
            suppress_tokens=[],
        )

    return tok.batch_decode(out, skip_special_tokens=True)[0]


# ----------------------------
# API ENDPOINTS
# ----------------------------

@app.post("/extract")
async def extract(req: ExtractRequest):
    loop = asyncio.get_running_loop()
    out = await loop.run_in_executor(None, run_extraction, req.text)
    return {"extraction": out}


@app.post("/aggregate")
async def aggregate(req: AggregateRequest):
    # Placeholder for your weather/events/POI aggregator
    return {
        "location": req.location,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "preferences": req.preferences,
        "note": "Aggregator logic goes here."
    }


@app.post("/generate")
async def generate(req: GenerateRequest):
    prompt = req.context.get("prompt") or str(req.context)

    loop = asyncio.get_running_loop()
    out = await loop.run_in_executor(
        None,
        run_generation,
        prompt,
        req.length
    )

    return {"itinerary": out}


@app.get("/")
async def root():
    return {"message": "TravelPlanner API is running"}

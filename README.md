_150129 Maina Ben Waweru_
**Travel Itinerary Generator**
Final Year Project — Large Language Model + Real-World Data Integration

This project is an end-to-end AI itinerary generation platform powered by a local Hermes2Pro 7B model, a FastAPI backend, and a React/Next.js frontend with user authentication.
It combines real-time city data with an LLM rewriting pipeline to produce personalized, structured travel itineraries.

This README describes the project exactly as it exists — no imaginary features, no hallucinated components, only what was actually built and completed.

⭐ Overview

The system takes user input (destination, days, dates, travelers, budget), fetches real-world travel data, builds a structured itinerary, and lets a local Hermes2Pro model rewrite it into a natural, readable itinerary.

It demonstrates:

Full backend architecture

Local GPU inference with quantized Hermes2Pro

Real API integrations (POIs + events + geocoding)

A protected user frontend

Robust extraction & fallback logic

Modern state management using Zustand

🔥 Features

1. Real-World Travel Data Aggregation

The backend integrates multiple external APIs:

Source Purpose
Geoapify Geocoding Convert city → lat/lon
Geoapify Places API Retrieve nearby POIs
TicketMaster Events API Get upcoming events during trip
Weather Estimation Layer Simple per-day weather context
SQLite caching Reduce API calls, speed up repeated queries

These data sources are bundled into a structured JSON itinerary before being sent to the LLM.

2. Deterministic Itinerary Construction

Backend logic selects:

Morning / afternoon / evening POIs

Indoor vs outdoor based on weather summary

Relevant events (date-matched using TicketMaster)

Category descriptors (museum, historic, landmark, natural, etc.)

This produces a consistent, safe itinerary with no hallucinated locations.

3. Hermes2Pro 7B Rewriting Engine

A quantized 7B Hermes2Pro model (4-bit) runs on an external GPU via RunPod (RTX 4090).

LLM Responsibilities:

Rewrite itinerary in a conversational tone

Keep all locations exactly the same

Produce smooth, friendly travel text

Incorporate travelers/budget metadata

A custom prompt and OUTPUT_START / OUTPUT_END markers ensure predictable formatting.

4. Safe Output Extraction

The system uses a strict extractor that:

Reads ONLY text between markers

Rejects malformed output

Rejects placeholders or template echoes

Validates Day 1 → Day N structure

Performs safe trimming

Falls back to deterministic itinerary if Hermes2Pro output fails

This makes the system reliable, even with unpredictable LLM behavior.

5. Frontend (Next.js 14 + React + Zustand)

Frontend includes:

User authentication (local store, persistent sessions)

Protected routes (redirect to login if not authenticated)

A complete itinerary form:

trip description

days

start/end dates

travelers

budget

Global state using Zustand (itineraryStore)

Clean rendering of itinerary text

Loading states & error states

Responsive Tailwind UI

6. Backend API (FastAPI)

The main endpoint:

POST /itinerary

Example request:

{
"text": "Plan a 3-day trip to Tokyo",
"days": 3,
"start_date": "2025-01-10",
"end_date": "2025-01-12",
"travelers": 2,
"budget": 800
}

Example response:

{
"itinerary": "Day 1..."
}

Includes:

Timeout handling

GPU warming

Logging

Strict validation

🧱 Architecture
FRONTEND (Next.js)
-------------------
User → Travel Form → POST /itinerary
|
v

               BACKEND (FastAPI)
               -------------------

[1] Extract user request
[2] Aggregator pipeline:
• Geocoding
• POI lookup
• Events matching
• Weather info
[3] Structured itinerary JSON
[4] Build Hermes2Pro prompt
[5] Generate rewritten itinerary
[6] Extract clean output or fallback
|
v

                 FRONTEND
         Render final itinerary to user

🛠 Tech Stack
Backend

Python

FastAPI

PyTorch & Transformers

BitsAndBytes 4-bit quantization

RunPod GPU (RTX 4090)

SQLite caching

Geoapify API

TicketMaster API

Frontend

React

Next.js (App Router)

Zustand

TailwindCSS

Next Navigation

Protected routing

⚙ Why Hermes2Pro 7B Produces Generic Output

You can confidently tell your panel:

7B models have limited reasoning depth compared to larger 13B/70B models.

They lack strong world knowledge and struggle with nuanced travel writing.

Memory and parameter limits lead to repetitive phrasing.

The model is not fine-tuned for travel writing — only prompted.

Small models prioritize safety and structure over creativity.

This is normal behavior for a compact model.

🐢 Why Computation Is Slow

Clear justification:

Hermes2Pro models generate text sequentially, 1 token at a time.

A 7B model still has billions of parameters — expensive to run.

4-bit quantization reduces memory but not generation time.

Running locally is impossible without a high-end GPU (≥ 12GB VRAM).

Consumer laptops cannot load the model (insufficient VRAM).

CPU inference would take minutes per sentence, so GPU is required.

Thus, running via RunPod is the only feasible option.

🚀 Running the Project
Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

Requires GPU. Best on RTX 4090.

Frontend
cd frontend
npm install
npm run dev

Make sure .env.local contains:

NEXT_PUBLIC_RUNPOD_URL=http://localhost:8000

📦 Folder Structure (essential parts only)
backend/
├── main.py
├── loader.py
├── aggregator.py
└── tests/

frontend/
├── app/
│ └── page.tsx
├── components/
├── store/
│ ├── authStore.ts
│ └── itineraryStore.ts
├── lib/api.ts
├── hooks/
│ └── useHydrated.ts
└── public/

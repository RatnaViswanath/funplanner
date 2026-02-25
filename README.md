# 🗺️ FunPlanner — Agentic AI for Hyderabad

An agentic AI app that takes your free time + budget and builds a real hourly plan
by autonomously searching Google Places, BookMyShow, and Maps.

---

## Architecture

```
User Prompt (React frontend)
        │
        ▼  POST /plan  (SSE stream)
┌───────────────────────────────┐
│   FastAPI Backend             │
│                               │
│   ┌─────────────────────────┐ │
│   │  Claude Sonnet (Agent)  │ │
│   │  - Parses intent        │ │
│   │  - Decides tool calls   │ │
│   │  - Synthesizes plan     │ │
│   └────────┬────────────────┘ │
│            │ Tool calls        │
│   ┌────────▼────────────────┐ │
│   │  Tools (run parallel)  │  │
│   │  • Google Places API   │  │
│   │  • Google Maps Matrix  │  │
│   │  • SerpAPI (movies)    │  │
│   └────────────────────────┘  │
└───────────────────────────────┘
        │
        ▼  SSE Events
  agent_step  → frontend animates progress
  tool_result → shows data count fetched
  final_plan  → renders timeline itinerary
```

---

## Quick Start

### 1. Backend

```bash
cd backend
cp .env.example .env
# Fill in your API keys in .env

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend will be live at: http://localhost:8000

### 2. Frontend

```bash
# If using Create React App
npx create-react-app funplanner
cd funplanner/src
# Replace App.js content with fun-planner-connected.jsx content
npm start
```

```bash
# If using Vite (recommended)
npm create vite@latest funplanner -- --template react
cd funplanner/src
# Replace App.jsx with fun-planner-connected.jsx content
npm install && npm run dev
```

---

## API Keys (What You Need)

| Key | Required? | Free Tier | Get It |
|-----|-----------|-----------|--------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Pay per use (~₹1-2/plan) | console.anthropic.com |
| `GOOGLE_API_KEY` | Recommended | $200 free/month | console.cloud.google.com |
| `SERPAPI_KEY` | Optional | 100 searches/month free | serpapi.com |

**Without Google/SerpAPI keys:** The app falls back to curated mock data for
Hyderabad restaurants, places, and movies. Great for development and demos!

**Google APIs to enable** (in your Google Cloud Console):
- Places API
- Distance Matrix API

---

## Folder Structure

```
funplanner/
├── backend/
│   ├── main.py          # FastAPI app + CORS + SSE endpoint
│   ├── agent.py         # Claude agentic loop (the brain)
│   ├── tools.py         # Real data fetchers (Places, Maps, SerpAPI)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── fun-planner-connected.jsx   # React UI with SSE streaming
└── README.md
```

---

## How the Agentic Loop Works

1. **User submits prompt** → FastAPI receives it
2. **Claude receives prompt + tool definitions** (search_restaurants, search_movies, search_places, get_travel_info)
3. **Claude reasons** and decides which tools to call (it may call 4-6 tools)
4. **Tools run in parallel** (asyncio.gather) → real data fetched
5. **Results fed back** to Claude as tool_result messages
6. **Claude synthesizes** all data into a structured JSON itinerary
7. **JSON streamed back** to frontend via Server-Sent Events

---

## Extending the App

**Add Swiggy/Zomato scraping:**
```python
# tools.py — add a new tool
async def search_zomato(area: str, max_budget: int) -> list[dict]:
    # Use Playwright to scrape zomato.com/hyderabad/...
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ...
```

**Add user location (GPS):**
```javascript
// frontend — get GPS coords
navigator.geolocation.getCurrentPosition(pos => {
  setLocation(`${pos.coords.latitude},${pos.coords.longitude}`);
});
```
Then pass to backend → use as `origins` in get_travel_info().

**Add memory / preferences:**
Store past plans in SQLite → feed user history to Claude system prompt
so it learns what the user likes over time.

---

## Cost Estimate

| Component | Cost |
|-----------|------|
| Claude API (per plan) | ~₹1.50 |
| Google Places (per search) | $0.032 |
| Google Maps (per route) | $0.005 |
| SerpAPI (per search) | Free up to 100/month |
| **Total per plan** | **~₹3-4** |

---

Built with Claude claude-sonnet-4, FastAPI, Google Places API, and React.

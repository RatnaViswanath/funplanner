"""
MENSPACE FunPlanner — FastAPI Backend
Agentic AI that autonomously searches restaurants, movies, places
and builds a personalized hourly itinerary using Claude tool use.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
from agent import run_planner_agent

app = FastAPI(title="FunPlanner API", version="1.0.0")

# ── CORS: allow your frontend origin ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    prompt: str
    location: str = "Hyderabad"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/plan")
async def create_plan(req: PlanRequest):
    """
    Main endpoint. Runs the Claude agentic loop and streams back:
      - agent_step  events (so the frontend can animate progress)
      - final_plan  event  (the structured itinerary JSON)
    """
    if not req.prompt.strip():
        raise HTTPException(400, "Prompt cannot be empty")

    async def event_stream():
        async for event in run_planner_agent(req.prompt, req.location):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

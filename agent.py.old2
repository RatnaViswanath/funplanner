"""
agent.py — The agentic loop.

Claude decides which tools to call, calls them (in parallel when possible),
feeds results back, and eventually outputs the final structured itinerary.

Streams events to the caller so the frontend can animate each step.
"""

import os
import json
import asyncio
from typing import AsyncGenerator
import anthropic
from tools import TOOL_DEFINITIONS, execute_tool

client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

SYSTEM_PROMPT = """You are an expert local activity planner for Hyderabad, India.
You have access to real-time tools to find restaurants, movies, places to visit, and travel info.

WORKFLOW:
1. Parse the user's prompt: extract budget, time window, preferences, start location
2. Call search_restaurants to find a good lunch/dinner option within budget
3. Call search_movies if entertainment/cinema is relevant 
4. Call search_places to find 1-2 attractions to visit
5. Call get_travel_info between key locations to estimate travel time and cost
6. Build a realistic hourly itinerary that fits within the time window and budget

BUDGET RULES:
- Total cost of all activities + food + travel MUST fit within the user's stated budget
- Be conservative: always leave ₹100-200 buffer for miscellaneous spending
- Ticket prices + restaurant cost + travel cost = check they sum below budget

OUTPUT FORMAT:
After all tool calls, respond ONLY with this exact JSON (no markdown, no extra text):
{
  "summary": "Brief 1-sentence plan overview",
  "totalEstimatedCost": 1500,
  "budgetBreakdown": {
    "food": 350,
    "entertainment": 700,
    "travel": 300,
    "entry_fees": 100,
    "misc": 50
  },
  "itinerary": [
    {
      "time": "12:00 PM",
      "title": "Lunch at Paradise Biryani",
      "category": "food",
      "location": "MG Road, Secunderabad",
      "cost": 320,
      "rating": 4.4,
      "description": "Legendary Hyderabadi dum biryani. Order the mutton biryani. Expect a 10-min wait.",
      "link": "https://maps.google.com/?q=Paradise+Biryani"
    },
    {
      "time": "1:30 PM",
      "title": "Travel to Hussain Sagar",
      "category": "travel",
      "location": "Secunderabad → Tank Bund Road",
      "cost": 80,
      "description": "Take Uber/Ola. ~15 min ride. Pre-book on app for best fare."
    }
  ],
  "tips": [
    "Book movie tickets on BookMyShow app 30 mins before to skip queues",
    "Use Hyderabad Metro where possible — cheaper and faster than cabs"
  ],
  "sources": {
    "restaurants": "Google Places API",
    "movies": "BookMyShow via search",
    "places": "Google Places API",
    "travel": "Google Maps Distance Matrix"
  }
}

Categories: "food", "movie", "place", "travel", "shopping", "entertainment"
Always include travel steps between locations with realistic Uber/Ola cost.
"""


# ─── Tool call label map (for frontend status display) ───────────────────────
TOOL_LABELS = {
    "search_restaurants": "🍽️  Searching Zomato & Google for restaurants...",
    "search_movies":       "🎬  Checking BookMyShow for current movies...",
    "search_places":       "📍  Finding places & attractions on JustDial / Google...",
    "get_travel_info":     "🚗  Calculating travel time & cab fares...",
}


async def run_planner_agent(
    user_prompt: str,
    location: str = "Hyderabad",
) -> AsyncGenerator[dict, None]:
    """
    Core agentic loop. Yields event dicts:
      {"type": "agent_step", "label": "..."}
      {"type": "tool_result", "tool": "...", "data": [...]}
      {"type": "final_plan", "plan": {...}}
      {"type": "error", "message": "..."}
    """
    messages = [{"role": "user", "content": user_prompt}]

    yield {"type": "agent_step", "label": "🧠  Parsing your request and deciding what to search..."}
    await asyncio.sleep(0.1)

    # ── Agentic loop: max 10 rounds to prevent infinite loops ─────────────────
    for round_num in range(10):
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # Append assistant message to history
        messages.append({"role": "assistant", "content": response.content})

        # ── If Claude is done (no more tool calls) ────────────────────────────
        if response.stop_reason == "end_turn":
            # Extract the JSON text block
            for block in response.content:
                if hasattr(block, "text"):
                    try:
                        plan = json.loads(block.text.strip())
                        yield {"type": "final_plan", "plan": plan}
                        return
                    except json.JSONDecodeError:
                        yield {"type": "error", "message": "Failed to parse plan JSON from Claude."}
                        return
            yield {"type": "error", "message": "No text response from Claude."}
            return

        # ── Process tool calls ─────────────────────────────────────────────────
        tool_calls = [b for b in response.content if b.type == "tool_use"]
        if not tool_calls:
            break

        # Stream a step event for each unique tool being called
        seen_tools = set()
        for tc in tool_calls:
            if tc.name not in seen_tools:
                label = TOOL_LABELS.get(tc.name, f"⚙️  Running {tc.name}...")
                yield {"type": "agent_step", "label": label}
                seen_tools.add(tc.name)

        # Execute all tool calls concurrently
        async def _run(tc):
            result_str = await execute_tool(tc.name, tc.input)
            return tc.id, tc.name, result_str

        tool_results_raw = await asyncio.gather(*[_run(tc) for tc in tool_calls])

        # Emit tool result data to frontend (for optional display)
        for tool_id, tool_name, result_str in tool_results_raw:
            try:
                yield {
                    "type":  "tool_result",
                    "tool":  tool_name,
                    "count": len(json.loads(result_str)) if result_str.startswith("[") else 1,
                }
            except Exception:
                pass

        # Feed tool results back to Claude
        tool_result_blocks = [
            {
                "type":        "tool_result",
                "tool_use_id": tool_id,
                "content":     result_str,
            }
            for tool_id, _, result_str in tool_results_raw
        ]
        messages.append({"role": "user", "content": tool_result_blocks})

    yield {"type": "agent_step", "label": "📅  Building your personalized hourly itinerary..."}
    await asyncio.sleep(0.3)

    yield {"type": "error", "message": "Agent loop exhausted without producing a plan."}

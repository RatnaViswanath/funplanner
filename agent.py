"""
agent.py — The agentic loop.

Claude decides which tools to call, calls them (in parallel when possible),
feeds results back, and eventually outputs the final structured itinerary.

Streams events to the caller so the frontend can animate each step.
"""

import os
import json
import re
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

PROXIMITY RULES — CRITICAL:
- Total travel time across the entire day MUST be under 25% of the available time window
  Example: 4-hour window → max 60 mins total travel. 6-hour window → max 90 mins total travel.
- ALWAYS pass user_lat and user_lng to search_restaurants and search_places tool calls
- Prefer places within 8-10 km of the user's starting location
- If the user is in north Hyderabad (Jeedimetla, Kompally, Medchal), suggest north-side venues
- If the user is in west Hyderabad (HITEC City, Kondapur, Gachibowli), suggest west-side venues
- If the user is in south Hyderabad (LB Nagar, Dilsukhnagar), suggest south-side venues
- NEVER recommend Golconda Fort, Charminar, or Hussain Sagar to a user who is 20+ km away unless they specifically ask
- Famous landmarks are NOT always the best choice — a good nearby park beats a far-away monument

OUTPUT FORMAT:
After all tool calls, respond ONLY with this exact JSON (no markdown, no extra text).
Generate exactly 3 DIFFERENT plan options. Each plan should have a distinct angle:
- Plan 1: "Budget Smart" — maximise fun, minimise spend, use free/low-cost venues
- Plan 2: "Best Experience" — best-rated venues, premium experience within budget  
- Plan 3: "Relaxed & Easy" — fewest travel hops, low stress, close to home

{
  "plans": [
    {
      "planId": 1,
      "planTitle": "Budget Smart",
      "planEmoji": "💰",
      "planTagline": "Maximum fun, minimum spend",
      "summary": "Brief 1-sentence plan overview",
      "totalEstimatedCost": 1200,
      "budgetBreakdown": {
        "food": 300,
        "entertainment": 500,
        "travel": 250,
        "entry_fees": 100,
        "misc": 50
      },
      "itinerary": [
        {
          "time": "12:00 PM",
          "title": "Lunch at Local Dhaba",
          "category": "food",
          "location": "Near User Location",
          "cost": 200,
          "rating": 4.2,
          "description": "Great value South Indian thali. Family-friendly.",
          "link": "https://maps.google.com/?q=restaurant"
        },
        {
          "time": "1:30 PM",
          "title": "Travel to Park",
          "category": "travel",
          "location": "Home → Nearby Park",
          "cost": 80,
          "description": "Take Uber/Ola. ~15 min ride.",
          "pickup_coords": { "lat": 17.4399, "lng": 78.4983 },
          "dropoff_coords": { "lat": 17.4239, "lng": 78.4738 },
          "dropoff_name": "Destination Park",
          "estimated_fare": "₹80-100"
        }
      ],
      "tips": ["Tip 1", "Tip 2"],
      "sources": {
        "restaurants": "Google Places API",
        "movies": "BookMyShow via search",
        "places": "Google Places API",
        "travel": "Google Maps Distance Matrix"
      }
    },
    {
      "planId": 2,
      "planTitle": "Best Experience",
      "planEmoji": "⭐",
      "planTagline": "Top-rated venues, premium day out",
      "summary": "...",
      "totalEstimatedCost": 2200,
      "budgetBreakdown": { "food": 600, "entertainment": 800, "travel": 500, "entry_fees": 200, "misc": 100 },
      "itinerary": [],
      "tips": [],
      "sources": {}
    },
    {
      "planId": 3,
      "planTitle": "Relaxed & Easy",
      "planEmoji": "😌",
      "planTagline": "Stress-free, close to home",
      "summary": "...",
      "totalEstimatedCost": 1500,
      "budgetBreakdown": { "food": 400, "entertainment": 600, "travel": 300, "entry_fees": 150, "misc": 50 },
      "itinerary": [],
      "tips": [],
      "sources": {}
    }
  ]
}

IMPORTANT: All 3 plans must be FULLY detailed with complete itinerary arrays — not empty like the examples above.
Each plan must use DIFFERENT venues, restaurants, and activities from each other.
Categories: "food", "movie", "place", "travel", "shopping", "entertainment"
Always include travel steps between locations with realistic Uber/Ola cost.
For ALL travel steps, always include pickup_coords, dropoff_coords (lat/lng), dropoff_name, and estimated_fare so users can deep-link directly into Uber/Ola apps.
For ALL movie steps, always include movie_title (the exact film name, not the venue) so users can search it directly on BookMyShow.
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
    user_coords: dict | None = None,
) -> AsyncGenerator[dict, None]:
    """
    Core agentic loop. Yields event dicts:
      {"type": "agent_step", "label": "..."}
      {"type": "tool_result", "tool": "...", "data": [...]}
      {"type": "final_plan", "plan": {...}}
      {"type": "error", "message": "..."}
    """
    # Inject user location explicitly at the top of the message
    location_context = ""
    if user_coords:
        location_context = (
            f"\n\n[SYSTEM NOTE: The user's EXACT current GPS location is {location} "
            f"(coordinates: lat={user_coords['lat']:.4f}, lng={user_coords['lng']:.4f}). "
            f"MANDATORY INSTRUCTIONS:\n"
            f"1. Start the itinerary from this location.\n"
            f"2. When calling search_restaurants, pass user_lat={user_coords['lat']:.4f} and user_lng={user_coords['lng']:.4f}.\n"
            f"3. When calling search_places, pass user_lat={user_coords['lat']:.4f} and user_lng={user_coords['lng']:.4f}.\n"
            f"4. Only suggest places within 10km of this location unless the user explicitly asks for far destinations.\n"
            f"5. Use these coordinates as pickup_coords for the first travel step.]\n\n"
        )
    elif location and location != "Hyderabad":
        location_context = (
            f"\n\n[SYSTEM NOTE: The user's starting location is {location}. "
            f"Begin the itinerary from this area and prefer nearby venues.]\n\n"
        )

    augmented_prompt = location_context + user_prompt
    messages = [{"role": "user", "content": augmented_prompt}]

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
                        raw = block.text.strip()
                        # Strip markdown code fences if Claude wrapped the JSON
                        if raw.startswith("```"):
                            raw = re.sub(r"^```(?:json)?\s*", "", raw)
                            raw = re.sub(r"\s*```$", "", raw.strip())
                        parsed = json.loads(raw)
                        # Support both multi-plan {"plans": [...]} and legacy single plan
                        if "plans" in parsed:
                            yield {"type": "final_plans", "plans": parsed["plans"]}
                        else:
                            # Wrap legacy single plan in plans array for backwards compat
                            yield {"type": "final_plans", "plans": [{"planId": 1, "planTitle": "Your Plan", "planEmoji": "✨", "planTagline": "", **parsed}]}
                        return
                    except json.JSONDecodeError as e:
                        yield {"type": "error", "message": f"Failed to parse plan JSON: {str(e)[:120]}. Raw: {block.text[:300]}"}
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

import { useState, useRef, useEffect } from "react";

// ── Change this to your deployed backend URL ──────────────────────────────
const API_BASE = "http://localhost:8000";

const SAMPLE_PROMPTS = [
  "Bored on a weekday, want to spend 4-6 hours in Hyderabad within ₹2000. Like biryani.",
  "Fun Sunday with family, ₹3000 budget, 10am to 6pm, kids enjoy outdoor places.",
  "Solo evening out tonight in Hyderabad, ₹800, 5pm to 10pm. I like action movies.",
  "Couple's day out, ₹4000, full day, want good food and a historical place.",
];

const STEP_ICONS = {
  "🧠": "#a78bfa",
  "🍽️": "#fb923c",
  "🎬": "#c084fc",
  "📍": "#34d399",
  "🚗": "#60a5fa",
  "📅": "#fbbf24",
};

function AgentStep({ label, isActive, isDone, index }) {
  const emoji = label.split("  ")[0];
  const text  = label.split("  ").slice(1).join("  ");
  const color = STEP_ICONS[emoji] || "#fbbf24";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "10px 14px",
        borderRadius: "10px",
        background: isDone
          ? "rgba(34,197,94,0.07)"
          : isActive
          ? `${color}18`
          : "rgba(255,255,255,0.02)",
        border: `1px solid ${
          isDone ? "rgba(34,197,94,0.25)" : isActive ? `${color}50` : "rgba(255,255,255,0.06)"
        }`,
        transition: "all 0.35s ease",
        opacity: !isActive && !isDone ? 0.35 : 1,
        animation: isActive ? "none" : isDone ? "none" : "none",
      }}
    >
      <span style={{ fontSize: "18px", lineHeight: 1 }}>{emoji}</span>
      <span
        style={{
          fontSize: "13px",
          fontFamily: "'DM Mono', monospace",
          color: isDone ? "#86efac" : isActive ? color : "#64748b",
          flex: 1,
        }}
      >
        {text}
      </span>
      {isActive && (
        <div
          style={{
            width: "14px",
            height: "14px",
            border: `2px solid ${color}`,
            borderTop: "2px solid transparent",
            borderRadius: "50%",
            animation: "spin 0.7s linear infinite",
            flexShrink: 0,
          }}
        />
      )}
      {isDone && <span style={{ color: "#86efac", fontSize: "13px" }}>✓</span>}
    </div>
  );
}

function TimelineCard({ item, index }) {
  const cats = {
    food:          { color: "#fb923c", icon: "🍽️" },
    movie:         { color: "#c084fc", icon: "🎬" },
    place:         { color: "#34d399", icon: "📍" },
    travel:        { color: "#64748b", icon: "🚗" },
    shopping:      { color: "#38bdf8", icon: "🛍️" },
    entertainment: { color: "#f472b6", icon: "🎉" },
  };
  const c = cats[item.category] || cats.food;

  return (
    <div
      style={{
        display: "flex",
        gap: "14px",
        animation: `slideUp 0.4s ease ${index * 0.08}s both`,
      }}
    >
      {/* Timeline spine */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: "38px" }}>
        <div
          style={{
            width: "38px",
            height: "38px",
            borderRadius: "50%",
            background: `${c.color}18`,
            border: `2px solid ${c.color}60`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "16px",
            flexShrink: 0,
          }}
        >
          {c.icon}
        </div>
        <div style={{ width: "2px", flex: 1, background: "rgba(255,255,255,0.05)", marginTop: "4px", minHeight: "16px" }} />
      </div>

      {/* Card body */}
      <div
        style={{
          flex: 1,
          background: "rgba(255,255,255,0.025)",
          border: `1px solid ${c.color}25`,
          borderRadius: "12px",
          padding: "14px 16px",
          marginBottom: "10px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "5px", flexWrap: "wrap", gap: "6px" }}>
          <span style={{ fontSize: "12px", color: c.color, fontFamily: "'DM Mono', monospace", fontWeight: 600 }}>
            {item.time}
          </span>
          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            {item.rating && (
              <span style={{ fontSize: "12px", color: "#fbbf24", fontFamily: "'DM Mono', monospace" }}>
                ★ {typeof item.rating === "number" ? item.rating.toFixed(1) : item.rating}
              </span>
            )}
            {item.cost > 0 && (
              <span
                style={{
                  fontSize: "11px",
                  background: "rgba(251,191,36,0.1)",
                  border: "1px solid rgba(251,191,36,0.25)",
                  color: "#fbbf24",
                  padding: "2px 8px",
                  borderRadius: "20px",
                  fontFamily: "'DM Mono', monospace",
                }}
              >
                ₹{item.cost}
              </span>
            )}
          </div>
        </div>

        <div style={{ fontSize: "15px", fontWeight: 700, color: "#f1f5f9", marginBottom: "4px", fontFamily: "'Syne', sans-serif" }}>
          {item.title}
        </div>

        {item.location && (
          <div style={{ fontSize: "12px", color: "#475569", marginBottom: "6px", display: "flex", alignItems: "center", gap: "4px" }}>
            📌 {item.location}
          </div>
        )}

        {item.description && (
          <div style={{ fontSize: "13px", color: "#94a3b8", lineHeight: 1.55 }}>
            {item.description}
          </div>
        )}

        {item.link && item.category !== "travel" && (
          <a
            href={item.link}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "inline-block",
              marginTop: "8px",
              fontSize: "12px",
              color: c.color,
              textDecoration: "none",
              border: `1px solid ${c.color}40`,
              padding: "3px 10px",
              borderRadius: "6px",
            }}
          >
            Open ↗
          </a>
        )}

        {/* Uber/Ola deep link buttons for travel cards */}
        {item.category === "travel" && item.pickup_coords && item.dropoff_coords && (
          <div style={{ display: "flex", gap: "8px", marginTop: "10px", flexWrap: "wrap" }}>
            <a
              href={`https://m.uber.com/ul/?action=setPickup&pickup[latitude]=${item.pickup_coords.lat}&pickup[longitude]=${item.pickup_coords.lng}&dropoff[latitude]=${item.dropoff_coords.lat}&dropoff[longitude]=${item.dropoff_coords.lng}&dropoff[nickname]=${encodeURIComponent(item.dropoff_name || "Destination")}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                fontSize: "12px",
                fontWeight: 600,
                color: "#000",
                background: "#fff",
                textDecoration: "none",
                padding: "5px 12px",
                borderRadius: "8px",
                fontFamily: "'DM Sans', sans-serif",
              }}
            >
              <span style={{ fontSize: "14px" }}>⚫</span> Uber
            </a>
            <a
              href={`https://book.olacabs.com/?pickup_lat=${item.pickup_coords.lat}&pickup_lng=${item.pickup_coords.lng}&drop_lat=${item.dropoff_coords.lat}&drop_lng=${item.dropoff_coords.lng}&drop_name=${encodeURIComponent(item.dropoff_name || "Destination")}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                fontSize: "12px",
                fontWeight: 600,
                color: "#fff",
                background: "#10b981",
                textDecoration: "none",
                padding: "5px 12px",
                borderRadius: "8px",
                fontFamily: "'DM Sans', sans-serif",
              }}
            >
              <span style={{ fontSize: "14px" }}>🟡</span> Ola
            </a>
            {item.estimated_fare && (
              <span style={{
                fontSize: "11px",
                color: "#64748b",
                alignSelf: "center",
                fontFamily: "'DM Mono', monospace",
              }}>
                est. {item.estimated_fare}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function FunPlanner() {
  const [prompt, setPrompt]           = useState("");
  const [isLoading, setIsLoading]     = useState(false);
  const [steps, setSteps]             = useState([]);
  const [result, setResult]           = useState(null);
  const [error, setError]             = useState(null);
  const resultRef                     = useRef(null);

  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = `
      @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');
      @keyframes spin    { to { transform: rotate(360deg); } }
      @keyframes slideUp { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
      @keyframes fadeIn  { from { opacity:0; } to { opacity:1; } }
      @keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
      * { box-sizing: border-box; }
      textarea { resize: none; }
      ::-webkit-scrollbar { width: 4px; }
      ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 2px; }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  // Scroll to results
  useEffect(() => {
    if (result && resultRef.current) {
      setTimeout(() => resultRef.current.scrollIntoView({ behavior: "smooth", block: "start" }), 200);
    }
  }, [result]);

  const handleSubmit = async () => {
    if (!prompt.trim() || isLoading) return;
    setIsLoading(true);
    setResult(null);
    setError(null);
    setSteps([]);

    try {
      const response = await fetch(`${API_BASE}/plan`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ prompt, location: "Hyderabad" }),
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const reader  = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer    = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();                // keep incomplete line

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (raw === "[DONE]") break;

          try {
            const event = JSON.parse(raw);

            if (event.type === "agent_step") {
              setSteps(prev => {
                // Don't duplicate
                if (prev.some(s => s.label === event.label)) return prev;
                return [...prev, { label: event.label, done: false }];
              });
              // Mark previous steps done
              setSteps(prev =>
                prev.map((s, i) => i < prev.length - 1 ? { ...s, done: true } : s)
              );
            }

            if (event.type === "tool_result") {
              // Mark last step done when tool result arrives
              setSteps(prev => prev.map(s => ({ ...s, done: true })));
            }

            if (event.type === "final_plan") {
              setSteps(prev => prev.map(s => ({ ...s, done: true })));
              setResult(event.plan);
            }

            if (event.type === "error") {
              setError(event.message);
            }
          } catch (_) {}
        }
      }
    } catch (err) {
      setError(`Could not connect to backend. Make sure it's running at ${API_BASE}. Error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const budgetColors = {
    food:          "#fb923c",
    entertainment: "#c084fc",
    travel:        "#60a5fa",
    entry_fees:    "#34d399",
    misc:          "#64748b",
  };

  return (
    <div style={{ minHeight: "100vh", background: "#070b12", color: "#f1f5f9", fontFamily: "'DM Sans', sans-serif" }}>
      {/* Ambient background */}
      <div style={{
        position: "fixed", inset: 0, pointerEvents: "none",
        background: `
          radial-gradient(ellipse 80% 40% at 15% 5%,  rgba(251,191,36,0.07) 0%, transparent 55%),
          radial-gradient(ellipse 50% 40% at 85% 85%, rgba(6,182,212,0.05) 0%, transparent 55%),
          radial-gradient(ellipse 40% 30% at 50% 50%, rgba(168,85,247,0.03) 0%, transparent 60%)
        `,
      }}/>

      <div style={{ maxWidth: "720px", margin: "0 auto", padding: "40px 20px 80px", position: "relative" }}>

        {/* ── HEADER ── */}
        <div style={{ textAlign: "center", marginBottom: "44px" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: "8px",
            fontSize: "11px", letterSpacing: "3px", textTransform: "uppercase",
            color: "#fbbf24", fontFamily: "'DM Mono', monospace",
            padding: "6px 14px", border: "1px solid rgba(251,191,36,0.25)",
            borderRadius: "4px", background: "rgba(251,191,36,0.06)", marginBottom: "18px",
          }}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#22c55e", animation: "fadeIn 1s ease infinite alternate" }}/>
            Agentic AI · Live Data · Hyderabad
          </div>
          <h1 style={{
            fontFamily: "'Syne', sans-serif",
            fontSize: "clamp(34px, 6vw, 54px)",
            fontWeight: 800, lineHeight: 1.1, marginBottom: "14px",
            background: "linear-gradient(135deg, #f8fafc 10%, #fbbf24 55%, #f97316 100%)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
          }}>
            What's the Plan?
          </h1>
          <p style={{ color: "#64748b", fontSize: "14px", maxWidth: "400px", margin: "0 auto", lineHeight: 1.65 }}>
            Tell me your free time & budget. I'll search <strong style={{ color: "#94a3b8" }}>Google Places</strong>,
            <strong style={{ color: "#94a3b8" }}> BookMyShow</strong>, and <strong style={{ color: "#94a3b8" }}>Maps</strong>
            — then build your perfect day.
          </p>
        </div>

        {/* ── INPUT CARD ── */}
        <div style={{
          background: "rgba(255,255,255,0.025)",
          border: "1px solid rgba(255,255,255,0.09)",
          borderRadius: "18px", padding: "22px", marginBottom: "20px",
        }}>
          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder={"e.g. I'm bored on a weekday afternoon, want to spend 4-6 hours in Hyderabad within ₹2000. I like biryani and action movies."}
            rows={3}
            style={{
              width: "100%", background: "transparent", border: "none", outline: "none",
              color: "#f1f5f9", fontSize: "15px", fontFamily: "'DM Sans', sans-serif",
              lineHeight: 1.65, marginBottom: "16px",
            }}
            onKeyDown={e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit(); }}
          />

          {/* Sample prompts */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "7px", marginBottom: "18px" }}>
            {SAMPLE_PROMPTS.map((p, i) => (
              <button
                key={i}
                onClick={() => setPrompt(p)}
                style={{
                  background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: "6px", color: "#64748b", fontSize: "11px",
                  padding: "5px 10px", cursor: "pointer", fontFamily: "'DM Sans', sans-serif",
                  transition: "all 0.2s",
                }}
                onMouseEnter={e => { e.target.style.color = "#fbbf24"; e.target.style.borderColor = "rgba(251,191,36,0.35)"; }}
                onMouseLeave={e => { e.target.style.color = "#64748b"; e.target.style.borderColor = "rgba(255,255,255,0.08)"; }}
              >
                {p.slice(0, 38)}…
              </button>
            ))}
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "11px", color: "#2d3748", fontFamily: "'DM Mono', monospace" }}>⌘ Enter to plan</span>
            <button
              onClick={handleSubmit}
              disabled={!prompt.trim() || isLoading}
              style={{
                background: prompt.trim() && !isLoading
                  ? "linear-gradient(135deg, #fbbf24 0%, #f97316 100%)"
                  : "rgba(255,255,255,0.04)",
                border: "none", borderRadius: "10px",
                color: prompt.trim() && !isLoading ? "#07080c" : "#2d3748",
                fontSize: "14px", fontWeight: 700, fontFamily: "'Syne', sans-serif",
                padding: "12px 30px", cursor: prompt.trim() && !isLoading ? "pointer" : "not-allowed",
                transition: "all 0.2s", letterSpacing: "0.3px",
              }}
            >
              {isLoading ? "Agent Working…" : "Build My Day →"}
            </button>
          </div>
        </div>

        {/* ── AGENT STEPS PANEL ── */}
        {(isLoading || steps.length > 0) && !result && (
          <div style={{
            background: "rgba(255,255,255,0.018)",
            border: "1px solid rgba(255,255,255,0.07)",
            borderRadius: "14px", padding: "20px",
            marginBottom: "24px", display: "flex", flexDirection: "column", gap: "8px",
          }}>
            <div style={{ fontSize: "10px", letterSpacing: "2.5px", textTransform: "uppercase", color: "#334155", fontFamily: "'DM Mono', monospace", marginBottom: "8px" }}>
              Agent Trace
            </div>
            {steps.map((step, i) => (
              <AgentStep
                key={i}
                label={step.label}
                isActive={i === steps.length - 1 && isLoading}
                isDone={step.done && !(i === steps.length - 1 && isLoading)}
                index={i}
              />
            ))}
          </div>
        )}

        {/* ── ERROR ── */}
        {error && (
          <div style={{
            background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.25)",
            borderRadius: "12px", padding: "16px 18px",
            color: "#fca5a5", marginBottom: "24px", fontSize: "13px", lineHeight: 1.6,
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* ── RESULTS ── */}
        {result && (
          <div ref={resultRef} style={{ animation: "slideUp 0.5s ease" }}>

            {/* Summary + Budget header */}
            <div style={{
              background: "linear-gradient(135deg, rgba(251,191,36,0.07), rgba(249,115,22,0.07))",
              border: "1px solid rgba(251,191,36,0.18)",
              borderRadius: "16px", padding: "22px", marginBottom: "28px",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
                <div>
                  <div style={{ fontSize: "10px", letterSpacing: "2.5px", textTransform: "uppercase", color: "#fbbf24", fontFamily: "'DM Mono', monospace", marginBottom: "8px" }}>
                    Your Plan is Ready
                  </div>
                  <div style={{ fontSize: "15px", color: "#cbd5e1", lineHeight: 1.6, maxWidth: "460px" }}>
                    {result.summary}
                  </div>
                </div>
                <div style={{ textAlign: "right", flexShrink: 0 }}>
                  <div style={{ fontSize: "10px", color: "#475569", marginBottom: "4px", fontFamily: "'DM Mono', monospace" }}>TOTAL</div>
                  <div style={{ fontSize: "32px", fontWeight: 800, fontFamily: "'Syne', sans-serif", color: "#fbbf24", lineHeight: 1 }}>
                    ₹{result.totalEstimatedCost}
                  </div>
                </div>
              </div>

              {/* Budget breakdown pills */}
              {result.budgetBreakdown && (
                <div style={{ marginTop: "18px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  {Object.entries(result.budgetBreakdown).map(([k, v]) => (
                    <div key={k} style={{
                      fontSize: "12px", fontFamily: "'DM Mono', monospace",
                      padding: "4px 12px", borderRadius: "20px",
                      color: budgetColors[k] || "#94a3b8",
                      background: `${budgetColors[k] || "#94a3b8"}12`,
                      border: `1px solid ${budgetColors[k] || "#94a3b8"}30`,
                    }}>
                      {k} ₹{v}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Itinerary timeline */}
            <div style={{ fontSize: "10px", letterSpacing: "2.5px", textTransform: "uppercase", color: "#334155", fontFamily: "'DM Mono', monospace", marginBottom: "18px" }}>
              Hourly Itinerary
            </div>

            {result.itinerary?.map((item, i) => (
              <TimelineCard key={i} item={item} index={i} />
            ))}

            {/* Tips */}
            {result.tips?.length > 0 && (
              <div style={{
                marginTop: "22px",
                background: "rgba(6,182,212,0.05)", border: "1px solid rgba(6,182,212,0.18)",
                borderRadius: "12px", padding: "18px 20px",
              }}>
                <div style={{ fontSize: "10px", letterSpacing: "2.5px", textTransform: "uppercase", color: "#06b6d4", fontFamily: "'DM Mono', monospace", marginBottom: "10px" }}>
                  Insider Tips
                </div>
                {result.tips.map((tip, i) => (
                  <div key={i} style={{ fontSize: "13px", color: "#94a3b8", marginBottom: "7px", display: "flex", gap: "8px", lineHeight: 1.5 }}>
                    <span style={{ color: "#06b6d4", flexShrink: 0 }}>→</span> {tip}
                  </div>
                ))}
              </div>
            )}

            {/* Data sources */}
            {result.sources && (
              <div style={{ marginTop: "16px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {Object.entries(result.sources).map(([k, v]) => (
                  <div key={k} style={{
                    fontSize: "11px", color: "#334155", fontFamily: "'DM Mono', monospace",
                    padding: "3px 10px", borderRadius: "4px",
                    background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)",
                  }}>
                    {k}: {v}
                  </div>
                ))}
              </div>
            )}

            {/* Re-plan */}
            <div style={{ textAlign: "center", marginTop: "36px" }}>
              <button
                onClick={() => { setResult(null); setSteps([]); setPrompt(""); window.scrollTo({ top: 0, behavior: "smooth" }); }}
                style={{
                  background: "transparent", border: "1px solid rgba(255,255,255,0.09)",
                  borderRadius: "8px", color: "#475569", padding: "10px 26px",
                  fontSize: "13px", cursor: "pointer", fontFamily: "'DM Sans', sans-serif",
                }}
              >
                ↺ Plan Another Day
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
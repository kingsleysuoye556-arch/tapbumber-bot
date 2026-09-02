"use client";

import { useState } from "react";

export default function HorticultureDesigner() {
  const [request, setRequest] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleDesign() {
    if (!request.trim() || loading) return;

    setLoading(true);
    setResult("");

    try {
      const response = await fetch("/api/horticulture", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ request: request.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Something went wrong.");
      }

      setResult(data.result || "No design result was received.");
    } catch (error) {
      setResult(
        error instanceof Error ? error.message : "Unable to create design."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#050505",
        color: "#fff",
        padding: "32px 16px",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif',
      }}
    >
      <div
        style={{
          maxWidth: 800,
          margin: "0 auto",
        }}
      >
        <header
          style={{
            textAlign: "center",
            marginBottom: 32,
          }}
        >
          <div
            style={{
              fontSize: 48,
              marginBottom: 10,
            }}
          >
            🌺
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: 30,
              fontWeight: 800,
            }}
          >
            <span style={{ color: "#FFD43B" }}>Horticulture</span> Designer
          </h1>

          <p
            style={{
              marginTop: 10,
              color: "#fff",
              opacity: 0.7,
              lineHeight: 1.6,
            }}
          >
            Design beautiful flower and plant landscapes for houses, buildings,
            gardens, and outdoor spaces.
          </p>
        </header>

        <section
          style={{
            background: "#0D0D0D",
            border: "1px solid rgba(255,255,255,0.09)",
            borderRadius: 20,
            padding: 20,
          }}
        >
          <label
            htmlFor="horticulture-request"
            style={{
              display: "block",
              marginBottom: 10,
              fontWeight: 700,
            }}
          >
            What would you like to{" "}
            <span style={{ color: "#FFD43B" }}>design?</span>
          </label>

          <textarea
            id="horticulture-request"
            value={request}
            onChange={(event) => setRequest(event.target.value)}
            placeholder="Example: Design a beautiful modern house with Royal Palms, flowering plants and decorative trees around the entrance and walkway."
            style={{
              width: "100%",
              minHeight: 150,
              boxSizing: "border-box",
              resize: "vertical",
              borderRadius: 14,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "#101010",
              color: "#fff",
              padding: 16,
              fontSize: 15,
              lineHeight: 1.5,
              outline: "none",
            }}
          />

          <button
            type="button"
            onClick={handleDesign}
            disabled={loading || !request.trim()}
            style={{
              marginTop: 16,
              width: "100%",
              padding: "14px 18px",
              borderRadius: 14,
              border: "1px solid rgba(255,212,59,0.25)",
              background: loading || !request.trim() ? "#171717" : "#FFD43B",
              color: loading || !request.trim() ? "#777" : "#050505",
              fontWeight: 800,
              fontSize: 15,
              cursor: loading || !request.trim() ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Creating Design..." : "Create Horticulture Design 🌿"}
          </button>
        </section>

        {result && (
          <section
            style={{
              marginTop: 20,
              background: "#0D0D0D",
              border: "1px solid rgba(255,255,255,0.09)",
              borderRadius: 20,
              padding: 20,
            }}
          >
            <h2
              style={{
                margin: "0 0 14px",
                fontSize: 21,
                fontWeight: 800,
              }}
            >
              Your <span style={{ color: "#FFD43B" }}>Horticulture Plan</span>{" "}
              🌱
            </h2>

            <div
              style={{
                whiteSpace: "pre-wrap",
                lineHeight: 1.7,
                opacity: 0.85,
                fontSize: 15,
              }}
            >
              {result}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
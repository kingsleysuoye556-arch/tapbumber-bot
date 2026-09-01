"use client";

import { useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  async function askAI(e) {
    e.preventDefault();

    if (!message.trim()) return;

    setLoading(true);
    setResponse("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message.trim(),
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Something went wrong.");
      }

      setResponse(data.response);
    } catch (error) {
      setResponse(error.message || "Unable to connect to TapBumber AI.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#080812",
        color: "white",
        fontFamily: "Arial, Helvetica, sans-serif",
        padding: "30px 20px",
      }}
    >
      <div
        style={{
          maxWidth: "800px",
          margin: "0 auto",
          textAlign: "center",
        }}
      >
        <div
          style={{
            display: "inline-block",
            padding: "9px 15px",
            borderRadius: "50px",
            background: "rgba(108,76,255,0.15)",
            border: "1px solid rgba(139,108,255,0.35)",
            color: "#b9aaff",
            marginBottom: "25px",
          }}
        >
          ✨ AI-Powered Business Platform
        </div>

        <h1
          style={{
            fontSize: "clamp(44px, 9vw, 82px)",
            lineHeight: "0.98",
            marginBottom: "25px",
          }}
        >
          Automate.
          <br />
          <span style={{ color: "#9b7cff" }}>Grow. Earn.</span>
        </h1>

        <p
          style={{
            color: "#b7b7c8",
            fontSize: "18px",
            lineHeight: "1.7",
          }}
        >
          TapBumber AI helps you create, automate and grow your digital
          business with powerful artificial intelligence tools.
        </p>

        <form
          onSubmit={askAI}
          style={{
            marginTop: "40px",
            display: "flex",
            flexDirection: "column",
            gap: "14px",
          }}
        >
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask TapBumber AI anything..."
            rows={5}
            style={{
              width: "100%",
              padding: "16px",
              borderRadius: "14px",
              border: "1px solid rgba(255,255,255,0.15)",
              background: "#11111d",
              color: "white",
              fontSize: "16px",
              outline: "none",
              resize: "vertical",
            }}
          />

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: "16px 25px",
              border: "none",
              borderRadius: "12px",
              background: loading ? "#51408f" : "#7657ff",
              color: "white",
              fontSize: "16px",
              fontWeight: "700",
              cursor: loading ? "wait" : "pointer",
            }}
          >
            {loading ? "🤖 TapBumber AI is thinking..." : "✨ Ask TapBumber AI"}
          </button>
        </form>

        {response && (
          <div
            style={{
              marginTop: "25px",
              padding: "22px",
              borderRadius: "16px",
              background: "#11111d",
              border: "1px solid rgba(139,108,255,0.25)",
              textAlign: "left",
              lineHeight: "1.7",
              whiteSpace: "pre-wrap",
            }}
          >
            <strong>🤖 TapBumber AI</strong>
            <p style={{ marginTop: "10px", color: "#d0d0df" }}>
              {response}
            </p>
          </div>
        )}

        <p
          style={{
            marginTop: "60px",
            color: "#777789",
            fontSize: "14px",
          }}
        >
          © 2026 TapBumber AI. All rights reserved.
        </p>
      </div>
    </main>
  );
}
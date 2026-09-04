"use client";

import { useState, useRef, useEffect } from "react";

export default function Home() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I'm Top Bomba AI — your practical business assistant. Ask me anything about business, growth, or earning online.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setMessage("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
      });
      const data = await res.json();

      if (!res.ok) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.error || "Something went wrong. Please try again." },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.reply || data.response || "No response received." },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Failed to reach the server. Please check your connection." },
      ]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  function startContentCreator() {
    setMessage(
      "Help me create professional content for my business. Ask me what type of content I want and what my business is about."
    );
    setTimeout(() => textareaRef.current?.focus(), 100);
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#000",
        color: "#ffffff",
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif',
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* HEADER WITH NEW LOGO */}
      <header
        style={{
          padding: "20px",
          borderBottom: "1px solid rgba(255,212,59,0.2)",
          background: "rgba(0,0,0,0.95)",
          backdropFilter: "blur(12px)",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <div style={{ maxWidth: 800, margin: "0 auto", display: "flex", justifyContent: "center" }}>
          <img
            src="/logo.png"
            alt="Top Bomba AI Logo"
            style={{
              height: 70,
              width: "auto",
              objectFit: "contain",
              filter: "drop-shadow(0 0 15px rgba(255,212,59,0.4))",
            }}
          />
        </div>
      </header>

      <main
        style={{
          flex: 1,
          maxWidth: 800,
          width: "100%",
          margin: "0 auto",
          padding: "24px 16px",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        {/* CONTENT CREATOR CARD */}
        <div
          style={{
            padding: "18px",
            borderRadius: 18,
            background: "#0A0A0A",
            border: "1px solid rgba(255,212,59,0.25)",
            boxShadow: "0 8px 30px rgba(255,212,59,0.1)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 12,
                background: "#111",
                border: "1px solid rgba(255,212,59,0.4)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 18,
              }}
            >
              ✨
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>
                AI <span style={{ color: "#FFD43B" }}>Content</span> Creator
              </h2>
              <p style={{ margin: "3px 0 0", fontSize: 12, opacity: 0.7 }}>
                Create content for your business
              </p>
            </div>
          </div>

          <p style={{ margin: "12px 0", opacity: 0.85, fontSize: 14, lineHeight: 1.6 }}>
            Create social media posts, captions, advertisements, product descriptions, and promotional messages.
          </p>

          <button
            type="button"
            onClick={startContentCreator}
            disabled={loading}
            style={{
              width: "100%",
              padding: "13px 18px",
              borderRadius: 12,
              border: "none",
              background: loading ? "#222" : "linear-gradient(135deg, #FFD43B 0%, #FFA500 100%)",
              color: loading ? "#888" : "#000",
              fontWeight: 800,
              fontSize: 15,
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: loading ? "none" : "0 0 25px rgba(255,212,59,0.4)",
            }}
          >
            {loading ? "Please wait..." : "Create Content ✨"}
          </button>
        </div>

        {/* CHAT MESSAGES */}
        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
            <div
              style={{
                maxWidth: "85%",
                padding: "12px 16px",
                borderRadius: 16,
                background: msg.role === "user" ? "#151515" : "#0A0A0A",
                border: msg.role === "user" ? "1px solid rgba(255,212,59,0.3)" : "1px solid rgba(255,212,59,0.15)",
                whiteSpace: "pre-wrap",
                lineHeight: 1.6,
                fontSize: 15,
              }}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: "flex", justifyContent: "flex-start" }}>
            <div style={{ padding: "12px 16px", borderRadius: 16, background: "#0A0A0A", border: "1px solid rgba(255,212,59,0.15)", color: "#FFD43B" }}>
              Thinking...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* INPUT */}
      <div
        style={{
          padding: "16px",
          borderTop: "1px solid rgba(255,212,59,0.2)",
          background: "rgba(0,0,0,0.97)",
          backdropFilter: "blur(12px)",
        }}
      >
        <form
          onSubmit={handleSubmit}
          style={{ maxWidth: 800, margin: "0 auto", display: "flex", gap: 10, alignItems: "flex-end" }}
        >
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Top Bomba AI anything..."
            rows={1}
            disabled={loading}
            style={{
              flex: 1,
              resize: "none",
              padding: "14px 16px",
              borderRadius: 14,
              border: "1px solid rgba(255,212,59,0.3)",
              background: "#0F0F0F",
              color: "#ffffff",
              fontSize: 15,
              outline: "none",
              minHeight: 48,
              maxHeight: 120,
              caretColor: "#FFD43B",
            }}
          />
          <button
            type="submit"
            disabled={loading || !message.trim()}
            style={{
              padding: "14px 20px",
              borderRadius: 14,
              border: "none",
              background: loading || !message.trim() ? "#222" : "linear-gradient(135deg, #FFD43B 0%, #FFA500 100%)",
              color: loading || !message.trim() ? "#777" : "#000",
              fontWeight: 800,
              fontSize: 15,
              cursor: loading || !message.trim() ? "not-allowed" : "pointer",
              boxShadow: loading || !message.trim() ? "none" : "0 0 20px rgba(255,212,59,0.3)",
            }}
          >
            {loading ? "..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}
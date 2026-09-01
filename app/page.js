"use client";

import { useState, useRef, useEffect } from "react";

export default function Home() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I'm TapBomba AI — your practical business assistant. Ask me anything about business, growth, or earning online.",
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

    const userMessage = { role: "user", content: trimmed };

    setMessages((prev) => [...prev, userMessage]);
    setMessage("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: trimmed,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              data.error || "Something went wrong. Please try again.",
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              data.reply || data.response || "No response received.",
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Failed to reach the server. Please check your connection.",
        },
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

    setTimeout(() => {
      textareaRef.current?.focus();
    }, 100);
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "linear-gradient(160deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)",
        color: "#e2e8f0",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: "16px 24px",
          borderBottom: "1px solid rgba(148, 163, 184, 0.15)",
          background: "rgba(15, 23, 42, 0.8)",
          backdropFilter: "blur(12px)",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <div
          style={{
            maxWidth: 800,
            margin: "0 auto",
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              background:
                "linear-gradient(135deg, #22c55e, #16a34a)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: 18,
              color: "white",
            }}
          >
            T
          </div>

          <div>
            <h1
              style={{
                margin: 0,
                fontSize: 18,
                fontWeight: 600,
              }}
            >
              TapBomba AI
            </h1>

            <p
              style={{
                margin: 0,
                fontSize: 13,
                color: "#94a3b8",
              }}
            >
              Automate. Grow. Earn.
            </p>
          </div>
        </div>
      </header>

      {/* Messages and Content Creator */}
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
        {/* AI Content Creator Feature */}
        <div
          style={{
            padding: "18px",
            borderRadius: 18,
            background: "rgba(30, 41, 59, 0.85)",
            border: "1px solid rgba(34, 197, 94, 0.25)",
            boxShadow: "0 4px 16px rgba(0,0,0,0.2)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 8,
            }}
          >
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: 12,
                background:
                  "linear-gradient(135deg, #22c55e, #16a34a)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 18,
              }}
            >
              📝
            </div>

            <div>
              <h2
                style={{
                  margin: 0,
                  fontSize: 18,
                  color: "#ffffff",
                }}
              >
                AI Content Creator
              </h2>

              <p
                style={{
                  margin: "2px 0 0",
                  color: "#94a3b8",
                  fontSize: 12,
                }}
              >
                Create content for your business
              </p>
            </div>
          </div>

          <p
            style={{
              margin: "12px 0",
              color: "#cbd5e1",
              fontSize: 14,
              lineHeight: 1.55,
            }}
          >
            Create social media posts, captions, advertisements, product
            descriptions, promotional messages, and other professional
            business content.
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
              background: loading
                ? "rgba(34, 197, 94, 0.4)"
                : "linear-gradient(135deg, #22c55e, #16a34a)",
              color: "white",
              fontWeight: 600,
              fontSize: 15,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Please wait..." : "Create Content ✨"}
          </button>
        </div>

        {/* Chat Messages */}
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              justifyContent:
                msg.role === "user" ? "flex-end" : "flex-start",
            }}
          >
            <div
              style={{
                maxWidth: "85%",
                padding: "12px 16px",
                borderRadius: 16,
                background:
                  msg.role === "user"
                    ? "linear-gradient(135deg, #22c55e, #16a34a)"
                    : "rgba(30, 41, 59, 0.9)",
                color:
                  msg.role === "user" ? "white" : "#e2e8f0",
                border:
                  msg.role === "assistant"
                    ? "1px solid rgba(148, 163, 184, 0.2)"
                    : "none",
                boxShadow:
                  msg.role === "user"
                    ? "0 4px 12px rgba(34, 197, 94, 0.25)"
                    : "0 2px 8px rgba(0,0,0,0.2)",
                whiteSpace: "pre-wrap",
                lineHeight: 1.55,
                fontSize: 15,
              }}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div
            style={{
              display: "flex",
              justifyContent: "flex-start",
            }}
          >
            <div
              style={{
                padding: "12px 16px",
                borderRadius: 16,
                background: "rgba(30, 41, 59, 0.9)",
                border:
                  "1px solid rgba(148, 163, 184, 0.2)",
                color: "#94a3b8",
                fontSize: 14,
              }}
            >
              Thinking...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Input */}
      <div
        style={{
          padding: "16px",
          borderTop:
            "1px solid rgba(148, 163, 184, 0.15)",
          background: "rgba(15, 23, 42, 0.9)",
          backdropFilter: "blur(12px)",
        }}
      >
        <form
          onSubmit={handleSubmit}
          style={{
            maxWidth: 800,
            margin: "0 auto",
            display: "flex",
            gap: 12,
            alignItems: "flex-end",
          }}
        >
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask TapBomba AI anything..."
            rows={1}
            disabled={loading}
            style={{
              flex: 1,
              resize: "none",
              padding: "14px 16px",
              borderRadius: 14,
              border:
                "1px solid rgba(148, 163, 184, 0.25)",
              background: "rgba(30, 41, 59, 0.8)",
              color: "#e2e8f0",
              fontSize: 15,
              lineHeight: 1.4,
              outline: "none",
              minHeight: 48,
              maxHeight: 120,
            }}
          />

          <button
            type="submit"
            disabled={loading || !message.trim()}
            style={{
              padding: "14px 22px",
              borderRadius: 14,
              border: "none",
              background:
                loading || !message.trim()
                  ? "rgba(34, 197, 94, 0.4)"
                  : "linear-gradient(135deg, #22c55e, #16a34a)",
              color: "white",
              fontWeight: 600,
              fontSize: 15,
              cursor:
                loading || !message.trim()
                  ? "not-allowed"
                  : "pointer",
              transition: "opacity 0.2s",
              whiteSpace: "nowrap",
            }}
          >
            {loading ? "..." : "Send"}
          </button>
        </form>

        <p
          style={{
            textAlign: "center",
            margin: "10px 0 0",
            fontSize: 12,
            color: "#64748b",
          }}
        >
          Press Enter to send • Shift + Enter for new line
        </p>
      </div>
    </div>
  );
}
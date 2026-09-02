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

    const userMessage = {
      role: "user",
      content: trimmed,
    };

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
        background: "#050505",
        color: "#ffffff",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* HEADER */}
      <header
        style={{
          padding: "16px 20px",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
          background: "rgba(5,5,5,0.96)",
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
          {/* TB LOGO */}
          <div
            style={{
              width: 42,
              height: 42,
              borderRadius: 12,
              background: "#111111",
              border: "1px solid rgba(255,255,255,0.12)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 800,
              fontSize: 17,
              color: "#ffffff",
              boxShadow: "0 0 18px rgba(255,193,7,0.08)",
            }}
          >
            TB
          </div>

          <div>
            <h1
              style={{
                margin: 0,
                fontSize: 18,
                fontWeight: 700,
                color: "#ffffff",
                letterSpacing: "-0.3px",
              }}
            >
              TapBomba <span style={{ color: "#FFD43B" }}>AI</span>
            </h1>

            <p
              style={{
                margin: "2px 0 0",
                fontSize: 13,
                color: "#ffffff",
              }}
            >
              <span style={{ color: "#FFD43B" }}>Automate.</span>{" "}
              Grow. <span style={{ color: "#FF4D4D" }}>Earn.</span>
            </p>
          </div>
        </div>
      </header>

      {/* MAIN CONTENT */}
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
        {/* AI CONTENT CREATOR */}
        <div
          style={{
            padding: "18px",
            borderRadius: 18,
            background: "#0D0D0D",
            border: "1px solid rgba(255,255,255,0.09)",
            boxShadow: "0 8px 30px rgba(0,0,0,0.35)",
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
                width: 40,
                height: 40,
                borderRadius: 12,
                background: "#151515",
                border: "1px solid rgba(255,212,59,0.22)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 18,
              }}
            >
              ✨
            </div>

            <div>
              <h2
                style={{
                  margin: 0,
                  fontSize: 18,
                  color: "#ffffff",
                  fontWeight: 700,
                }}
              >
                AI <span style={{ color: "#FFD43B" }}>Content</span>{" "}
                Creator
              </h2>

              <p
                style={{
                  margin: "3px 0 0",
                  color: "#ffffff",
                  fontSize: 12,
                  opacity: 0.7,
                }}
              >
                Create content for your business
              </p>
            </div>
          </div>

          <p
            style={{
              margin: "12px 0",
              color: "#ffffff",
              opacity: 0.82,
              fontSize: 14,
              lineHeight: 1.6,
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
              border: "1px solid rgba(255,212,59,0.25)",
              background: loading ? "#171717" : "#111111",
              color: loading ? "#888888" : "#FFD43B",
              fontWeight: 700,
              fontSize: 15,
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: loading
                ? "none"
                : "0 4px 18px rgba(255,212,59,0.08)",
            }}
          >
            {loading ? "Please wait..." : "Create Content ✨"}
          </button>
        </div>

        {/* CHAT MESSAGES */}
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
                  msg.role === "user" ? "#151515" : "#0D0D0D",
                color: "#ffffff",
                border:
                  msg.role === "user"
                    ? "1px solid rgba(255,212,59,0.18)"
                    : "1px solid rgba(255,255,255,0.09)",
                boxShadow:
                  msg.role === "user"
                    ? "0 4px 16px rgba(0,0,0,0.3)"
                    : "0 3px 12px rgba(0,0,0,0.25)",
                whiteSpace: "pre-wrap",
                lineHeight: 1.6,
                fontSize: 15,
              }}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* THINKING */}
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
                background: "#0D0D0D",
                border: "1px solid rgba(255,255,255,0.09)",
                color: "#FFD43B",
                fontSize: 14,
              }}
            >
              Thinking...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* INPUT AREA */}
      <div
        style={{
          padding: "16px",
          borderTop: "1px solid rgba(255,255,255,0.08)",
          background: "rgba(5,5,5,0.97)",
          backdropFilter: "blur(12px)",
        }}
      >
        <form
          onSubmit={handleSubmit}
          style={{
            maxWidth: 800,
            margin: "0 auto",
            display: "flex",
            gap: 10,
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
              border: "1px solid rgba(255,255,255,0.12)",
              background: "#101010",
              color: "#ffffff",
              fontSize: 15,
              lineHeight: 1.4,
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
              border: "1px solid rgba(255,212,59,0.22)",
              background:
                loading || !message.trim() ? "#171717" : "#FFD43B",
              color:
                loading || !message.trim() ? "#777777" : "#050505",
              fontWeight: 800,
              fontSize: 15,
              cursor:
                loading || !message.trim()
                  ? "not-allowed"
                  : "pointer",
              transition: "all 0.2s",
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
            color: "#ffffff",
            opacity: 0.4,
          }}
        >
          Press Enter to send • Shift + Enter for new line
        </p>
      </div>
    </div>
  );
}
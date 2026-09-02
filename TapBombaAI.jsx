"use client";

import { useState, useRef, useEffect } from "react";

export default function TapBombaAI() {
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([
    {
      role: "assistant",
      content:
        "Hello! I'm TapBomba AI — your practical business assistant. Ask me anything about business, growth, or earning online.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const textareaRef = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  async function handleSend() {
    if (!message.trim() || loading) return;

    const userMessage = message.trim();
    setMessage("");
    setChat((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const response = await fetch("/api/tapbomba", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Something went wrong.");
      }

      setChat((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply || "I couldn't generate a response.",
        },
      ]);
    } catch (error) {
      setChat((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            error instanceof Error
              ? error.message
              : "Unable to get a response right now.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
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
        {/* Header */}
        <header
          style={{
            textAlign: "center",
            marginBottom: 32,
          }}
        >
          <div
            style={{
              fontSize: 42,
              marginBottom: 8,
            }}
          >
            🚀
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: "-0.5px",
            }}
          >
            TapBomba <span style={{ color: "#FFD43B" }}>AI</span>
          </h1>

          <p
            style={{
              marginTop: 8,
              color: "#fff",
              opacity: 0.7,
              fontSize: 16,
              fontWeight: 500,
            }}
          >
            Automate. Grow. Earn.
          </p>
        </header>

        {/* AI Content Creator Card */}
        <section
          style={{
            background: "#0D0D0D",
            border: "1px solid rgba(255,255,255,0.09)",
            borderRadius: 20,
            padding: 24,
            marginBottom: 24,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 12,
            }}
          >
            <span style={{ fontSize: 24 }}>📝</span>
            <h2
              style={{
                margin: 0,
                fontSize: 20,
                fontWeight: 700,
              }}
            >
              AI Content Creator
            </h2>
          </div>

          <p
            style={{
              margin: "0 0 20px",
              color: "#fff",
              opacity: 0.7,
              lineHeight: 1.6,
              fontSize: 15,
            }}
          >
            Create social media posts, captions, advertisements, product
            descriptions, promotional messages, and other professional business
            content.
          </p>

          <button
            type="button"
            onClick={() =>
              setMessage(
                "Create a professional social media post for my business"
              )
            }
            style={{
              width: "100%",
              padding: "14px 18px",
              borderRadius: 14,
              border: "1px solid rgba(255,212,59,0.25)",
              background: "#FFD43B",
              color: "#050505",
              fontWeight: 800,
              fontSize: 15,
              cursor: "pointer",
            }}
          >
            Create Content ✨
          </button>
        </section>

        {/* Chat Area */}
        <section
          style={{
            background: "#0D0D0D",
            border: "1px solid rgba(255,255,255,0.09)",
            borderRadius: 20,
            padding: 20,
            display: "flex",
            flexDirection: "column",
            minHeight: 420,
          }}
        >
          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              marginBottom: 16,
              display: "flex",
              flexDirection: "column",
              gap: 14,
            }}
          >
            {chat.map((msg, index) => (
              <div
                key={index}
                style={{
                  alignSelf:
                    msg.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: "85%",
                  background:
                    msg.role === "user" ? "#FFD43B" : "rgba(255,255,255,0.06)",
                  color: msg.role === "user" ? "#050505" : "#fff",
                  padding: "12px 16px",
                  borderRadius: 16,
                  fontSize: 15,
                  lineHeight: 1.55,
                  whiteSpace: "pre-wrap",
                }}
              >
                {msg.content}
              </div>
            ))}

            {loading && (
              <div
                style={{
                  alignSelf: "flex-start",
                  background: "rgba(255,255,255,0.06)",
                  color: "#fff",
                  padding: "12px 16px",
                  borderRadius: 16,
                  fontSize: 15,
                  opacity: 0.7,
                }}
              >
                Thinking...
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Input Area */}
          <div>
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask TapBomba AI anything..."
              rows={3}
              style={{
                width: "100%",
                boxSizing: "border-box",
                resize: "none",
                borderRadius: 14,
                border: "1px solid rgba(255,255,255,0.12)",
                background: "#101010",
                color: "#fff",
                padding: 14,
                fontSize: 15,
                lineHeight: 1.5,
                outline: "none",
                marginBottom: 12,
              }}
            />

            <button
              type="button"
              onClick={handleSend}
              disabled={loading || !message.trim()}
              style={{
                width: "100%",
                padding: "14px 18px",
                borderRadius: 14,
                border: "1px solid rgba(255,212,59,0.25)",
                background:
                  loading || !message.trim() ? "#171717" : "#FFD43B",
                color: loading || !message.trim() ? "#777" : "#050505",
                fontWeight: 800,
                fontSize: 15,
                cursor:
                  loading || !message.trim() ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Sending..." : "Send"}
            </button>

            <p
              style={{
                margin: "10px 0 0",
                fontSize: 12,
                opacity: 0.45,
                textAlign: "center",
              }}
            >
              Press Enter to send • Shift + Enter for new line
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
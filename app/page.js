"use client";

import { useState, useRef, useEffect } from "react";

export default function Home() {
  const [mode, setMode] = useState("content");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I'm Top Bomba AI. Select a mode above and let's build something amazing.",
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

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 160) + "px";
    }
  }, [message]);

  const systemPrompts = {
    content: `You are Top Bomba AI Content Creator.
Help Nigerian and African business owners create:
- Social media posts
- Captions
- Ads
- Product descriptions
- Promotional messages

Be practical, direct, culturally relevant, and results-focused. Use simple English and local flavor when appropriate.`,

    app: `You are Top Bomba AI App Builder.

When the user wants to build an app:

1. First ask clarifying questions if needed (Web or Mobile? Main features? Preferred tech stack?).
2. Then generate a complete, working project using:
   - Next.js 15 (App Router)
   - Tailwind CSS
   - Clean, production-ready code

Always structure your reply like this:

### Project Structure
(list the folders and files)

### package.json
\`\`\`json
...
\`\`\`

### File: app/page.tsx
\`\`\`tsx
...
\`\`\`

(continue for every important file)

### How to run
\`\`\`bash
npm install
npm run dev
\`\`\`

### Deploy to Vercel
1. Push to GitHub
2. Import in Vercel
3. Deploy

Keep code modern, typed when possible, and ready to copy-paste.`,
  };

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || loading) return;

    const userMsg = { role: "user", content: trimmed };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setMessage("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          system: systemPrompts[mode],
          history: newMessages.slice(-12),
        }),
      });

      if (!res.ok) throw new Error("API error");

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply || "No response received." },
      ]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Server error. Please try again in a moment.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function switchMode(newMode) {
    if (newMode === mode) return;
    setMode(newMode);
    setMessages([
      {
        role: "assistant",
        content:
          newMode === "app"
            ? "🚀 App Builder Mode ON\n\nDescribe the app you want to build.\nExample: “Build a simple POS web app for my provision store with sales tracking and receipt printing”"
            : "✨ Content Creator Mode ON\n\nWhat content do you need today?\nExample: “Write 5 Instagram captions for my fashion store”",
      },
    ]);
  }

  function renderContent(text) {
    const parts = text.split(/(```[\s\S]*?```)/g);

    return parts.map((part, i) => {
      if (part.startsWith("```")) {
        const match = part.match(/```(\w+)?\n?([\s\S]*?)```/);
        if (match) {
          const lang = match[1] || "";
          const code = match[2];
          return (
            <pre
              key={i}
              style={{
                background: "#111",
                border: "1px solid rgba(255,212,59,0.25)",
                borderRadius: 12,
                padding: 14,
                overflowX: "auto",
                margin: "12px 0",
                fontSize: 13,
                lineHeight: 1.5,
              }}
            >
              {lang && (
                <div
                  style={{
                    color: "#FFD43B",
                    fontSize: 11,
                    marginBottom: 8,
                    fontWeight: 600,
                  }}
                >
                  {lang}
                </div>
              )}
              <code>{code}</code>
            </pre>
          );
        }
      }
      return (
        <span key={i} style={{ whiteSpace: "pre-wrap" }}>
          {part}
        </span>
      );
    });
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#000",
        color: "#fff",
        fontFamily: "system-ui, -apple-system, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: "16px 20px",
          borderBottom: "1px solid rgba(255,212,59,0.2)",
          background: "rgba(0,0,0,0.95)",
        }}
      >
        <div
          style={{
            maxWidth: 800,
            margin: "0 auto",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: 12,
          }}
        >
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 12,
              background: "linear-gradient(135deg, #FFD43B, #FFA500)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              fontSize: 22,
              color: "#000",
            }}
          >
            TB
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 18 }}>Top Bomba AI</div>
            <div style={{ fontSize: 12, opacity: 0.7 }}>
              Automate. Grow. Earn.
            </div>
          </div>
        </div>
      </header>

      <main
        style={{
          flex: 1,
          maxWidth: 800,
          width: "100%",
          margin: "0 auto",
          padding: "20px 16px",
          overflowY: "auto",
        }}
      >
        {/* Mode Switcher */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 12,
            marginBottom: 24,
          }}
        >
          <div
            onClick={() => switchMode("content")}
            style={{
              padding: 16,
              borderRadius: 16,
              cursor: "pointer",
              background:
                mode === "content"
                  ? "linear-gradient(135deg, #FFD43B 0%, #FFA500 100%)"
                  : "#0A0A0A",
              border: "1px solid rgba(255,212,59,0.3)",
              color: mode === "content" ? "#000" : "#fff",
              transition: "all 0.2s",
            }}
          >
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 800 }}>
              ✨ Content Creator
            </h3>
            <p style={{ margin: "4px 0 0", fontSize: 12, opacity: 0.85 }}>
              Posts • Ads • Captions
            </p>
          </div>

          <div
            onClick={() => switchMode("app")}
            style={{
              padding: 16,
              borderRadius: 16,
              cursor: "pointer",
              background:
                mode === "app"
                  ? "linear-gradient(135deg, #FFD43B 0%, #FFA500 100%)"
                  : "#0A0A0A",
              border: "1px solid rgba(255,212,59,0.3)",
              color: mode === "app" ? "#000" : "#fff",
              transition: "all 0.2s",
            }}
          >
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 800 }}>
              🚀 App Builder
            </h3>
            <p style={{ margin: "4px 0 0", fontSize: 12, opacity: 0.85 }}>
              Full App Code + Deploy
            </p>
          </div>
        </div>

        {/* Messages */}
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              marginBottom: 14,
            }}
          >
            <div
              style={{
                maxWidth: "88%",
                padding: "12px 16px",
                borderRadius: 16,
                background: msg.role === "user" ? "#151515" : "#0A0A0A",
                border: "1px solid rgba(255,212,59,0.2)",
                lineHeight: 1.55,
              }}
            >
              {msg.role === "assistant"
                ? renderContent(msg.content)
                : msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div
            style={{
              display: "flex",
              gap: 6,
              padding: "8px 0",
              color: "#FFD43B",
              fontSize: 14,
            }}
          >
            <span>Thinking</span>
            <span>.</span>
            <span>.</span>
            <span>.</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Input */}
      <div
        style={{
          padding: "16px",
          borderTop: "1px solid rgba(255,212,59,0.2)",
          background: "rgba(0,0,0,0.97)",
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
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder={
              mode === "app"
                ? "Describe the app you want to build..."
                : "Ask for content ideas..."
            }
            rows={1}
            disabled={loading}
            style={{
              flex: 1,
              padding: "14px 16px",
              borderRadius: 14,
              border: "1px solid rgba(255,212,59,0.3)",
              background: "#0F0F0F",
              color: "#fff",
              fontSize: 15,
              resize: "none",
              outline: "none",
              maxHeight: 160,
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
                  ? "#333"
                  : "linear-gradient(135deg, #FFD43B 0%, #FFA500 100%)",
              color: loading || !message.trim() ? "#888" : "#000",
              fontWeight: 800,
              cursor: loading || !message.trim() ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}
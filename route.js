import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(req) {
  try {
    const body = await req.json();

    const message =
      typeof body.message === "string" ? body.message.trim() : "";
    const system =
      typeof body.system === "string" && body.system.trim()
        ? body.system.trim()
        : "You are TapBomba AI, a friendly and practical business assistant for Nigerian entrepreneurs. Use ₦ for Naira where appropriate and give practical business advice.";

    if (!message) {
      return Response.json(
        { error: "Message is required" },
        { status: 400 }
      );
    }

    if (message.length > 4000) {
      return Response.json(
        { error: "Message is too long" },
        { status: 400 }
      );
    }

    // Build conversation history (optional)
    let messages = [{ role: "system", content: system }];

    if (Array.isArray(body.history) && body.history.length > 0) {
      // Take only the last few messages and map them correctly
      const recent = body.history.slice(-12);
      for (const msg of recent) {
        if (msg.role === "user" || msg.role === "assistant") {
          messages.push({
            role: msg.role,
            content: String(msg.content || ""),
          });
        }
      }
    } else {
      messages.push({ role: "user", content: message });
    }

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages,
    });

    return Response.json({
      reply: completion.choices[0]?.message?.content ?? "",
    });
  } catch (error) {
    console.error("TapBomba AI error:", error);

    const status = error?.status === 429 ? 429 : 500;

    return Response.json(
      {
        error:
          status === 429
            ? "Too many requests. Please try again shortly."
            : "Something went wrong. Please try again.",
      },
      { status }
    );
  }
}
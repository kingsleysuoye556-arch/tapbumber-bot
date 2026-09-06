import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(req) {
  try {
    const body = await req.json();

    const message =
      typeof body.message === "string" ? body.message.trim() : null;

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

    // Use the system prompt coming from the frontend (Content Creator or App Builder)
    const systemPrompt =
      typeof body.system === "string" && body.system.trim()
        ? body.system.trim()
        : "You are TapBomba AI, a friendly and practical business assistant for Nigerian and African entrepreneurs. Give clear, actionable advice. Use ₦ when talking about money.";

    // Support conversation history
    const history = Array.isArray(body.history) ? body.history : [];

    const messages = [
      { role: "system", content: systemPrompt },
      ...history
        .filter((m) => m.role === "user" || m.role === "assistant")
        .map((m) => ({
          role: m.role,
          content: String(m.content || "").slice(0, 4000),
        })),
      { role: "user", content: message },
    ];

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages,
      temperature: 0.7,
      max_tokens: 2000,
    });

    return Response.json({
      reply: completion.choices[0]?.message?.content ?? "No response generated.",
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
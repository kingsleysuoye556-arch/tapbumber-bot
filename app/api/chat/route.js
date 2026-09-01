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

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content:
            "You are TapBomba AI, a friendly and practical business assistant for Nigerian entrepreneurs. Use ₦ for Naira where appropriate and give practical business advice.",
        },
        {
          role: "user",
          content: message,
        },
      ],
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
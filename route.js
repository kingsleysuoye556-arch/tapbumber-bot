export const runtime = "nodejs";

export async function POST(request) {
  try {
    const { message } = await request.json();

    if (!message || typeof message !== "string") {
      return Response.json(
        { error: "Please provide a message." },
        { status: 400 }
      );
    }

    if (!process.env.OPENAI_API_KEY) {
      return Response.json(
        { error: "AI service is not configured yet." },
        { status: 500 }
      );
    }

    const response = await fetch(
      "https://api.openai.com/v1/chat/completions",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
        },
        body: JSON.stringify({
          model: "gpt-4o-mini",
          messages: [
            {
              role: "system",
              content:
                "You are TapBomba AI, a helpful, friendly, and professional AI assistant. Give clear and useful answers.",
            },
            {
              role: "user",
              content: message,
            },
          ],
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      return Response.json(
        {
          error: data?.error?.message || "OpenAI request failed.",
        },
        { status: response.status }
      );
    }

    return Response.json({
      success: true,
      response:
        data?.choices?.[0]?.message?.content ||
        "No response generated.",
    });
  } catch (error) {
    console.error("TapBomba AI error:", error);

    return Response.json(
      { error: "Something went wrong while contacting TapBomba AI." },
      { status: 500 }
    );
  }
}
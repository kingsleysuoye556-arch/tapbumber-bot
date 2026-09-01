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

    const apiKey = process.env.OPENAI_API_KEY;

    if (!apiKey) {
      return Response.json(
        { error: "OpenAI API key is not configured." },
        { status: 500 }
      );
    }

    const openAIResponse = await fetch(
      "https://api.openai.com/v1/chat/completions",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: "gpt-4o-mini",
          messages: [
            {
              role: "system",
              content:
                "You are TapBomba AI, a helpful, friendly, and professional AI business assistant. Give clear, practical, useful answers. Do not claim to have performed actions you cannot actually perform.",
            },
            {
              role: "user",
              content: message.trim(),
            },
          ],
        }),
      }
    );

    const data = await openAIResponse.json();

    if (!openAIResponse.ok) {
      console.error("OpenAI error:", data);

      return Response.json(
        {
          error:
            data?.error?.message ||
            "OpenAI could not process the request.",
        },
        { status: openAIResponse.status }
      );
    }

    const answer =
      data?.choices?.[0]?.message?.content;

    if (!answer) {
      return Response.json(
        { error: "No AI response was generated." },
        { status: 500 }
      );
    }

    return Response.json({
      success: true,
      response: answer,
    });
  } catch (error) {
    console.error("TapBomba AI error:", error);

    return Response.json(
      {
        error:
          "Something went wrong while contacting TapBomba AI.",
      },
      { status: 500 }
    );
  }
}
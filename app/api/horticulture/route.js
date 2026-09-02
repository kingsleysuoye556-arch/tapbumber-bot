import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(req) {
  try {
    const body = await req.json();

    const request =
      typeof body.request === "string" ? body.request.trim() : "";

    if (!request) {
      return Response.json(
        { error: "Please describe the horticulture design you want." },
        { status: 400 }
      );
    }

    if (request.length > 4000) {
      return Response.json(
        { error: "Your design request is too long." },
        { status: 400 }
      );
    }

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content:
            "You are TapBomba AI's professional Horticulture Designer. Create practical, attractive horticulture and landscape plans for Nigerian homes, buildings, gardens, compounds, walkways and outdoor spaces. Recommend suitable plants, flowers, trees, spacing, layout, maintenance and estimated considerations where useful. Give clear, professional and easy-to-understand plans.",
        },
        {
          role: "user",
          content: request,
        },
      ],
    });

    const result =
      completion.choices[0]?.message?.content ||
      "Unable to create a horticulture design.";

    return Response.json({ result });
  } catch (error) {
    console.error("Horticulture AI error:", error);

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
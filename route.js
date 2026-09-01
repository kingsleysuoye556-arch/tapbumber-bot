import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request) {
  try {
    const { message, tool } = await request.json();

    if (!message || typeof message !== "string") {
      return Response.json(
        { error: "Please provide a message." },
        { status: 400 }
      );
    }

    const tools = {
      content: "AI Content Creator",
      business: "Business Assistant",
      social: "Social Media Assistant",
      marketing: "Marketing Assistant",
      ideas: "AI Idea Generator",
      automation: "Automation Hub",
    };

    const selectedTool = tools[tool] || "TapBumber AI Assistant";

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content: `You are TapBumber AI, a helpful and professional AI assistant.
The user selected: ${selectedTool}.
Give practical, clear, useful answers.
Do not claim to have performed actions you cannot actually perform.`,
        },
        {
          role: "user",
          content: message,
        },
      ],
    });

    return Response.json({
      success: true,
      response: completion.choices[0]?.message?.content || "No response generated.",
    });
  } catch (error) {
    console.error("TapBumber AI error:", error);

    return Response.json(
      { error: "Something went wrong while contacting TapBumber AI." },
      { status: 500 }
    );
  }
}
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request) {
  try {
    const { prompt } = await request.json();

    if (!prompt || !prompt.trim()) {
      return Response.json(
        { error: "Please enter what you want TapBomba AI to create." },
        { status: 400 }
      );
    }

    const response = await openai.images.generate({
      model: "gpt-image-2",
      prompt: prompt,
      size: "1024x1024",
    });

    return Response.json({
      image: response.data[0].b64_json,
    });

  } catch (error) {
    console.error("TapBomba AI Image Error:", error);

    return Response.json(
      {
        error:
          error?.message ||
          "TapBomba AI could not generate the image.",
      },
      { status: 500 }
    );
  }
}
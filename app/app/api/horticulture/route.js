"use client";

import { useState } from "react";

export default function HorticultureDesigner() {
  const [request, setRequest] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleDesign() {
    if (!request.trim()) return;

    setLoading(true);
    setResult("");

    try {
      const response = await fetch("/api/horticulture", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ request }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Something went wrong.");
      }

      setResult(data.result);
    } catch (error) {
      setResult(error.message || "Unable to create design.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-green-50 px-4 py-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-8 text-center">
          <div className="text-5xl">🌺</div>

          <h1 className="mt-3 text-3xl font-bold text-green-900">
            Horticulture Designer
          </h1>

          <p className="mt-2 text-green-700">
            Design beautiful flower and plant landscapes for houses,
            buildings and outdoor spaces.
          </p>
        </div>

        <div className="rounded-2xl bg-white p-5 shadow-lg">
          <label className="mb-2 block font-semibold text-gray-800">
            What would you like to design?
          </label>

          <textarea
            value={request}
            onChange={(e) => setRequest(e.target.value)}
            placeholder="Example: Design a beautiful modern house with Royal Palms, flowering plants and decorative trees around the entrance and walkway."
            className="min-h-36 w-full rounded-xl border border-green-200 p-4 outline-none focus:border-green-500"
          />

          <button
            onClick={handleDesign}
            disabled={loading}
            className="mt-4 w-full rounded-xl bg-green-700 px-5 py-3 font-bold text-white hover:bg-green-800 disabled:opacity-50"
          >
            {loading ? "Creating Design..." : "Create Horticulture Design 🌿"}
          </button>
        </div>

        {result && (
          <div className="mt-6 rounded-2xl bg-white p-5 shadow-lg">
            <h2 className="mb-3 text-xl font-bold text-green-900">
              Your Horticulture Plan 🌱
            </h2>

            <div className="whitespace-pre-wrap leading-7 text-gray-700">
              {result}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
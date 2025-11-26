"use client";

import { useState } from "react";
import { getItineraryWithPolling } from "@/lib/api";

export default function ItineraryForm({
  onResult,
}: {
  onResult: (text: string) => void;
}) {
  const [text, setText] = useState("");
  const [days, setDays] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await getItineraryWithPolling({ text, days });
      onResult(result.itinerary);
    } catch (err: any) {
      onResult(`ERROR: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full bg-white rounded-2xl shadow-xl border border-gray-200 p-8 space-y-6"
    >
      <h2 className="text-2xl font-semibold text-gray-800">
        Generate an Itinerary
      </h2>

      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-600">
          Describe your trip
        </label>
        <textarea
          className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none text-gray-800"
          placeholder="E.g. Plan a 3-day trip to Rome focusing on culture and authentic food..."
          rows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-600">
          Optional: Number of Days
        </label>
        <input
          type="number"
          min={1}
          max={14}
          className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none text-gray-800 placeholder:text-slate-500 placeholder:opacity-100"
          placeholder="E.g. 4"
          value={days ?? ""}
          onChange={(e) => setDays(Number(e.target.value) || undefined)}
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 text-lg font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-all shadow-md"
      >
        {loading ? "Generating..." : "Generate Itinerary"}
      </button>
    </form>
  );
}

"use client";

import React, { useState } from "react";
import { getItineraryWithPolling } from "../lib/api";
import { useItineraryStore } from "../store/itineraryStore";
import { useHydrated } from "@/hooks/useHydrated";

export default function ItineraryFormFull() {
  const hydrated = useHydrated();
  const setItinerary = useItineraryStore((s) => s.setItinerary);
  const setLoading = useItineraryStore((s) => s.setLoading);
  const setError = useItineraryStore((s) => s.setError);

  const [text, setText] = useState("Plan a 2-day trip to Los Angeles");
  const [days, setDays] = useState<number | "">(2);
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [travelers, setTravelers] = useState<number | "">(2);
  const [budget, setBudget] = useState<number | "">("");

  if (!hydrated) return null;

  const handleGenerate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    setError(null);
    setLoading(true);

    try {
      const payload: any = { text };
      if (days !== "") payload.days = Number(days);
      if (startDate) payload.start_date = startDate;
      if (endDate) payload.end_date = endDate;
      if (travelers !== "") payload.travelers = Number(travelers);
      if (budget !== "") payload.budget = Number(budget);

      const res = await getItineraryWithPolling(payload);
      if (!res || typeof res.itinerary !== "string") {
        throw new Error("Invalid response from server");
      }

      setItinerary(res.itinerary);
    } catch (err: any) {
      console.error("Generation failed:", err);
      setError(err.message || String(err));
      setItinerary("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleGenerate} className="p-4 space-y-3 max-w-2xl">
      <label className="block">
        <div className="text-sm font-medium">What would you like planned?</div>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          className="w-full mt-1 p-2 border rounded"
        />
      </label>

      <div className="grid grid-cols-2 gap-2">
        <label>
          Days
          <input
            type="number"
            min={1}
            max={14}
            value={days as any}
            onChange={(e) =>
              setDays(e.target.value === "" ? "" : Number(e.target.value))
            }
            className="w-full mt-1 p-2 border rounded"
          />
        </label>

        <label>
          Travelers
          <input
            type="number"
            min={1}
            value={travelers as any}
            onChange={(e) =>
              setTravelers(e.target.value === "" ? "" : Number(e.target.value))
            }
            className="w-full mt-1 p-2 border rounded"
          />
        </label>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <label>
          Start Date
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full mt-1 p-2 border rounded"
          />
        </label>

        <label>
          End Date
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full mt-1 p-2 border rounded"
          />
        </label>
      </div>

      <label>
        Budget (USD)
        <input
          type="number"
          value={budget as any}
          onChange={(e) =>
            setBudget(e.target.value === "" ? "" : Number(e.target.value))
          }
          className="w-full mt-1 p-2 border rounded"
        />
      </label>

      <div className="flex gap-2">
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          Generate Itinerary
        </button>

        <button
          type="button"
          onClick={handleGenerate}
          className="px-4 py-2 bg-gray-200 rounded"
        >
          Quick Test
        </button>
      </div>
    </form>
  );
}

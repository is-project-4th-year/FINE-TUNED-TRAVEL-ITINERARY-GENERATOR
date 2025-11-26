"use client";

import { useItineraryStore } from "../store/itineraryStore";
import { useEffect } from "react";
import { useHydrated } from "@/hooks/useHydrated";

export default function ItineraryResult() {
  const hydrated = useHydrated();
  if (!hydrated) return null;
  const itinerary = useItineraryStore((s) => s.itinerary);
  const loading = useItineraryStore((s) => s.loading);
  const error = useItineraryStore((s) => s.error);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  if (loading) {
    return <p className="p-4">Generating itinerary...</p>;
  }

  if (error) {
    return (
      <p className="p-4 text-red-600">Error generating itinerary: {error}</p>
    );
  }

  if (!itinerary) {
    return <p className="p-4">No itinerary generated yet.</p>;
  }

  return (
    <div className="max-w-2xl mx-auto my-8 bg-white rounded-2xl shadow-xl border border-gray-200 p-8">
      <h2 className="text-2xl font-bold text-blue-700 mb-6">
        Your Generated Itinerary
      </h2>
      <div className="whitespace-pre-line text-gray-800 text-lg leading-relaxed">
        {itinerary}
      </div>
    </div>
  );
}

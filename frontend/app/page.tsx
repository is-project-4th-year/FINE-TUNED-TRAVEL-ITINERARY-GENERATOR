"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/store/authStore";
import { useItineraryStore } from "@/store/itineraryStore";
import { generateItinerary } from "@/lib/api";
import Navbar from "@/components/Navbar_only";
import LoadingButton from "@/components/LoadingButton";
import FormSummary from "@/components/FormSummary";

// Custom hook to check hydration
function useHydrated() {
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => {
    setHydrated(true);
  }, []);
  return hydrated;
}

export default function HomePage() {
  // --- All hooks must be called unconditionally at the top ---
  const hydrated = useHydrated();
  const { isLoggedIn, setIsLoggedIn } = useAuth();
  const router = useRouter();
  const [text, setText] = useState("");
  const [days, setDays] = useState<number | undefined>(undefined);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [travelers, setTravelers] = useState<number | undefined>(2);
  const [budget, setBudget] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [activeChip, setActiveChip] = useState<string | null>(null);
  const checkInRef = useRef<HTMLInputElement | null>(null);

  // Only redirect after hydration is complete and user is definitely not logged in
  // Persist login state in localStorage
  useEffect(() => {
    if (hydrated) {
      const storedLogin = localStorage.getItem("isLoggedIn");
      if (storedLogin === "true") {
        setIsLoggedIn(true);
        if (typeof window !== "undefined" && window.location.pathname !== "/") {
          router.push("/");
        }
      } else if (!isLoggedIn) {
        router.push("/auth/signin");
      }
    }
  }, [hydrated, isLoggedIn, router, setIsLoggedIn]);

  useEffect(() => {
    if (hydrated) {
      localStorage.setItem("isLoggedIn", isLoggedIn ? "true" : "false");
    }
  }, [hydrated, isLoggedIn]);

  // --- Zustand itinerary store ---
  const setItinerary = useItineraryStore((s) => s.setItinerary);
  const setLoadingStore = useItineraryStore((s) => s.setLoading);
  const setError = useItineraryStore((s) => s.setError);
  const clearItinerary = useItineraryStore((s) => s.clear);

  // --- Generate itinerary logic ---
  async function handleGenerate(e?: React.FormEvent) {
    e?.preventDefault();
    setLoading(true);
    setDone(false);
    setLoadingStore(true);
    setError(null);
    clearItinerary();
    try {
      const payload = {
        text,
        days,
        start_date: startDate,
        end_date: endDate,
        travelers,
        budget,
      };
      const result = await generateItinerary(payload);
      setItinerary(result.itinerary || "");
      setDone(true);
    } catch (err: any) {
      setError(err?.message ?? "Unknown error");
      // Log full error object for debugging
      // eslint-disable-next-line no-console
      console.error("Itinerary generation error:", err);
      alert("Generation failed: " + (err?.message ?? err));
    } finally {
      setLoading(false);
      setLoadingStore(false);
    }
  }

  // --- Conditional rendering after all hooks ---
  if (!hydrated) {
    return (
      <div className="min-h-screen bg-emerald-50 flex items-center justify-center">
        <p className="text-gray-600 text-lg">Loading...</p>
      </div>
    );
  }
  if (!isLoggedIn) {
    return null;
  }

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main className="max-w-7xl mx-auto p-8 flex flex-col md:flex-row gap-8">
        <section className="flex-1 bg-white rounded-2xl shadow-lg p-8 border border-teal-100">
          <h1 className="text-4xl font-bold mb-8 text-teal-700">
            Create Your Itinerary
          </h1>
          <form onSubmit={handleGenerate} className="space-y-6">
            <label className="block">
              <span className="text-base font-semibold text-teal-700">
                What would you like planned?
              </span>
              <textarea
                placeholder="E.g. Plan a 3-day trip to Rome focusing on culture and authentic food..."
                className="w-full mt-2 p-4 border border-gray-300 rounded-xl bg-white text-gray-900 placeholder:text-black focus:bg-gray-50 focus:border-gray-500 focus:ring-2 focus:ring-gray-300 focus:outline-none"
                rows={3}
                value={text}
                onChange={(e) => {
                  setText(e.target.value);
                  setActiveChip(null);
                }}
                required
              />
            </label>
            {/* Example chips */}
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              <button
                type="button"
                onClick={() => {
                  setText(
                    "Plan a 4-day food & culture trip to Nairobi focusing on museums, local markets..."
                  );
                  setActiveChip("food");
                }}
                className={`px-3 py-1 rounded-full border transition ${
                  activeChip === "food"
                    ? "bg-emerald-100 text-emerald-700 border-emerald-300"
                    : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                }`}
              >
                Food & culture trip
              </button>
              <button
                type="button"
                onClick={() => {
                  setText(
                    "Weekend getaway with art galleries, romantic restaurants, and local nightlife."
                  );
                  setActiveChip("weekend");
                }}
                className={`px-3 py-1 rounded-full border transition ${
                  activeChip === "weekend"
                    ? "bg-indigo-100 text-indigo-700 border-indigo-300"
                    : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                }`}
              >
                Weekend getaway
              </button>
              <button
                type="button"
                onClick={() => {
                  setText(
                    "Family-friendly trip with local markets, hands-on activities and attractions."
                  );
                  setActiveChip("family");
                }}
                className={`px-3 py-1 rounded-full border transition ${
                  activeChip === "family"
                    ? "bg-blue-100 text-blue-700 border-blue-300"
                    : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                }`}
              >
                Family friendly
              </button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <label className="block">
                <span className="text-sm font-medium text-teal-700">Days</span>
                <input
                  type="number"
                  min={1}
                  max={14}
                  className="w-full mt-2 p-3 border border-gray-300 rounded-xl bg-white text-gray-900 placeholder:text-black focus:bg-gray-50 focus:border-gray-500 focus:ring-2 focus:ring-gray-300 focus:outline-none"
                  placeholder="E.g. 4"
                  value={days ?? ""}
                  onChange={(e) => setDays(Number(e.target.value) || undefined)}
                />
              </label>
              <label className="block">
                <span className="text-sm font-medium text-teal-700">
                  Travelers
                </span>
                <input
                  type="number"
                  min={1}
                  className="w-full mt-2 p-3 border border-gray-300 rounded-xl bg-white text-gray-900 placeholder:text-black focus:bg-gray-50 focus:border-gray-500 focus:ring-2 focus:ring-gray-300 focus:outline-none"
                  placeholder="E.g. 2"
                  value={travelers ?? ""}
                  onChange={(e) => setTravelers(Number(e.target.value) || 1)}
                />
              </label>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <label className="block">
                <span className="text-sm font-medium text-teal-700">
                  Start Date
                </span>
                <input
                  type="date"
                  className="w-full mt-2 p-3 border border-gray-300 rounded-xl bg-white text-gray-900 focus:bg-gray-50 focus:border-gray-500 focus:ring-2 focus:ring-gray-300 focus:outline-none"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </label>
              <label className="block">
                <span className="text-sm font-medium text-teal-700">
                  End Date
                </span>
                <input
                  type="date"
                  className="w-full mt-2 p-3 border border-gray-300 rounded-xl bg-white text-gray-900 focus:bg-gray-50 focus:border-gray-500 focus:ring-2 focus:ring-gray-300 focus:outline-none"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </label>
            </div>
            <label className="block">
              <span className="text-sm font-medium text-teal-700">
                Budget (USD)
              </span>
              <input
                type="number"
                className="w-full mt-2 p-3 border border-gray-300 rounded-xl bg-white text-gray-900 placeholder:text-black focus:bg-gray-50 focus:border-gray-500 focus:ring-2 focus:ring-gray-300 focus:outline-none"
                placeholder="E.g. 1000"
                value={budget ?? ""}
                onChange={(e) => setBudget(Number(e.target.value) || undefined)}
              />
            </label>
            <div className="flex flex-col md:flex-row gap-4 mt-8">
              <div className="flex-1">
                <LoadingButton loading={loading} done={done} type="submit">
                  Generate Itinerary
                </LoadingButton>
              </div>
              {done && (
                <button
                  type="button"
                  onClick={() => router.push("/itinerary")}
                  className="flex-1 py-3 rounded-xl bg-indigo-600 text-white shadow-md font-semibold hover:bg-indigo-700"
                >
                  View Itinerary →
                </button>
              )}
            </div>
          </form>
        </section>
        <aside className="w-full md:w-[28vw] lg:w-[22vw] xl:w-[20vw] shrink-0 mt-0 md:mt-2">
          <FormSummary
            title="Trip Summary"
            dates={
              startDate && endDate ? `${startDate} → ${endDate}` : undefined
            }
            travelers={travelers}
            budget={budget}
            onEdit={() => {
              const el = document.querySelector("input[type='date']");
              if (el) {
                el.scrollIntoView({ behavior: "smooth", block: "center" });
                (el as HTMLInputElement).focus();
              }
            }}
          />
          {loading && (
            <div className="flex flex-col items-center mt-8">
              <svg
                className="animate-spin h-8 w-8 text-indigo-600 mb-2"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                />
              </svg>
              <span className="text-indigo-700 font-semibold">
                Generating itinerary with Hermes...
              </span>
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}

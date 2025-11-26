"use client";

import Navbar from "@/components/Navbar_only";
import { useRef } from "react";
import jsPDF from "jspdf";
import { useRouter } from "next/navigation";
import { useItineraryStore } from "@/store/itineraryStore";
import { useAuth } from "@/store/authStore";
import { useHydrated } from "@/hooks/useHydrated";

export default function ItineraryRoute() {
  const hydrated = useHydrated();
  const router = useRouter();
  const { isLoggedIn } = useAuth();
  const { itinerary } = useItineraryStore();
  const itineraryRef = useRef<HTMLDivElement>(null);

  const handleDownloadPDF = () => {
    if (!itinerary) return;
    const doc = new jsPDF({ orientation: "portrait" });
    doc.setFont("helvetica", "normal");
    doc.setFontSize(16);
    doc.text(itinerary, 20, 30, { maxWidth: 170 });
    doc.save("itinerary.pdf");
  };

  if (!hydrated) return null;

  if (!isLoggedIn) {
    router.push("/auth/signin");
    return null;
  }

  return (
    <div className="min-h-screen bg-blue-50">
      <Navbar />

      <main className="max-w-4xl mx-auto p-6">
        <h1 className="text-4xl font-extrabold text-blue-700 mb-8 tracking-tight text-center">
          Your Itinerary
        </h1>

        {!itinerary ? (
          <p className="text-gray-600">No itinerary generated yet.</p>
        ) : (
          <div
            className="max-w-2xl mx-auto my-8 bg-white rounded-2xl shadow-xl border border-gray-200 p-8 relative"
            ref={itineraryRef}
          >
            <h2 className="text-2xl font-bold text-blue-700 mb-6">
              Your Generated Itinerary
            </h2>
            <div className="whitespace-pre-line text-gray-800 text-lg leading-relaxed">
              {itinerary}
            </div>
            <button
              onClick={handleDownloadPDF}
              className="fixed bottom-8 right-8 px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-lg font-bold z-50"
            >
              Download PDF
            </button>
          </div>
        )}

        <button
          onClick={() => router.push("/")}
          className="fixed bottom-8 left-8 px-5 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg shadow-lg font-bold z-50"
        >
          Back to Planner
        </button>
      </main>
    </div>
  );
}

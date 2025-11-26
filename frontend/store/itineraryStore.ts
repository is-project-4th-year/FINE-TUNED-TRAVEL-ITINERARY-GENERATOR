"use client";

import { create } from "zustand";

type ItineraryState = {
  itinerary: string;
  loading: boolean;
  error?: string | null;
  setItinerary: (t: string) => void;
  setLoading: (v: boolean) => void;
  setError: (e?: string | null) => void;
  clear: () => void;
};

export const useItineraryStore = create<ItineraryState>((set) => ({
  itinerary: "",
  loading: false,
  error: null,

  setItinerary: (t) => set({ itinerary: t }),
  setLoading: (v) => set({ loading: v }),
  setError: (e) => set({ error: e }),

  clear: () => set({ itinerary: "", loading: false, error: null }),
}));

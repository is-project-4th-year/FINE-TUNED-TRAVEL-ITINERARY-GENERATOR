"use client";

import { useAuth } from "@/store/authStore";
import { useHydrated } from "@/hooks/useHydrated";
import { useRouter } from "next/navigation";

export default function Navbar() {
  const hydrated = useHydrated();
  const { isLoggedIn, logout } = useAuth();
  const router = useRouter();

  if (!hydrated) return null;

  return (
    <nav className="w-full bg-white shadow px-6 py-4 flex justify-between items-center">
      <h1
        className="text-xl font-bold text-emerald-700 cursor-pointer"
        onClick={() => router.push("/")}
      >
        Travel Planner
      </h1>

      {isLoggedIn && (
        <button
          onClick={() => {
            logout();
            router.push("/auth/signin");
          }}
          className="px-4 py-2 rounded bg-red-500 hover:bg-red-600 text-white"
        >
          Logout
        </button>
      )}
    </nav>
  );
}

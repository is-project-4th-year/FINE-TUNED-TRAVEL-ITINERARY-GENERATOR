// frontend/components/LoadingButton.tsx
"use client";
import React from "react";

export default function LoadingButton({
  loading,
  done,
  children,
  type = "button",
}: {
  loading: boolean;
  done?: boolean;
  children?: React.ReactNode;
  type?: "button" | "submit";
}) {
  const base =
    "w-full py-3 rounded-xl text-lg font-semibold transition-shadow flex items-center justify-center gap-3";
  const style = loading
    ? "bg-indigo-600 text-white shadow-md"
    : done
    ? "bg-emerald-600 text-white shadow-lg"
    : "bg-indigo-700 text-white shadow-md hover:shadow-lg";

  return (
    <button disabled={loading} type={type} className={`${base} ${style}`}>
      {loading && (
        <svg
          className="animate-spin h-5 w-5 text-white"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
          ></path>
        </svg>
      )}
      <span>
        {loading ? "Generating..." : done ? "Generation complete" : children}
      </span>
    </button>
  );
}

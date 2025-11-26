"use client";

import React from "react";

export default function ItineraryDayCard({
  dayNumber,
  content,
  onEdit,
}: {
  dayNumber: number;
  content: string;
  onEdit: () => void;
}) {
  return (
    <article className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-800">
          Day {dayNumber}
        </h3>

        <button
          onClick={onEdit}
          className="text-sm px-3 py-1 rounded-md border border-slate-300 
                     hover:bg-slate-50 text-slate-700"
        >
          Edit
        </button>
      </div>

      <div className="whitespace-pre-line text-slate-700 leading-relaxed">
        {content}
      </div>
    </article>
  );
}

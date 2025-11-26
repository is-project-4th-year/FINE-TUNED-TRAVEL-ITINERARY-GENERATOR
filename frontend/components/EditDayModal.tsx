"use client";

import React, { useState, useEffect } from "react";

export default function EditDayModal({
  open,
  initialText,
  dayNumber,
  onClose,
  onSave,
}: {
  open: boolean;
  initialText: string;
  dayNumber: number;
  onClose: () => void;
  onSave: (newText: string) => void;
}) {
  const [text, setText] = useState(initialText);

  useEffect(() => {
    if (open) setText(initialText);
  }, [open, initialText]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center px-4">
      <div className="bg-white w-full max-w-xl rounded-2xl shadow-2xl border border-slate-200 p-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-4">
          Edit Day {dayNumber}
        </h2>

        <textarea
          className="w-full h-64 p-4 border border-slate-300 rounded-xl text-slate-800 
          focus:ring-2 focus:ring-emerald-400 focus:outline-none"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border border-slate-300 
              text-slate-600 hover:bg-slate-100 hover:text-slate-800 transition shadow-sm"
          >
            Cancel
          </button>

          <button
            onClick={() => onSave(text)}
            className="px-4 py-2 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 shadow"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

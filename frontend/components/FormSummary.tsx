"use client";

export default function FormSummary({
  title,
  dates,
  travelers,
  budget,
  onEdit,
}: {
  title?: string;
  dates?: string;
  travelers?: number;
  budget?: number;
  onEdit?: () => void;
}) {
  return (
    <aside className="w-full md:w-72 lg:w-80 shrink-0 bg-white rounded-2xl border border-slate-200 p-4 shadow-sm h-fit">
      <h3 className="text-base font-semibold text-slate-800 mb-4">
        {title || "Trip Summary"}
      </h3>

      <div className="text-sm text-slate-700 space-y-4">
        <div>
          <div className="text-xs text-slate-500">Dates</div>
          <div className="mt-1 font-medium">{dates || "—"}</div>
        </div>

        <div>
          <div className="text-xs text-slate-500">Number of Travelers</div>
          <div className="mt-1 font-medium">{travelers ?? 1}</div>
        </div>

        <div>
          <div className="text-xs text-slate-500">Budget</div>
          <div className="mt-1 font-medium">{budget ? `$${budget}` : "—"}</div>
        </div>
      </div>

      <button
        onClick={onEdit}
        className="mt-6 w-full py-2 rounded-lg border border-slate-300 text-sm text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition shadow-sm"
      >
        Edit
      </button>
    </aside>
  );
}

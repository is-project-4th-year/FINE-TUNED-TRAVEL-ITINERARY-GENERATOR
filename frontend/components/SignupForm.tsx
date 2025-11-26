// frontend/components/SignupForm.tsx
"use client";

import { useState } from "react";
import { useAuth } from "@/store/authStore";
import { useHydrated } from "@/hooks/useHydrated";
import { useRouter } from "next/navigation";

export default function SignupForm() {
  const hydrated = useHydrated();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const signup = useAuth((s) => s.signup);
  const router = useRouter();

  if (!hydrated) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const res = await signup(email.trim(), password);
    setBusy(false);
    if (!res.ok) {
      setError(res.message || "Signup failed");
      return;
    }
    router.push("/auth/signin");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-md bg-white rounded-xl p-8 shadow"
    >
      <h2 className="text-2xl font-semibold mb-6 text-center">
        Create account
      </h2>

      <label className="block mb-3">
        <input
          className="w-full p-3 rounded-lg border border-slate-200 placeholder:text-slate-400"
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
        />
      </label>

      <label className="block mb-3">
        <input
          className="w-full p-3 rounded-lg border border-slate-200 placeholder:text-slate-400"
          placeholder="Password (6+ chars)"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="new-password"
        />
      </label>

      {error && <div className="text-red-600 mb-3">{error}</div>}

      <button
        type="submit"
        disabled={busy}
        className="w-full py-3 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 disabled:opacity-60"
      >
        {busy ? "Creating..." : "Sign Up"}
      </button>

      <div className="mt-4 text-center">
        <a href="/auth/signin" className="text-emerald-600 hover:underline">
          Already have an account? Sign in
        </a>
      </div>
    </form>
  );
}

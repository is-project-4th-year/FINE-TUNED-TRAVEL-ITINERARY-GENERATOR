// frontend/components/LoginForm.tsx
"use client";

import { useState } from "react";
import { useAuth } from "@/store/authStore";
import { useHydrated } from "@/hooks/useHydrated";
import { useRouter } from "next/navigation";

export default function LoginForm() {
  const hydrated = useHydrated();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useAuth((s) => s.login);
  const router = useRouter();

  if (!hydrated) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const result = await login(email.trim().toLowerCase(), password);
    setBusy(false);
    if (!result.ok) {
      setError(result.message || "Login failed");
      return;
    }
    // successful login: push to home; middleware will accept because store set cookie
    router.push("/");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-md bg-white rounded-xl p-8 shadow"
    >
      <h2 className="text-2xl font-semibold mb-6 text-center">Sign In</h2>

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
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
      </label>

      {error && <div className="text-red-600 mb-3">{error}</div>}

      <button
        type="submit"
        disabled={busy}
        className="w-full py-3 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 disabled:opacity-60"
      >
        {busy ? "Signing in…" : "Sign In"}
      </button>

      <div className="mt-4 text-center">
        <a href="/auth/signup" className="text-emerald-600 hover:underline">
          Don't have an account? Sign Up
        </a>
      </div>
    </form>
  );
}

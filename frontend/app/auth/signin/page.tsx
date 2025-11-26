// frontend/app/auth/signin/page.tsx
"use client";

import LoginForm from "@/components/LoginForm";
import { useHydrated } from "@/hooks/useHydrated";

export default function SignInPage() {
  const hydrated = useHydrated();
  if (!hydrated) return null;

  return (
    <div className="min-h-screen flex items-center justify-center bg-emerald-50">
      <LoginForm />
    </div>
  );
}

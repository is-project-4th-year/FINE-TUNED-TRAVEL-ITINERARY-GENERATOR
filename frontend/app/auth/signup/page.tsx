// frontend/app/auth/signup/page.tsx
"use client";

import SignupForm from "@/components/SignupForm";
import { useHydrated } from "@/hooks/useHydrated";

export default function SignUpPage() {
  const hydrated = useHydrated();
  if (!hydrated) return null;

  return (
    <div className="min-h-screen flex items-center justify-center bg-emerald-50">
      <SignupForm />
    </div>
  );
}

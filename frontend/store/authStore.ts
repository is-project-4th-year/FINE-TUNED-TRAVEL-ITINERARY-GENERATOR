"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

type UserRecord = {
  email: string;
  password: string;
};

type AuthState = {
  isLoggedIn: boolean;
  userEmail: string | null;
  users: UserRecord[];
  signup(
    email: string,
    password: string
  ): Promise<{ ok: boolean; message?: string }>;
  login(
    email: string,
    password: string
  ): Promise<{ ok: boolean; message?: string }>;
  logout(): void;
  setIsLoggedIn(v: boolean): void;
};

function setAuthCookie() {
  if (typeof document !== "undefined") {
    document.cookie = "tp_auth=true; path=/;";
  }
}

function clearAuthCookie() {
  if (typeof document !== "undefined") {
    document.cookie = "tp_auth=; Max-Age=0; path=/;";
  }
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      isLoggedIn: false,
      userEmail: null,
      users: [],

      signup: async (email, password) => {
        email = email.trim().toLowerCase();

        if (!email || !password)
          return { ok: false, message: "Missing fields" };

        if (password.length < 6)
          return { ok: false, message: "Password too short" };

        const { users } = get();
        if (users.find((u) => u.email === email)) {
          return { ok: false, message: "Email already registered" };
        }

        set({
          users: [...users, { email, password }],
          isLoggedIn: true,
          userEmail: email,
        });

        setAuthCookie();
        return { ok: true };
      },

      login: async (email, password) => {
        email = email.trim().toLowerCase();
        const { users } = get();
        const user = users.find((u) => u.email === email);

        await new Promise((res) => setTimeout(res, 150));

        if (!user || user.password !== password) {
          return { ok: false, message: "Invalid credentials" };
        }

        set({ isLoggedIn: true, userEmail: email });
        setAuthCookie();
        return { ok: true };
      },

      logout: () => {
        set({ isLoggedIn: false, userEmail: null });
        clearAuthCookie();
      },
      setIsLoggedIn: (v: boolean) => set({ isLoggedIn: v }),
    }),
    {
      name: "travelplanner-auth",

      // 🔥 FIX FOR NEXT.JS HOOK ORDER ERRORS:
      storage: createJSONStorage(() => localStorage),

      // 🔥 prevent hydration mismatch
      skipHydration: true,
    }
  )
);

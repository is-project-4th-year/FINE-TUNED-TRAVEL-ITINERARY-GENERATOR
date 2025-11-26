"use client";

export const AUTH_USER_KEY = "travelplanner_user";
export const AUTH_COOKIE = "tp_auth";

export function signUp(email: string, password: string) {
  const user = { email, password };
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function authenticate(email: string, password: string): boolean {
  const saved = localStorage.getItem(AUTH_USER_KEY);
  if (!saved) return false;

  const user = JSON.parse(saved);
  if (user.email === email && user.password === password) {
    document.cookie = `${AUTH_COOKIE}=true; path=/;`;
    return true;
  }
  return false;
}

export function isLoggedIn(): boolean {
  if (typeof document === "undefined") return false;
  return document.cookie.includes(`${AUTH_COOKIE}=true`);
}

export function logout() {
  document.cookie = `${AUTH_COOKIE}=; Max-Age=0; path=/;`; // Delete cookie
}

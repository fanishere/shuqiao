// Server-only helper (ADR 0001): never import from a client component.
// The refresh cookie is httpOnly, so its value only ever exists server-side.
import { cookies } from "next/headers";

export const REFRESH_COOKIE = "shuqiao_refresh";

export function apiBaseUrl(): string {
  return process.env.API_BASE_URL ?? "http://localhost:8000";
}

type CookieOptions = {
  httpOnly: true;
  path: "/";
  sameSite: "lax";
  secure: boolean;
  maxAge: number;
};

export function refreshCookieOptions(): CookieOptions {
  return {
    httpOnly: true,
    path: "/",
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    // Mirrors REFRESH_TOKEN_TTL in app/auth.py (7 days).
    maxAge: 7 * 24 * 60 * 60,
  };
}

/** Only callable from a Route Handler or Server Function. */
export async function setRefreshCookie(token: string): Promise<void> {
  const store = await cookies();
  store.set(REFRESH_COOKIE, token, refreshCookieOptions());
}

export type Session = {
  accessToken: string;
  /** Set-Cookie instruction for the rotated refresh token; Server Components cannot set cookies themselves. */
  setCookie?: { name: string; value: string; options: CookieOptions };
};

/**
 * Silent re-auth: exchange the refresh cookie for a fresh access token.
 * Returns null when there is no cookie or the API rejects it.
 */
export async function getSession(): Promise<Session | null> {
  const store = await cookies();
  const token = store.get(REFRESH_COOKIE)?.value;
  if (!token) return null;

  try {
    const res = await fetch(`${apiBaseUrl()}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: token }),
      cache: "no-store",
    });
    if (!res.ok) return null;
    const data: { access_token?: string; refresh_token?: string } = await res.json();
    if (!data.access_token) return null;
    return {
      accessToken: data.access_token,
      setCookie: data.refresh_token
        ? { name: REFRESH_COOKIE, value: data.refresh_token, options: refreshCookieOptions() }
        : undefined,
    };
  } catch {
    return null;
  }
}

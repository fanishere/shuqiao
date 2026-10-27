import { NextRequest } from "next/server";

import { apiBaseUrl, setRefreshCookie } from "@/lib/auth";
import type { LoginResponse } from "@/lib/auth-types";

export async function POST(request: NextRequest): Promise<Response> {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "invalid_request" }, { status: 400 });
  }

  const { username, password } = (body ?? {}) as Record<string, unknown>;
  if (typeof username !== "string" || typeof password !== "string" || !username || !password) {
    return Response.json({ error: "invalid_request" }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiBaseUrl()}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
      cache: "no-store",
    });
  } catch {
    return Response.json({ error: "unavailable" }, { status: 502 });
  }

  if (upstream.status === 401) {
    return Response.json({ error: "invalid_credentials" }, { status: 401 });
  }
  if (!upstream.ok) {
    return Response.json({ error: "unavailable" }, { status: 502 });
  }

  const tokens: LoginResponse & { refresh_token?: string } = await upstream.json();
  if (!tokens.access_token || !tokens.token_type || !tokens.refresh_token) {
    return Response.json({ error: "unavailable" }, { status: 502 });
  }

  await setRefreshCookie(tokens.refresh_token);
  // The refresh token stays in the httpOnly cookie; the browser never sees it.
  return Response.json({ access_token: tokens.access_token, token_type: tokens.token_type });
}

import { NextRequest } from "next/server";

import { apiBaseUrl } from "@/lib/auth";

export async function POST(request: NextRequest): Promise<Response> {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "invalid_request" }, { status: 400 });
  }

  const { username, password } = (body ?? {}) as Record<string, unknown>;
  if (
    typeof username !== "string" ||
    typeof password !== "string" ||
    !username.trim() ||
    !password
  ) {
    return Response.json({ error: "invalid_request" }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiBaseUrl()}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: username.trim(), password }),
      cache: "no-store",
    });
  } catch {
    return Response.json({ error: "unavailable" }, { status: 502 });
  }

  if (upstream.status === 409) {
    return Response.json({ error: "username_taken" }, { status: 409 });
  }
  if (upstream.status === 422) {
    const data: { detail?: unknown } = await upstream.json().catch(() => ({}));
    const fields: Record<string, string> = {};
    if (Array.isArray(data.detail)) {
      for (const item of data.detail) {
        const loc = (item as { loc?: unknown } | null)?.loc;
        const msg = (item as { msg?: unknown } | null)?.msg;
        if (Array.isArray(loc) && typeof msg === "string") {
          const field = loc[loc.length - 1];
          if (field === "username" || field === "password") {
            fields[field] = msg;
          }
        }
      }
    }
    return Response.json({ error: "invalid_request", fields }, { status: 400 });
  }
  if (!upstream.ok) {
    return Response.json({ error: "unavailable" }, { status: 502 });
  }

  const data: { username?: string } = await upstream.json().catch(() => ({}));
  if (!data.username) {
    return Response.json({ error: "unavailable" }, { status: 502 });
  }
  return Response.json({ username: data.username }, { status: 201 });
}

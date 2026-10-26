import { Suspense } from "react";

const API_URL = process.env.API_URL ?? "http://localhost:8010";

type Health = { status?: string };

async function getHealth(): Promise<Health | null> {
  try {
    const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as Health;
  } catch {
    return null;
  }
}

async function ApiStatus() {
  const health = await getHealth();
  return (
    <p>
      API:{" "}
      {health === null ? (
        <span style={{ color: "#b00" }}>unreachable at {API_URL}</span>
      ) : (
        <span style={{ color: "#080" }}>{JSON.stringify(health)}</span>
      )}
    </p>
  );
}

export default function Home() {
  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Shuqiao 树桥</h1>
      <p>Chinese learning app — frontend scaffold (SHU-31).</p>
      <Suspense fallback={<p>API: checking…</p>}>
        <ApiStatus />
      </Suspense>
    </main>
  );
}

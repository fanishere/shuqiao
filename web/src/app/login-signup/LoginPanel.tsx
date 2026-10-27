"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import PasswordInput from "@/components/PasswordInput";
import styles from "./LoginPanel.module.css";

import type { LoginResponse } from "@/lib/auth-types";

// Access token lives in memory only (ADR 0001); never persisted.
let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

type FormState =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "error"; message: string }
  | { kind: "success" };

export default function LoginPanel({ defaultUsername = "" }: { defaultUsername?: string }) {
  const router = useRouter();
  const [username, setUsername] = useState(defaultUsername);
  const [password, setPassword] = useState("");
  const [state, setState] = useState<FormState>({ kind: "idle" });
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string }>({});

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errors: { username?: string; password?: string } = {};
    if (!username.trim()) errors.username = "Enter your username.";
    if (!password.trim()) errors.password = "Enter your password.";
    if (errors.username || errors.password) {
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});
    setState({ kind: "submitting" });
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (res.status === 401) {
        setState({ kind: "error", message: "Incorrect username or password." });
        return;
      }
      if (!res.ok) {
        setState({ kind: "error", message: "Something went wrong. Please try again." });
        return;
      }
      const data: LoginResponse = await res.json();
      accessToken = data.access_token;
      setState({ kind: "success" });
      router.push("/");
    } catch {
      setState({ kind: "error", message: "Something went wrong. Please try again." });
    }
  }

  const busy = state.kind === "submitting" || state.kind === "success";

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="username">
          Username
        </label>
        <input
          id="username"
          className={styles.input}
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Your username"
          autoComplete="username"
          disabled={busy}
        />
        {fieldErrors.username && (
          <p className={styles.fieldError}>{fieldErrors.username}</p>
        )}
      </div>

      <PasswordInput
        id="password"
        label="Password"
        value={password}
        onChange={setPassword}
        disabled={busy}
      />
      {fieldErrors.password && (
        <p className={styles.fieldError}>{fieldErrors.password}</p>
      )}

      <div className={styles.forgotRow}>
        <a className={styles.forgot} title="coming soon" aria-disabled="true">
          Forgot password?
        </a>
      </div>

      {state.kind === "error" && (
        <p className={styles.error} role="alert">
          {state.message}
        </p>
      )}

      <button type="submit" className={styles.submit} disabled={busy}>
        Log in
      </button>
    </form>
  );
}

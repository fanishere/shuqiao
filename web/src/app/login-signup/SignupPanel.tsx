"use client";

import { useState } from "react";

import PasswordInput from "@/components/PasswordInput";
import styles from "./SignupPanel.module.css";

type FormState =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "error"; message: string }
  | { kind: "success" };

type FieldErrors = { username?: string; password?: string };

type Props = {
  onSignedUp: (username: string) => void;
};

function validate(username: string, password: string): FieldErrors {
  const errors: FieldErrors = {};
  if (!username.trim()) errors.username = "Enter a username.";
  if (!password.trim()) errors.password = "Enter a password.";
  else if (password.length < 8)
    errors.password = "Use at least 8 characters.";
  return errors;
}

export default function SignupPanel({ onSignedUp }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [state, setState] = useState<FormState>({ kind: "idle" });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errors = validate(username, password);
    if (errors.username || errors.password) {
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});
    setState({ kind: "submitting" });
    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      if (res.status === 409) {
        setState({ kind: "error", message: "That username is already taken." });
        return;
      }
      if (res.status === 400) {
        const data: { error?: string; fields?: FieldErrors } = await res.json();
        if (data.fields && (data.fields.username || data.fields.password)) {
          setFieldErrors(data.fields);
          setState({ kind: "idle" });
        } else {
          setState({ kind: "error", message: "Please check your entries and try again." });
        }
        return;
      }
      if (!res.ok) {
        setState({ kind: "error", message: "Something went wrong. Please try again." });
        return;
      }
      const data: { username?: string } = await res.json();
      setState({ kind: "success" });
      onSignedUp(data.username ?? username.trim());
    } catch {
      setState({ kind: "error", message: "Something went wrong. Please try again." });
    }
  }

  const busy = state.kind === "submitting" || state.kind === "success";

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="signup-username">
          Username
        </label>
        <input
          id="signup-username"
          className={styles.input}
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Pick a username"
          autoComplete="username"
          disabled={busy}
        />
        {fieldErrors.username && (
          <p className={styles.fieldError}>{fieldErrors.username}</p>
        )}
      </div>

      <PasswordInput
        id="signup-password"
        label="Password"
        value={password}
        onChange={setPassword}
        disabled={busy}
        autoComplete="new-password"
      />
      <p className={styles.hint}>Use at least 8 characters.</p>
      {fieldErrors.password && (
        <p className={styles.fieldError}>{fieldErrors.password}</p>
      )}

      {state.kind === "error" && (
        <p className={styles.error} role="alert">
          {state.message}
        </p>
      )}

      <button type="submit" className={styles.submit} disabled={busy}>
        Create account
      </button>

      <p className={styles.legal}>
        By creating an account you agree to our{" "}
        <a className={styles.legalLink} href="/terms">
          Terms
        </a>{" "}
        and{" "}
        <a className={styles.legalLink} href="/privacy">
          Privacy Policy
        </a>
        .
      </p>
    </form>
  );
}

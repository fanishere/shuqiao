"use client";

import { useState } from "react";

import LoginPanel from "./LoginPanel";
import TabToggle, { type Tab } from "@/components/TabToggle";
import styles from "./page.module.css";

export default function LoginSignupPage() {
  const [tab, setTab] = useState<Tab>("login");

  return (
    <main className={styles.page}>
      <div className={styles.header}>
        <div className={styles.brand}>
          <span className={styles.logo}>词</span>
          <span className={styles.wordmark}>SHUQIAO</span>
        </div>
        <h1 className={styles.heading}>Welcome back</h1>
        <p className={styles.subtitle}>Log in to pick up where you left off.</p>
      </div>

      <TabToggle active={tab} onChange={setTab} />

      {tab === "login" ? (
        <LoginPanel />
      ) : (
        <div className={styles.signupStub}>
          <p className={styles.signupNote}>
            Sign-up is on its way. Switch to <strong>Log in</strong> if you already have an account.
          </p>
          <button type="button" className={styles.submit} disabled title="coming soon">
            Sign up
          </button>
        </div>
      )}
    </main>
  );
}

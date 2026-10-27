"use client";

import { useState } from "react";

import LoginPanel from "./LoginPanel";
import SignupPanel from "./SignupPanel";
import TabToggle, { type Tab } from "@/components/TabToggle";
import styles from "./page.module.css";

const COPY: Record<Tab, { heading: string; subtitle: string }> = {
  login: {
    heading: "Welcome back",
    subtitle: "Log in to pick up where you left off.",
  },
  signup: {
    heading: "Create your account",
    subtitle: "Save words, track your HSK progress and review anywhere.",
  },
};

export default function LoginSignupPage() {
  const [tab, setTab] = useState<Tab>("login");
  const [loginUsername, setLoginUsername] = useState("");
  const { heading, subtitle } = COPY[tab];

  return (
    <main className={styles.page}>
      <div className={styles.header}>
        <div className={styles.brand}>
          <span className={styles.logo}>词</span>
          <span className={styles.wordmark}>SHUQIAO</span>
        </div>
        <h1 className={styles.heading}>{heading}</h1>
        <p className={styles.subtitle}>{subtitle}</p>
      </div>

      <div className={styles.toggleWrap}>
        <TabToggle active={tab} onChange={setTab} />
      </div>

      {tab === "login" ? (
        <LoginPanel key={loginUsername} defaultUsername={loginUsername} />
      ) : (
        <SignupPanel
          onSignedUp={(username) => {
            setLoginUsername(username);
            setTab("login");
          }}
        />
      )}
    </main>
  );
}

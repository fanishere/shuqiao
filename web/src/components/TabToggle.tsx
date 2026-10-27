"use client";

import styles from "./TabToggle.module.css";

export type Tab = "login" | "signup";

type Props = {
  active: Tab;
  onChange: (tab: Tab) => void;
};

const TABS: { id: Tab; label: string }[] = [
  { id: "login", label: "Log in" },
  { id: "signup", label: "Sign up" },
];

export default function TabToggle({ active, onChange }: Props) {
  return (
    <div className={styles.track} role="tablist">
      {TABS.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          role="tab"
          aria-selected={active === id}
          className={active === id ? `${styles.tab} ${styles.active}` : styles.tab}
          onClick={() => onChange(id)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

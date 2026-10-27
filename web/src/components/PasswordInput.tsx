"use client";

import { useState } from "react";
import styles from "./PasswordInput.module.css";

type Props = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  autoComplete?: string;
};

export default function PasswordInput({ id, label, value, onChange, disabled, autoComplete }: Props) {
  const [visible, setVisible] = useState(false);

  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={id}>
        {label}
      </label>
      <div className={styles.wrapper}>
        <input
          id={id}
          className={styles.input}
          type={visible ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Your password"
          autoComplete={autoComplete ?? "current-password"}
          disabled={disabled}
        />
        <button
          type="button"
          className={styles.toggle}
          onClick={() => setVisible((v) => !v)}
          aria-pressed={visible}
          disabled={disabled}
        >
          {visible ? "Hide" : "Show"}
        </button>
      </div>
    </div>
  );
}

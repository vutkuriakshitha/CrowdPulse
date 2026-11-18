"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, login } from "@/services/auth";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (getToken()) {
      router.replace("/");
      return;
    }
    const id = window.requestAnimationFrame(() => setReady(true));
    return () => window.cancelAnimationFrame(id);
  }, [router]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username.trim(), password);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell relative min-h-screen overflow-hidden">
      <div className="login-atmosphere pointer-events-none absolute inset-0" aria-hidden />
      <div className="pointer-events-none absolute inset-0 grid-fade opacity-[0.22]" aria-hidden />
      <div className="fx-atmosphere" aria-hidden>
        <span className="fx-orb fx-orb-a" />
        <span className="fx-orb fx-orb-b" />
        <span className="fx-orb fx-orb-c" />
      </div>

      <div
        className={`relative mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 py-14 transition-all duration-700 ease-out ${
          ready ? "translate-y-0 opacity-100" : "translate-y-3 opacity-0"
        }`}
      >
        <header className="mb-9">
          <p
            className={`font-mono text-[11px] uppercase tracking-[0.28em] text-accent transition-all delay-100 duration-700 ${
              ready ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
            }`}
          >
            Telangana · Venue Control
          </p>
          <h1
            className={`mt-3 text-5xl font-semibold tracking-tight text-ink md:text-6xl transition-all delay-150 duration-700 ${
              ready ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
            }`}
          >
            CrowdPulse
          </h1>
          <p
            className={`mt-4 max-w-sm text-[15px] leading-relaxed text-mist transition-all delay-200 duration-700 ${
              ready ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
            }`}
          >
            Sign in to the operations console for live crowd risk and decision support.
          </p>
        </header>

        <form
          onSubmit={onSubmit}
          className={`space-y-5 border-t border-line/80 pt-8 transition-all delay-300 duration-700 ${
            ready ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
          }`}
        >
          <div>
            <label htmlFor="username" className="mb-2 block font-mono text-[11px] uppercase tracking-wider text-mist">
              Username
            </label>
            <input
              id="username"
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="login-input w-full border-b border-line bg-transparent px-0 py-3 text-[15px] text-ink outline-none placeholder:text-mist/40 focus:border-accent"
              placeholder="tsp.operator"
              required
              autoFocus
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-2 block font-mono text-[11px] uppercase tracking-wider text-mist">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="login-input w-full border-b border-line bg-transparent px-0 py-3 text-[15px] text-ink outline-none placeholder:text-mist/40 focus:border-accent"
              placeholder="Enter password"
              required
            />
          </div>

          {error && (
            <p className="font-mono text-sm text-signal-red" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="login-cta mt-2 w-full bg-accent px-4 py-3.5 text-sm font-semibold tracking-wide text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-55"
          >
            {loading ? "Authenticating…" : "Sign in"}
          </button>
        </form>

        <footer className="mt-10 font-mono text-[11px] leading-relaxed text-mist/70">
          <p>Authorized control-room personnel only</p>
          <p className="mt-1">Hyderabad · Asia/Kolkata</p>
        </footer>
      </div>
    </div>
  );
}

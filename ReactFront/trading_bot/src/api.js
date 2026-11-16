import { useState, useEffect, useCallback, useRef } from 'react';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_URL = API_URL.replace(/^http/, 'ws') + '/ws/stream';

/** JSON request helper. Throws on network / HTTP errors. */
export async function api(path, { method = 'GET', body, timeout = 15000 } = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeout);
  try {
    const res = await fetch(`${API_URL}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(t);
  }
}

/** Polls an endpoint. Keeps the last good data on failure and exposes `error`. */
export function usePolling(path, ms = 10000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const alive = useRef(true);

  const load = useCallback(async () => {
    try {
      const d = await api(path);
      if (!alive.current) return;
      setData(d);
      setError(null);
    } catch (e) {
      if (alive.current) setError(e.name === 'AbortError' ? 'Request timed out' : 'Cannot reach the trading engine');
    } finally {
      if (alive.current) setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    alive.current = true;
    setLoading(true);
    load();
    const id = ms ? setInterval(load, ms) : null;
    return () => { alive.current = false; if (id) clearInterval(id); };
  }, [load, ms]);

  return { data, error, loading, reload: load };
}

export const money = (v, d = 2) =>
  v == null || Number.isNaN(v) ? '—' : `${v < 0 ? '-' : ''}$${Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })}`;
export const signedMoney = (v, d = 2) =>
  v == null || Number.isNaN(v) ? '—' : `${v >= 0 ? '+' : '-'}$${Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })}`;
export const pct = (v, d = 1) => (v == null || Number.isNaN(v) ? '—' : `${(v * 100).toFixed(d)}%`);
export const signedPct = (v, d = 2) => (v == null || Number.isNaN(v) ? '—' : `${v >= 0 ? '+' : ''}${(v * 100).toFixed(d)}%`);

export function ago(iso) {
  if (!iso) return '—';
  const s = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export function duration(sec) {
  if (sec == null) return '—';
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60);
  return h ? `${h}h ${m}m` : `${m}m`;
}

export const pnlClass = (v) => (v > 0 ? 'text-[var(--color-profit)]' : v < 0 ? 'text-[var(--color-loss)]' : 'text-[var(--color-surface-300)]');

import React, { useState, useEffect } from 'react';
import { Play, Square, AlertTriangle, RotateCcw, Cpu, Clock, ShieldAlert } from 'lucide-react';
import { pct, ago, duration } from '../api';
import CapitalCard from './CapitalCard';

const CARD = 'rounded-2xl border border-white/5 bg-gradient-to-b from-[var(--color-surface-850)]/80 to-[var(--color-surface-900)]/60 backdrop-blur-xl';
const NAMES = { TrendMomentum: 'Trend + Momentum', TrendMomentumLS: 'Trend + Momentum L/S', PairsTrading: 'Pairs Trading' };
const PALETTE = ['#f59e0b', '#38bdf8', '#a78bfa', '#34d399', '#fb7185', '#fbbf24', '#22d3ee', '#c084fc'];

function Meter({ label, value, limit, right }) {
  const frac = limit ? Math.min(Math.max(value / limit, 0), 1) : 0;
  const color = frac > 0.8 ? 'var(--color-loss)' : frac > 0.5 ? 'var(--color-gold-500)' : 'var(--color-profit)';
  return (
    <div>
      <div className="flex justify-between text-[10px] mb-1">
        <span className="uppercase tracking-wider text-[var(--color-surface-500)]">{label}</span>
        <span className="font-mono text-[var(--color-surface-400)]">{right}</span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--color-surface-800)] overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${frac * 100}%`, background: color }} />
      </div>
    </div>
  );
}

/** Sticky control + situation panel: what the bot is doing, how it is allocated, how risky it is. */
export default function EnginePanel({ status, isConnected, snapshotAt, onStart, onStop, onLiquidate, onReset, onChangeStrategy, onNotice }) {
  const running = !!status?.running;
  const positions = status?.positions || [];
  const risk = status?.risk_metrics || {};
  const lim = risk.limits || {};
  const weights = Object.entries(status?.portfolio?.weights || {});
  const gross = weights.reduce((a, [, w]) => a + Math.abs(w), 0);

  // live countdown to the next 4h bar
  const [now, setNow] = useState(Date.now());
  useEffect(() => { const id = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(id); }, []);
  const next = status?.next_bar_seconds;
  const remaining = next != null && snapshotAt ? Math.max(0, next - Math.floor((now - snapshotAt) / 1000)) : null;

  const dailyUsed = Math.min(risk.daily_limit_used || 0, 1);

  return (
    <div className="flex flex-col gap-3 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:overflow-y-auto lg:pr-1 engine-scroll">
      <div className={`${CARD} p-5 flex flex-col gap-4`}>
        {/* header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className={`relative flex h-2.5 w-2.5`}>
              {running && <span className="absolute inline-flex h-full w-full rounded-full bg-[var(--color-profit)] opacity-60 animate-ping" />}
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${running ? 'bg-[var(--color-profit)]' : isConnected ? 'bg-[var(--color-surface-600)]' : 'bg-[var(--color-loss)]'}`} />
            </span>
            <span className="text-[11px] font-heading font-bold tracking-[0.18em] text-white">
              {!isConnected ? 'OFFLINE' : running ? 'TRADING' : 'STANDBY'}
            </span>
          </div>
          <button onClick={onChangeStrategy} className="text-[10px] uppercase tracking-wider text-[var(--color-gold-400)] hover:text-[var(--color-gold-300)] cursor-pointer flex items-center gap-1">
            <Cpu size={11} /> {NAMES[status?.strategy] || status?.strategy || 'Strategy'}
          </button>
        </div>

        {/* primary action */}
        {running ? (
          <button onClick={onStop} className="w-full py-3 rounded-xl font-heading font-bold text-xs tracking-[0.18em] flex items-center justify-center gap-2 bg-[var(--color-surface-800)] hover:bg-[var(--color-loss)] text-[var(--color-surface-200,#e2e8f0)] hover:text-white border border-white/10 hover:border-[var(--color-loss)] transition-all cursor-pointer">
            <Square size={13} fill="currentColor" /> STOP TRADING
          </button>
        ) : (
          <button onClick={onStart} disabled={!isConnected}
            className="w-full py-3 rounded-xl font-heading font-bold text-xs tracking-[0.18em] flex items-center justify-center gap-2 bg-gradient-to-r from-[var(--color-profit)] to-emerald-400 text-black hover:brightness-110 transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed shadow-[0_0_24px_-6px_rgba(16,185,129,0.6)]">
            <Play size={13} fill="currentColor" /> START TRADING
          </button>
        )}

        {/* narrative */}
        <div className="rounded-xl bg-[var(--color-surface-950)]/50 border border-white/5 px-3.5 py-3">
          <p className="text-[9px] uppercase tracking-[0.16em] text-[var(--color-surface-500)] mb-1.5">What's happening</p>
          <p className="text-[12px] leading-relaxed text-[var(--color-surface-200,#e2e8f0)] text-white/90">{status?.summary || 'Waiting for data…'}</p>
        </div>

        {/* timing */}
        <div className="flex items-center justify-between text-[10px] font-mono text-[var(--color-surface-500)]">
          <span className="flex items-center gap-1.5"><Clock size={11} /> {running ? `checked ${ago(status?.last_cycle)}` : status?.analysis_at ? `scanned ${ago(status.analysis_at)}` : '—'}</span>
          {remaining != null && <span>next 4h bar <span className="text-white">{duration(remaining)}</span></span>}
        </div>
      </div>

      <CapitalCard capital={status?.capital} isConnected={isConnected} onNotice={onNotice} />

      {/* allocation */}
      <div className={`${CARD} p-5`}>
        <div className="flex items-center justify-between mb-3">
          <span className="text-[10px] font-heading font-bold tracking-[0.16em] text-[var(--color-surface-400)]">TARGET ALLOCATION</span>
          <span className="text-[10px] font-mono text-[var(--color-surface-500)]">{pct(gross, 0)} of budget</span>
        </div>
        <div className="h-2.5 rounded-full bg-[var(--color-surface-800)] overflow-hidden flex">
          {weights.map(([sym, w], i) => (
            <div key={sym} title={`${sym} ${(w * 100).toFixed(0)}%`} className="h-full first:rounded-l-full"
              style={{ width: `${Math.abs(w) * 100}%`, background: PALETTE[i % PALETTE.length], opacity: w < 0 ? 0.65 : 1 }} />
          ))}
        </div>
        {weights.length === 0 ? (
          <p className="mt-3 text-[11px] text-[var(--color-surface-500)]">100% cash — no coin qualifies right now.</p>
        ) : (
          <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5">
            {weights.map(([sym, w], i) => (
              <li key={sym} className="flex items-center justify-between text-[11px] font-mono">
                <span className="flex items-center gap-1.5 text-[var(--color-surface-300)]">
                  <span className="w-2 h-2 rounded-sm" style={{ background: PALETTE[i % PALETTE.length] }} />
                  {sym.replace('/USDT', '')}{w < 0 && <span className="text-[8px] text-[var(--color-loss)] font-bold">SHORT</span>}
                </span>
                <span className="text-white tabular-nums">{Math.abs(w * 100).toFixed(0)}%</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* risk */}
      <div className={`${CARD} p-5 flex flex-col gap-3.5`}>
        <div className="flex items-center gap-2 text-[10px] font-heading font-bold tracking-[0.16em] text-[var(--color-surface-400)]"><ShieldAlert size={12} /> RISK</div>
        {risk.halted_reason && (
          <p className="text-[11px] text-[var(--color-loss)] bg-[var(--color-loss-dim)] border border-[var(--color-loss)]/30 rounded-lg px-3 py-2">{risk.halted_reason}</p>
        )}
        <Meter label="Drawdown" value={risk.current_drawdown || 0} limit={lim.drawdown || 0.3}
          right={`${pct(risk.current_drawdown || 0, 2)} / ${pct(lim.drawdown || 0.3, 0)}`} />
        <Meter label="Daily loss" value={dailyUsed} limit={1} right={`${pct(dailyUsed, 0)} of ${pct(lim.daily || 0.03, 1)} limit`} />
      </div>

      {/* danger actions */}
      <div className="flex gap-2">
        <button onClick={onLiquidate} disabled={!positions.length || !isConnected}
          className="flex-1 py-2.5 rounded-xl text-[10px] font-heading font-bold tracking-[0.16em] flex items-center justify-center gap-1.5 border transition-all cursor-pointer disabled:opacity-35 disabled:cursor-not-allowed bg-[var(--color-loss-dim)] border-[var(--color-loss)]/30 text-[var(--color-loss)] hover:bg-[var(--color-loss)] hover:text-white">
          <AlertTriangle size={12} /> CLOSE ALL
        </button>
        <button onClick={onReset} disabled={running || !isConnected} title="Reset paper account"
          className="px-3.5 py-2.5 rounded-xl border border-white/10 text-[var(--color-surface-500)] hover:text-white hover:border-white/20 disabled:opacity-35 disabled:cursor-not-allowed cursor-pointer transition-colors">
          <RotateCcw size={13} />
        </button>
      </div>
    </div>
  );
}

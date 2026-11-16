import React, { useState } from 'react';
import { ArrowUp, ArrowDown, Radar, Wallet, ScrollText, Zap, Info, AlertTriangle, XCircle, CheckCircle } from 'lucide-react';
import Tooltip from './Tooltip';
import { money, signedMoney, pct, signedPct, ago, pnlClass } from '../api';

const CARD = 'rounded-2xl border border-white/5 bg-gradient-to-b from-[var(--color-surface-850)]/80 to-[var(--color-surface-900)]/60 backdrop-blur-xl overflow-hidden';
const LEVEL = {
  INFO: { Icon: Info, cls: 'text-[var(--color-surface-400)]' },
  WARNING: { Icon: AlertTriangle, cls: 'text-[var(--color-gold-500)]' },
  ERROR: { Icon: XCircle, cls: 'text-[var(--color-loss)]' },
  SUCCESS: { Icon: CheckCircle, cls: 'text-[var(--color-profit)]' },
};
const Empty = ({ children }) => <div className="py-12 text-center text-xs text-[var(--color-surface-500)]">{children}</div>;
const Th = ({ children, right, tip }) => (
  <th className={`px-4 py-2.5 text-[9px] uppercase tracking-[0.14em] font-medium text-[var(--color-surface-500)] ${right ? 'text-right' : 'text-left'}`}>
    {tip ? <Tooltip content={tip}><span>{children}</span></Tooltip> : children}
  </th>
);

function ScanTable({ scan, onSelect, selected, prices }) {
  const rows = [...scan.rows].sort((a, b) => Math.abs(b.target) - Math.abs(a.target) || a.momentum_rank - b.momentum_rank);
  return (
    <table className="w-full text-[11px]">
      <thead><tr className="border-b border-white/5">
        <Th>Coin</Th><Th right>Price</Th>
        <Th tip="Price above its 40-day moving average.">Trend</Th>
        <Th tip="Share of the three breakout look-backs currently active (green = long, red = short).">Breakout</Th>
        <Th right tip="90-bar return and rank among the 8 coins. The top 3 in an uptrend qualify.">Momentum</Th>
        <Th right>Target</Th>
      </tr></thead>
      <tbody className="divide-y divide-white/5">
        {rows.map(r => {
          const price = prices?.[r.symbol]?.last || r.price;
          return (
            <tr key={r.symbol} onClick={() => onSelect?.(r.symbol)}
              className={`cursor-pointer transition-colors hover:bg-white/[0.03] ${selected === r.symbol ? 'bg-white/[0.04]' : ''}`}>
              <td className="px-4 py-2.5 font-heading font-bold text-white">{r.symbol.replace('/USDT', '')}</td>
              <td className="px-4 py-2.5 text-right font-mono tabular-nums text-[var(--color-surface-300)]">{money(price, price < 10 ? 4 : 2)}</td>
              <td className="px-4 py-2.5">{r.trend_up ? <ArrowUp size={13} className="text-[var(--color-profit)]" /> : <ArrowDown size={13} className="text-[var(--color-loss)]" />}</td>
              <td className="px-4 py-2.5">
                <div className="w-16 h-1.5 rounded-full bg-[var(--color-surface-800)] overflow-hidden">
                  <div className={`h-full ${r.breakout < 0 ? 'bg-[var(--color-loss)]' : 'bg-[var(--color-gold-500)]'}`} style={{ width: `${Math.round(Math.abs(r.breakout) * 100)}%` }} />
                </div>
              </td>
              <td className="px-4 py-2.5 text-right font-mono tabular-nums">
                <span className={r.momentum_pct >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}>{signedPct(r.momentum_pct, 1)}</span>
                <span className="text-[var(--color-surface-500)]"> #{r.momentum_rank}{r.in_top3 ? ' ★' : ''}</span>
              </td>
              <td className={`px-4 py-2.5 text-right font-mono font-bold tabular-nums ${r.target > 0 ? 'text-[var(--color-gold-400)]' : r.target < 0 ? 'text-[var(--color-loss)]' : 'text-[var(--color-surface-600)]'}`}>
                {r.target > 0 ? pct(r.target, 0) : r.target < 0 ? `SHORT ${pct(-r.target, 0)}` : '—'}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function PairGauge({ scan, entry, exit }) {
  const z = scan.z ?? 0;
  const pos = Math.max(0, Math.min(100, 50 + (z / 4) * 50));
  return (
    <div className="p-6 flex flex-col gap-4">
      <p className="text-xs text-[var(--color-surface-300)]">Spread {scan.symbols?.join(' / ')}</p>
      <div className="relative h-2 rounded-full bg-[var(--color-surface-800)]">
        {[-entry, -exit, exit, entry].map(t => <div key={t} className="absolute top-[-3px] w-px h-[14px] bg-[var(--color-surface-600)]" style={{ left: `${50 + (t / 4) * 50}%` }} />)}
        <div className="absolute top-[-5px] w-3 h-[18px] rounded bg-[var(--color-gold-500)] shadow" style={{ left: `calc(${pos}% - 6px)` }} />
      </div>
      <div className="flex justify-between text-[10px] font-mono text-[var(--color-surface-500)]"><span>-4σ</span><span>entry ±{entry}</span><span>0</span><span>entry ±{entry}</span><span>+4σ</span></div>
      <p className="text-sm font-mono text-white">z-score {scan.ready ? z.toFixed(2) : '—'}</p>
    </div>
  );
}

function Positions({ positions, onSelect }) {
  if (!positions.length) return <Empty>No open positions — the account is in cash.</Empty>;
  return (
    <table className="w-full text-[11px]">
      <thead><tr className="border-b border-white/5"><Th>Symbol</Th><Th>Side</Th><Th right>Value</Th><Th right>Entry</Th><Th right>Mark</Th><Th right>P&L</Th></tr></thead>
      <tbody className="divide-y divide-white/5">
        {positions.map(p => {
          const val = p.size * p.mark_price;
          const pnlPct = p.entry_price ? (p.unrealized_pnl / (p.size * p.entry_price)) : 0;
          return (
            <tr key={p.symbol} onClick={() => onSelect?.(p.symbol)} className="cursor-pointer hover:bg-white/[0.03] transition-colors">
              <td className="px-4 py-2.5 font-heading font-bold text-white">{p.symbol.replace('/USDT', '')}</td>
              <td className={`px-4 py-2.5 text-[9px] font-bold uppercase ${p.side === 'long' ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>{p.side}</td>
              <td className="px-4 py-2.5 text-right font-mono tabular-nums text-[var(--color-surface-300)]">{money(val, 0)}</td>
              <td className="px-4 py-2.5 text-right font-mono tabular-nums text-[var(--color-surface-400)]">{money(p.entry_price, p.entry_price < 10 ? 4 : 2)}</td>
              <td className="px-4 py-2.5 text-right font-mono tabular-nums text-[var(--color-surface-300)]">{money(p.mark_price, p.mark_price < 10 ? 4 : 2)}</td>
              <td className={`px-4 py-2.5 text-right font-mono tabular-nums font-bold ${pnlClass(p.unrealized_pnl)}`}>
                {signedMoney(p.unrealized_pnl)} <span className="text-[9px] opacity-70">{signedPct(pnlPct, 2)}</span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function Activity({ events }) {
  if (!events.length) return <Empty>No activity yet</Empty>;
  return (
    <div className="divide-y divide-white/5 max-h-[320px] overflow-y-auto">
      {events.map(e => {
        const { Icon, cls } = LEVEL[e.level] || LEVEL.INFO;
        return (
          <div key={e.id} className="flex gap-3 px-5 py-3">
            <Icon size={14} className={`mt-0.5 shrink-0 ${cls}`} />
            <p className="flex-1 text-[12px] text-white/90 leading-snug">{e.text}</p>
            <span className="text-[10px] font-mono text-[var(--color-surface-500)] whitespace-nowrap">{ago(e.time)}</span>
          </div>
        );
      })}
    </div>
  );
}

function Signals({ signals }) {
  if (!signals.length) return <Empty>No signals yet — they appear when the bot opens or adjusts a position.</Empty>;
  return (
    <div className="divide-y divide-white/5">
      {signals.map((s, i) => (
        <div key={i} className="flex items-center gap-3 px-5 py-2.5">
          <span className={`w-6 h-6 rounded-md flex items-center justify-center ${s.direction === 'long' ? 'bg-[var(--color-profit-dim)] text-[var(--color-profit)]' : 'bg-[var(--color-loss-dim)] text-[var(--color-loss)]'}`}>
            {s.direction === 'long' ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
          </span>
          <span className="text-xs font-heading font-bold text-white w-20">{s.symbol.replace('/USDT', '')}</span>
          <span className="text-[11px] font-mono text-[var(--color-surface-400)] flex-1">{s.rule || ''}</span>
          <span className="text-[11px] font-mono tabular-nums text-[var(--color-surface-300)]">{money(s.price)}</span>
          <span className="text-[10px] font-mono text-[var(--color-surface-500)] w-16 text-right">{s.time}</span>
        </div>
      ))}
    </div>
  );
}

const TABS = [
  { id: 'scan', label: 'Market scan', icon: Radar },
  { id: 'positions', label: 'Positions', icon: Wallet },
  { id: 'activity', label: 'Activity', icon: ScrollText },
  { id: 'signals', label: 'Signals', icon: Zap },
];

export default function InsightTabs({ status, symbol, onSelect, prices }) {
  const [tab, setTab] = useState(() => { try { return localStorage.getItem('insightTab') || 'scan'; } catch { return 'scan'; } });
  const pick = (id) => { setTab(id); try { localStorage.setItem('insightTab', id); } catch { /* ignore */ } };
  const scan = status?.scan;
  const positions = status?.positions || [];
  const counts = { positions: positions.length, activity: (status?.events || []).length, signals: (status?.recent_signals || []).length };

  return (
    <div className={CARD}>
      <div className="flex items-center justify-between border-b border-white/5 px-2 overflow-x-auto">
        <div className="flex">
          {TABS.map(t => (
            <button key={t.id} onClick={() => pick(t.id)}
              className={`relative flex items-center gap-2 px-4 py-3.5 text-[11px] font-heading font-bold tracking-wider cursor-pointer transition-colors whitespace-nowrap ${tab === t.id ? 'text-white' : 'text-[var(--color-surface-500)] hover:text-[var(--color-surface-300)]'}`}>
              <t.icon size={13} className={tab === t.id ? 'text-[var(--color-gold-500)]' : ''} />
              {t.label}
              {counts[t.id] > 0 && <span className="text-[9px] font-mono px-1.5 rounded bg-[var(--color-surface-800)] text-[var(--color-surface-300)]">{counts[t.id]}</span>}
              {tab === t.id && <span className="absolute inset-x-3 -bottom-px h-0.5 rounded bg-[var(--color-gold-500)]" />}
            </button>
          ))}
        </div>
        {tab === 'scan' && scan?.kind === 'portfolio' && (
          <div className="hidden md:flex items-center gap-3 pr-3 text-[10px] font-mono text-[var(--color-surface-500)] whitespace-nowrap">
            <span className={scan.btc_regime_up ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}>BTC {scan.btc_regime_up ? 'uptrend' : 'downtrend'}</span>
            <span>risk scale {pct(scan.vol_scale, 0)}</span>
            <span>updated {ago(status.analysis_at)}</span>
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        {tab === 'scan' && (!scan?.kind
          ? <Empty>Analysing the market… (first scan takes ~10 seconds)</Empty>
          : scan.kind === 'portfolio'
            ? <ScanTable scan={scan} onSelect={onSelect} selected={symbol} prices={prices} />
            : <PairGauge scan={scan} entry={status.pair?.entry ?? 2} exit={status.pair?.exit ?? 0.5} />)}
        {tab === 'positions' && <Positions positions={positions} onSelect={onSelect} />}
        {tab === 'activity' && <Activity events={status?.events || []} />}
        {tab === 'signals' && <Signals signals={status?.recent_signals || []} />}
      </div>
    </div>
  );
}

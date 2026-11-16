import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { usePolling, money, signedMoney, pct, signedPct, pnlClass } from '../api';

const CARD = 'relative overflow-hidden rounded-2xl border border-white/5 bg-gradient-to-b from-[var(--color-surface-850)]/80 to-[var(--color-surface-900)]/60 backdrop-blur-xl';

function Sparkline({ values, up }) {
  if (!values || values.length < 2) {
    return <div className="absolute inset-x-0 bottom-0 h-12 flex items-end"><div className="w-full h-px bg-[var(--color-surface-700)]" /></div>;
  }
  const min = Math.min(...values), max = Math.max(...values), range = max - min || 1;
  const pts = values.map((v, i) => [(i / (values.length - 1)) * 100, 100 - ((v - min) / range) * 70 - 15]);
  const line = pts.map(p => p.join(',')).join(' ');
  const color = up ? 'var(--color-profit)' : 'var(--color-loss)';
  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-x-0 bottom-0 h-16 w-full opacity-90 pointer-events-none">
      <defs>
        <linearGradient id="kpiGrad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={`0,100 ${line} 100,100`} fill="url(#kpiGrad)" />
      <polyline points={line} fill="none" stroke={color} strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

function Tile({ label, children, sub }) {
  return (
    <div className={`${CARD} lg:col-span-2 px-4 py-3.5 flex flex-col justify-between min-h-[132px]`}>
      <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-[var(--color-surface-500)]">{label}</span>
      <div className="mt-1">{children}</div>
      <div className="text-[10px] text-[var(--color-surface-500)] font-mono leading-snug mt-1">{sub}</div>
    </div>
  );
}

export default function KpiRibbon({ status, isConnected }) {
  const { data: analytics } = usePolling('/api/test/analytics?timeframe=all', 20000);

  if (!status) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-12 gap-3">
        <div className={`${CARD} min-h-[132px] animate-pulse col-span-2 lg:col-span-4`} />
        {[0, 1, 2, 3].map(i => <div key={i} className={`${CARD} min-h-[96px] animate-pulse lg:col-span-2`} />)}
        <p className="col-span-full text-xs text-[var(--color-surface-500)]">
          {isConnected ? 'Loading account…' : 'Waiting for the trading engine — start the backend and this fills in automatically.'}
        </p>
      </div>
    );
  }

  const acct = status.account || {};
  const risk = status.risk_metrics || {};
  const daily = status.daily_stats || {};
  const positions = status.positions || [];
  const equity = acct.equity ?? 0;
  const initial = acct.initial_capital || 0;
  const totalPnl = risk.total_pnl ?? equity - initial;
  const ret = initial ? totalPnl / initial : 0;
  const unreal = positions.reduce((a, p) => a + (p.unrealized_pnl || 0), 0);
  const longV = positions.filter(p => p.side === 'long').reduce((a, p) => a + p.size * p.mark_price, 0);
  const shortV = positions.filter(p => p.side === 'short').reduce((a, p) => a + p.size * p.mark_price, 0);
  const gross = equity ? (longV + shortV) / equity : 0;
  const curve = (analytics?.chartData || []).map(d => d.value);
  const up = ret >= 0;
  const Trend = ret > 0 ? ArrowUpRight : ret < 0 ? ArrowDownRight : Minus;
  const winRate = daily.win_rate;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-12 gap-3">
      {/* Hero: equity */}
      <div className={`${CARD} col-span-2 lg:col-span-4 px-5 pt-4 pb-14 min-h-[132px]`}>
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-[var(--color-surface-500)]">Account equity</span>
          <span className="text-[10px] font-mono text-[var(--color-surface-500)]">PAPER</span>
        </div>
        <div className="mt-1 flex items-end gap-3 flex-wrap">
          <span className="text-[34px] leading-none font-heading font-bold text-white tabular-nums tracking-tight">{money(equity)}</span>
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-mono font-bold mb-1 ${up ? 'bg-[var(--color-profit-dim)] text-[var(--color-profit)]' : 'bg-[var(--color-loss-dim)] text-[var(--color-loss)]'}`}>
            <Trend size={12} /> {signedPct(ret)}
          </span>
        </div>
        <p className="mt-2 text-[11px] text-[var(--color-surface-500)] font-mono">Started with {money(initial, 0)} · cash {money(acct.cash ?? 0, 0)}</p>
        <Sparkline values={curve} up={up} />
      </div>

      <Tile label="Total P&L" sub={`Realised ${signedMoney(daily.realized_pnl || 0)} · open ${signedMoney(unreal)}`}>
        <span className={`text-2xl font-heading font-bold tabular-nums ${pnlClass(totalPnl)}`}>{signedMoney(totalPnl)}</span>
      </Tile>

      <Tile label="Today" sub={`${daily.trades || 0} trade${daily.trades === 1 ? '' : 's'} closed`}>
        <span className={`text-2xl font-heading font-bold tabular-nums ${pnlClass(daily.pnl || 0)}`}>{signedMoney(daily.pnl || 0)}</span>
      </Tile>

      <Tile label="Win rate" sub={daily.total_trades ? `${daily.wins}W · ${daily.losses}L · ${daily.total_trades} closed` : 'No closed trades yet'}>
        <div className="flex items-center gap-3">
          <span className={`text-2xl font-heading font-bold tabular-nums ${winRate == null ? 'text-[var(--color-surface-600)]' : winRate >= 0.5 ? 'text-[var(--color-profit)]' : 'text-[var(--color-gold-400)]'}`}>
            {winRate == null ? '—' : pct(winRate, 0)}
          </span>
          {daily.total_trades > 0 && (
            <div className="flex-1 h-1.5 rounded-full bg-[var(--color-loss)]/40 overflow-hidden">
              <div className="h-full bg-[var(--color-profit)]" style={{ width: `${(winRate || 0) * 100}%` }} />
            </div>
          )}
        </div>
      </Tile>

      <Tile label="Exposure" sub={`${positions.length} position${positions.length === 1 ? '' : 's'} · ${shortV > longV ? 'net short' : longV > shortV ? 'net long' : 'flat'}`}>
        <div className="flex items-center gap-3">
          <span className="text-2xl font-heading font-bold tabular-nums text-white">{pct(gross, 0)}</span>
          <div className="flex-1 h-1.5 rounded-full bg-[var(--color-surface-800)] overflow-hidden flex">
            <div className="h-full bg-[var(--color-profit)]" style={{ width: `${Math.min(longV / (equity || 1), 1) * 100}%` }} />
            <div className="h-full bg-[var(--color-loss)]" style={{ width: `${Math.min(shortV / (equity || 1), 1) * 100}%` }} />
          </div>
        </div>
      </Tile>
    </div>
  );
}

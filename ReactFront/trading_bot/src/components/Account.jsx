import React, { useState } from 'react';
import { Wallet, TrendingUp, Receipt, Award, TrendingDown, Gauge, ShieldAlert, SlidersHorizontal, RotateCcw, Loader, CheckCircle2, Circle, Rocket } from 'lucide-react';
import { api, usePolling, money, signedMoney, pct, signedPct, pnlClass } from '../api';

function Stat({ icon: Icon, label, value, cls = 'text-white', sub }) {
  return (
    <div className="bg-[var(--color-surface-900)]/40 backdrop-blur-md border border-[var(--color-surface-800)]/60 rounded-2xl p-5">
      <div className="p-2 rounded-lg bg-[var(--color-surface-800)] border border-[var(--color-surface-700)]/50 w-fit mb-3"><Icon size={16} className="text-[var(--color-gold-500)]" /></div>
      <p className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)] font-medium mb-1">{label}</p>
      <p className={`text-xl font-bold font-mono ${cls}`}>{value}</p>
      {sub && <p className="text-[10px] text-[var(--color-surface-500)] font-mono mt-1">{sub}</p>}
    </div>
  );
}

function LimitBar({ label, used, limit, current }) {
  const frac = Math.min(Math.max(used, 0), 1);
  return (
    <div>
      <div className="flex justify-between text-[11px] mb-1">
        <span className="text-[var(--color-surface-300)]">{label}</span>
        <span className="font-mono text-[var(--color-surface-500)]">{current} · limit {pct(limit, 1)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--color-surface-800)] overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700"
          style={{ width: `${frac * 100}%`, background: frac > 0.8 ? 'var(--color-loss)' : frac > 0.5 ? 'var(--color-gold-500)' : 'var(--color-profit)' }} />
      </div>
    </div>
  );
}

function Readiness() {
  const { data: r } = usePolling('/api/readiness', 20000);
  if (!r) return null;
  const fmt = (c) => c.unit === 'days' ? `${c.value.toFixed(1)} / ${c.target} days`
    : c.unit === 'trades' ? `${c.value} / ${c.target} trades`
    : c.unit === 'pct' ? `${(c.value * 100).toFixed(2)}%`
    : c.unit === 'pct_max' ? `${(c.value * 100).toFixed(1)}% (max ${(c.target * 100).toFixed(0)}%)`
    : `${(c.value || 0).toFixed(2)}x (need ${c.target}x)`;
  return (
    <div className="rounded-3xl border border-white/5 bg-gradient-to-b from-[var(--color-surface-850)]/80 to-[var(--color-surface-900)]/60 overflow-hidden">
      <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between flex-wrap gap-3">
        <h3 className="text-sm font-heading font-bold text-white tracking-widest flex items-center gap-2"><Rocket size={16} className="text-[var(--color-gold-500)]" /> SCALE-UP READINESS</h3>
        <span className={`text-[11px] font-bold px-2.5 py-1 rounded-lg ${r.ready ? 'bg-[var(--color-profit-dim)] text-[var(--color-profit)]' : 'bg-[var(--color-gold-500)]/10 text-[var(--color-gold-400)]'}`}>
          {r.passed} of {r.total} checks passed
        </span>
      </div>
      <div className="p-6 grid grid-cols-1 xl:grid-cols-5 gap-6">
        <div className="xl:col-span-3 flex flex-col gap-3">
          {r.checks.map(c => (
            <div key={c.key} className="flex gap-3">
              {c.pass ? <CheckCircle2 size={18} className="text-[var(--color-profit)] shrink-0 mt-0.5" /> : <Circle size={18} className="text-[var(--color-surface-600)] shrink-0 mt-0.5" />}
              <div className="flex-1 min-w-0">
                <div className="flex justify-between gap-3 text-[12px]"><span className="text-white font-medium">{c.label}</span><span className="font-mono text-[var(--color-surface-400)] whitespace-nowrap">{fmt(c)}</span></div>
                <p className="text-[10px] text-[var(--color-surface-500)] mt-0.5 leading-snug">{c.why}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="xl:col-span-2 rounded-2xl bg-[var(--color-surface-950)]/50 border border-white/5 p-4 flex flex-col gap-3">
          <p className="text-[12px] text-white/90 leading-relaxed">{r.verdict}</p>
          <div className="text-[11px] text-[var(--color-surface-400)] leading-relaxed">
            <p className="font-bold text-[var(--color-surface-300)] mb-1">The ladder</p>
            <ol className="list-decimal pl-4 space-y-0.5">
              <li>Run with a small amount until all checks pass.</li>
              <li>Add the same amount again (2x). Wait for 30 more closed trades.</li>
              <li>Repeat only while the live record keeps matching the tests.</li>
              <li>Never add money you can't afford to lose.</li>
            </ol>
          </div>
          <p className="text-[10px] text-[var(--color-surface-500)] leading-snug">Reference: {r.backtest_reference.note}</p>
        </div>
      </div>
    </div>
  );
}

export default function Account({ data, onOpenSettings, onNotice }) {
  const status = data?.status;
  const { data: cfg } = usePolling('/api/settings', 15000);
  const [resetting, setResetting] = useState(false);

  if (!status) {
    return <div className="py-24 text-center text-sm text-[var(--color-surface-400)]">Waiting for the trading engine…</div>;
  }
  const acct = status.account || {};
  const risk = status.risk_metrics || {};
  const daily = status.daily_stats || {};
  const lim = risk.limits || {};
  const positions = status.positions || [];
  const equity = acct.equity ?? 0;

  const reset = async () => {
    if (!window.confirm(`Reset the paper account to ${money(cfg?.values?.execution?.initial_capital ?? acct.initial_capital, 0)} and erase all trade history?`)) return;
    setResetting(true);
    try {
      const r = await api('/api/bot/reset', { method: 'POST' });
      onNotice?.(r.status === 'error' ? { type: 'error', text: r.message } : { type: 'ok', text: r.message });
    } catch { onNotice?.({ type: 'error', text: 'Failed to contact API server' }); }
    setResetting(false);
  };

  const v = cfg?.values;
  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      <div className="relative overflow-hidden bg-[var(--color-surface-900)]/60 backdrop-blur-xl border border-[var(--color-surface-800)]/60 rounded-3xl p-6 lg:p-8">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-[var(--color-gold-500)]/10 to-transparent rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h2 className="text-2xl font-heading font-bold text-white">Paper Trading Account</h2>
            <p className="text-xs text-[var(--color-surface-400)] mt-2 flex flex-wrap gap-x-4 gap-y-1 font-mono">
              <span>Mode: <b className="text-[var(--color-gold-400)]">PAPER (no real money)</b></span>
              <span>Strategy: <b className="text-white">{status.strategy}</b></span>
              <span>Prices: <b className="text-white">{status.data_source === 'synthetic' ? 'simulated feed' : `${cfg?.exchange || 'exchange'} (live)`}</b></span>
              <span>Engine: <b className={status.running ? 'text-[var(--color-profit)]' : 'text-[var(--color-surface-300)]'}>{status.running ? 'running' : 'stopped'}</b></span>
            </p>
          </div>
          <div className="flex gap-3">
            <button onClick={onOpenSettings} className="px-5 py-2 rounded-xl bg-[var(--color-gold-600)] text-black font-bold text-xs hover:bg-[var(--color-gold-500)] cursor-pointer flex items-center gap-2">
              <SlidersHorizontal size={14} /> Edit settings
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat icon={Wallet} label="Equity" value={money(equity)} sub={`Cash ${money(acct.cash)} · start ${money(acct.initial_capital, 0)}`} />
        <Stat icon={TrendingUp} label="Total P&L" value={signedMoney(risk.total_pnl)} cls={pnlClass(risk.total_pnl)}
          sub={signedPct(acct.initial_capital ? risk.total_pnl / acct.initial_capital : 0)} />
        <Stat icon={Receipt} label="Fees paid" value={money(acct.fees_paid)} sub="Simulated trading costs" />
        <Stat icon={Award} label="Win rate" value={daily.win_rate == null ? '—' : pct(daily.win_rate, 1)}
          sub={daily.total_trades ? `${daily.wins}W / ${daily.losses}L` : 'No closed trades yet'} />
        <Stat icon={TrendingDown} label="Drawdown" value={pct(risk.current_drawdown, 2)} cls={risk.current_drawdown > 0.05 ? 'text-[var(--color-loss)]' : 'text-white'}
          sub={`Worst ${pct(risk.max_drawdown_reached, 2)} · peak ${money(risk.peak_equity, 0)}`} />
        <Stat icon={Gauge} label="Sharpe (live)" value={(risk.sharpe_ratio ?? 0).toFixed(2)} sub="From recorded equity" />
        <Stat icon={Award} label="Profit factor" value={risk.profit_factor ? `${risk.profit_factor.toFixed(2)}x` : '—'} sub="Gross profit / gross loss" />
        <Stat icon={Wallet} label="Locked-in profit" value={signedMoney(acct.realised_gross || 0)} cls={pnlClass(acct.realised_gross || 0)} sub={`Today ${signedMoney(daily.pnl || 0)} · open ${signedMoney(acct.open_pnl || 0)}`} />
      </div>

      <Readiness />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-[var(--color-surface-900)]/40 backdrop-blur-md border border-[var(--color-surface-800)]/60 rounded-3xl overflow-hidden">
          <div className="px-6 py-4 border-b border-[var(--color-surface-800)]/60 bg-[var(--color-surface-900)]/30">
            <h3 className="text-sm font-heading font-bold text-white tracking-widest">OPEN POSITIONS</h3>
          </div>
          {positions.length === 0 ? (
            <p className="py-10 text-center text-xs text-[var(--color-surface-500)]">No open positions — the account is fully in cash.</p>
          ) : (
            <table className="w-full text-[11px]">
              <thead><tr className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] border-b border-[var(--color-surface-800)]/60">
                {['Symbol', 'Side', 'Size', 'Entry', 'Mark', 'P&L'].map((h, i) => <th key={h} className={`px-4 py-2 font-medium ${i > 1 ? 'text-right' : 'text-left'}`}>{h}</th>)}
              </tr></thead>
              <tbody className="divide-y divide-[var(--color-surface-800)]/40">
                {positions.map(p => (
                  <tr key={p.symbol}>
                    <td className="px-4 py-2 font-mono font-bold text-white">{p.symbol}</td>
                    <td className={`px-4 py-2 uppercase font-bold text-[9px] ${p.side === 'long' ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>{p.side}</td>
                    <td className="px-4 py-2 text-right font-mono text-[var(--color-surface-300)]">{p.size.toFixed(4)}</td>
                    <td className="px-4 py-2 text-right font-mono text-[var(--color-surface-300)]">{money(p.entry_price)}</td>
                    <td className="px-4 py-2 text-right font-mono text-[var(--color-surface-300)]">{money(p.mark_price)}</td>
                    <td className={`px-4 py-2 text-right font-mono font-bold ${pnlClass(p.unrealized_pnl)}`}>{signedMoney(p.unrealized_pnl)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="bg-[var(--color-surface-900)]/40 backdrop-blur-md border border-[var(--color-surface-800)]/60 rounded-3xl overflow-hidden">
          <div className="px-6 py-4 border-b border-[var(--color-surface-800)]/60 bg-[var(--color-surface-900)]/30 flex items-center gap-3">
            <ShieldAlert size={16} className="text-[var(--color-gold-500)]" />
            <h3 className="text-sm font-heading font-bold text-white tracking-widest">RISK LIMITS</h3>
          </div>
          <div className="p-6 flex flex-col gap-4">
            <LimitBar label="Daily loss" used={risk.daily_limit_used} limit={lim.daily} current={signedMoney(risk.daily_pnl)} />
            <LimitBar label="Weekly loss" used={risk.weekly_limit_used} limit={lim.weekly} current={signedMoney(risk.weekly_pnl)} />
            <LimitBar label="Monthly loss" used={risk.monthly_limit_used} limit={lim.monthly} current={signedMoney(risk.monthly_pnl)} />
            <LimitBar label="Drawdown from peak" used={lim.drawdown ? risk.current_drawdown / lim.drawdown : 0} limit={lim.drawdown} current={pct(risk.current_drawdown, 2)} />
            {v && (
              <p className="text-[10px] font-mono text-[var(--color-surface-500)] pt-2 border-t border-[var(--color-surface-800)]/50">
                Fee {pct(v.execution.fee_rate, 3)} · slippage {pct(v.execution.slippage, 3)} · max {pct(v.risk.max_position_size, 0)} per coin · cycle {v.execution.cycle_seconds}s
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="bg-red-500/5 border border-red-500/20 rounded-3xl overflow-hidden">
        <div className="p-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <p className="text-sm font-bold text-white mb-1">Reset paper account</p>
            <p className="text-xs text-[var(--color-surface-500)]">Restores starting capital and erases all simulated trades and equity history. Settings are kept. The engine must be stopped.</p>
          </div>
          <button onClick={reset} disabled={status.running || resetting}
            className="px-6 py-3 rounded-xl bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white border border-red-500/30 font-bold text-xs tracking-widest cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2">
            {resetting ? <Loader size={14} className="animate-spin" /> : <RotateCcw size={14} />} RESET ACCOUNT
          </button>
        </div>
      </div>
    </div>
  );
}

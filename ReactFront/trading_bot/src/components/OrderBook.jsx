import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, BarChart3, Target, Crosshair, Activity, Wallet, ArrowUpRight, ArrowDownRight, RefreshCw } from 'lucide-react';

const API_URL = 'http://localhost:8000';

export default function OrderBook({ status, prices }) {
  const stats = status?.daily_stats || { trades: 0, pnl: 0, win_rate: 0 };
  const risk = status?.risk_metrics || { current_drawdown: 0, total_pnl: 0 };
  const pnlPositive = (risk.total_pnl || 0) >= 0;

  const [balance, setBalance] = useState(null);
  const [balanceLoading, setBalanceLoading] = useState(false);

  const fetchBalance = () => {
    setBalanceLoading(true);
    fetch(`${API_URL}/api/status/balance`)
      .then(r => r.json())
      .then(d => { setBalance(d); setBalanceLoading(false); })
      .catch(() => setBalanceLoading(false));
  };

  useEffect(() => { fetchBalance(); }, []);

  const signals = status?.recent_signals || [];

  return (
    <div className="glass-strong rounded-2xl flex flex-col h-full animate-fade-in-up overflow-hidden" style={{ animationDelay: '0.3s' }}>
      {/* Header */}
      <div className="px-5 py-3.5 border-b border-[var(--color-surface-800)]/60 bg-[var(--color-surface-900)]/30 flex justify-between items-center shrink-0">
        <h3 className="text-xs font-heading font-bold text-[var(--color-surface-300)] tracking-widest">PORTFOLIO</h3>
        <button onClick={fetchBalance} className="text-[var(--color-surface-500)] hover:text-white transition-colors cursor-pointer">
          <RefreshCw size={13} className={balanceLoading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="flex-1 flex flex-col gap-0 overflow-y-auto">
        {/* KPI Stats */}
        <div className="grid grid-cols-2 gap-3 p-4">
          {[
            {
              label: 'Total PnL',
              value: `$${(risk.total_pnl || 0).toFixed(2)}`,
              Icon: pnlPositive ? TrendingUp : TrendingDown,
              color: pnlPositive ? 'var(--color-profit)' : 'var(--color-loss)',
              bg: pnlPositive ? 'var(--color-profit-dim)' : 'var(--color-loss-dim)',
            },
            {
              label: 'Drawdown',
              value: `${((risk.current_drawdown || 0) * 100).toFixed(2)}%`,
              Icon: BarChart3,
              color: 'var(--color-loss)',
              bg: 'var(--color-loss-dim)',
            },
            {
              label: 'Daily Trades',
              value: stats.trades || 0,
              Icon: Target,
              color: 'var(--color-surface-300)',
              bg: 'rgba(255,255,255,0.04)',
            },
            {
              label: 'Win Rate',
              value: `${((stats.win_rate || 0) * 100).toFixed(1)}%`,
              Icon: Crosshair,
              color: 'var(--color-gold-400)',
              bg: 'rgba(245, 158, 11, 0.1)',
            },
          ].map((m) => (
            <div key={m.label} className="rounded-xl p-3 flex flex-col gap-2 border border-[var(--color-surface-800)]/50" style={{ background: 'rgba(10,10,15,0.4)' }}>
              <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: m.bg }}>
                <m.Icon size={14} style={{ color: m.color }} />
              </div>
              <div>
                <p className="text-[9px] font-medium uppercase tracking-wider text-[var(--color-surface-500)] mb-0.5">{m.label}</p>
                <p className="text-base font-bold font-mono" style={{ color: m.color }}>{m.value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Balance Breakdown */}
        <div className="mx-4 mb-3 rounded-xl border border-[var(--color-surface-800)]/50 overflow-hidden">
          <div className="px-4 py-2.5 bg-[var(--color-surface-900)]/50 border-b border-[var(--color-surface-800)]/50 flex items-center gap-2">
            <Wallet size={13} className="text-[var(--color-gold-500)]" />
            <span className="text-[10px] font-heading font-bold tracking-widest text-[var(--color-surface-400)]">ACCOUNT BALANCE</span>
          </div>
          {balance ? (
            <div className="divide-y divide-[var(--color-surface-800)]/40">
              {['USDT', 'BTC', 'ETH', 'SOL'].map(asset => {
                const free = balance[asset]?.free || 0;
                const total = balance[asset]?.total || 0;
                return (
                  <div key={asset} className="flex items-center justify-between px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-[var(--color-surface-800)] flex items-center justify-center">
                        <span className="text-[8px] font-bold text-[var(--color-gold-400)]">{asset[0]}</span>
                      </div>
                      <span className="text-xs font-bold text-white">{asset}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-mono text-white">{free.toFixed(asset === 'USDT' ? 2 : 6)}</p>
                      <p className="text-[9px] font-mono text-[var(--color-surface-500)]">Total: {total.toFixed(asset === 'USDT' ? 2 : 6)}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-4 flex items-center justify-center text-xs text-[var(--color-surface-600)]">
              {balanceLoading ? 'Fetching balance...' : 'No balance data'}
            </div>
          )}
        </div>

        {/* Market Prices */}
        {prices && (
          <div className="mx-4 mb-3 rounded-xl border border-[var(--color-surface-800)]/50 overflow-hidden">
            <div className="px-4 py-2.5 bg-[var(--color-surface-900)]/50 border-b border-[var(--color-surface-800)]/50">
              <span className="text-[10px] font-heading font-bold tracking-widest text-[var(--color-surface-400)]">LIVE PRICES</span>
            </div>
            <div className="divide-y divide-[var(--color-surface-800)]/40">
              {Object.entries(prices).map(([sym, data]) => {
                const chg = data?.change || 0;
                const up = chg >= 0;
                return (
                  <div key={sym} className="flex items-center justify-between px-4 py-2.5">
                    <span className="text-xs font-mono font-bold text-white">{sym.replace('/USDT', '')}</span>
                    <div className="text-right">
                      <p className="text-xs font-mono text-white">${(data?.last || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                      <p className={`text-[9px] font-mono flex items-center gap-0.5 justify-end ${up ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                        {up ? <ArrowUpRight size={9} /> : <ArrowDownRight size={9} />}
                        {up ? '+' : ''}{(chg || 0).toFixed(2)}%
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Recent Signals */}
        <div className="mx-4 mb-4 rounded-xl border border-[var(--color-surface-800)]/50 overflow-hidden">
          <div className="px-4 py-2.5 bg-[var(--color-surface-900)]/50 border-b border-[var(--color-surface-800)]/50">
            <span className="text-[10px] font-heading font-bold tracking-widest text-[var(--color-surface-400)]">RECENT SIGNALS</span>
          </div>
          {signals.length > 0 ? (
            <div className="divide-y divide-[var(--color-surface-800)]/40">
              {signals.slice(0, 5).map((sig, i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-2.5">
                  <div className={`w-5 h-5 rounded flex items-center justify-center ${sig.direction === 'long' ? 'bg-[var(--color-profit)]/15' : 'bg-[var(--color-loss)]/15'}`}>
                    {sig.direction === 'long' ? <ArrowUpRight size={10} className="text-[var(--color-profit)]" /> : <ArrowDownRight size={10} className="text-[var(--color-loss)]" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-white font-mono">{sig.symbol}</p>
                    <p className="text-[9px] text-[var(--color-surface-500)] truncate">{sig.time}</p>
                  </div>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${sig.direction === 'long' ? 'text-[var(--color-profit)] bg-[var(--color-profit)]/10' : 'text-[var(--color-loss)] bg-[var(--color-loss)]/10'}`}>
                    {sig.direction}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-5 flex flex-col items-center justify-center gap-1.5">
              <Activity size={18} className="text-[var(--color-surface-700)]" />
              <p className="text-[10px] text-[var(--color-surface-600)]">Awaiting signals...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

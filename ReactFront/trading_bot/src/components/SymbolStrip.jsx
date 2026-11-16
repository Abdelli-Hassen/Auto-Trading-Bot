import React from 'react';
import { pnlClass } from '../api';

/** Horizontal market selector: every tracked coin with live price, 24h change and any open position. */
export default function SymbolStrip({ symbols, prices, positions, symbol, onSelect }) {
  if (!symbols.length) return null;
  const posBy = Object.fromEntries((positions || []).map(p => [p.symbol, p]));
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 snap-x">
      {symbols.map(sym => {
        const p = prices?.[sym] || {};
        const chg = p.change || 0;
        const pos = posBy[sym];
        const active = sym === symbol;
        return (
          <button key={sym} onClick={() => onSelect(sym)}
            className={`snap-start shrink-0 min-w-[132px] text-left rounded-xl px-3.5 py-2.5 border transition-all cursor-pointer ${
              active
                ? 'bg-[var(--color-surface-800)]/80 border-[var(--color-gold-500)]/40 shadow-[0_0_0_1px_rgba(245,158,11,0.15)]'
                : 'bg-[var(--color-surface-900)]/50 border-white/5 hover:border-white/10 hover:bg-[var(--color-surface-850)]/70'}`}>
            <div className="flex items-center justify-between gap-2">
              <span className={`text-xs font-heading font-bold tracking-wide ${active ? 'text-white' : 'text-[var(--color-surface-300)]'}`}>{sym.replace('/USDT', '')}</span>
              {pos && (
                <span className={`text-[8px] font-bold uppercase px-1.5 py-0.5 rounded ${pos.side === 'long' ? 'bg-[var(--color-profit-dim)] text-[var(--color-profit)]' : 'bg-[var(--color-loss-dim)] text-[var(--color-loss)]'}`}>
                  {pos.side === 'long' ? 'Long' : 'Short'}
                </span>
              )}
            </div>
            <div className="mt-1 flex items-baseline justify-between gap-2">
              <span className="text-[13px] font-mono font-semibold text-white tabular-nums">
                {(p.last || 0).toLocaleString('en-US', { minimumFractionDigits: p.last < 10 ? 4 : 2, maximumFractionDigits: p.last < 10 ? 4 : 2 })}
              </span>
              <span className={`text-[10px] font-mono tabular-nums ${chg >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                {chg >= 0 ? '+' : ''}{chg.toFixed(2)}%
              </span>
            </div>
            {pos && (
              <div className={`mt-1 text-[10px] font-mono tabular-nums ${pnlClass(pos.unrealized_pnl)}`}>
                {pos.unrealized_pnl >= 0 ? '+' : '-'}${Math.abs(pos.unrealized_pnl).toFixed(2)}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}

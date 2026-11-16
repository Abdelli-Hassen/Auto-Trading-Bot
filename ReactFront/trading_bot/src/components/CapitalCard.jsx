import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Banknote, ArrowDownToLine, ArrowUpFromLine, X, Loader, DollarSign } from 'lucide-react';
import { api, money, pct } from '../api';

const CARD = 'rounded-2xl border border-white/5 bg-gradient-to-b from-[var(--color-surface-850)]/80 to-[var(--color-surface-900)]/60 backdrop-blur-xl';
const PRESETS = [0.25, 0.5, 0.75, 1];

function FundsModal({ capital, onClose, onDone }) {
  const [mode, setMode] = useState('deposit');
  const [amount, setAmount] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const free = capital?.free ?? 0;

  const submit = async () => {
    const n = parseFloat(amount);
    if (!(n > 0)) { setErr('Enter an amount greater than 0'); return; }
    setBusy(true); setErr(null);
    try {
      const r = await api(`/api/account/${mode}`, { method: 'POST', body: { amount: n } });
      if (r.status === 'error') throw new Error(r.message);
      onDone({ type: 'ok', text: r.message });
      onClose();
    } catch (e) { setErr(e.message || 'Request failed'); setBusy(false); }
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="w-full max-w-sm rounded-2xl bg-[var(--color-surface-900)] border border-[var(--color-surface-700)] p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-heading font-bold text-white text-sm tracking-wider">PAPER FUNDS</h3>
          <button onClick={onClose} className="text-[var(--color-surface-500)] hover:text-white cursor-pointer"><X size={18} /></button>
        </div>
        <div className="grid grid-cols-2 gap-1 p-1 rounded-xl bg-[var(--color-surface-950)] border border-white/5 mb-5">
          {[['deposit', 'Deposit', ArrowDownToLine], ['withdraw', 'Withdraw', ArrowUpFromLine]].map(([id, label, Icon]) => (
            <button key={id} onClick={() => { setMode(id); setErr(null); }}
              className={`py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-2 cursor-pointer transition-colors ${mode === id ? 'bg-[var(--color-surface-800)] text-white' : 'text-[var(--color-surface-500)] hover:text-white'}`}>
              <Icon size={13} /> {label}
            </button>
          ))}
        </div>
        <label className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)]">Amount (USD)</label>
        <div className="relative mt-1.5">
          <DollarSign size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-surface-500)]" />
          <input type="number" min="0" step="any" value={amount} autoFocus onChange={e => setAmount(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && submit()}
            className="w-full bg-[var(--color-surface-950)] border border-[var(--color-surface-700)] rounded-lg pl-8 pr-3 py-2.5 text-lg font-mono text-white focus:outline-none focus:border-[var(--color-gold-500)]/60" />
        </div>
        <div className="flex gap-2 mt-3">
          {(mode === 'deposit' ? [500, 1000, 5000, 10000] : [0.25, 0.5, 1].map(f => Math.floor(free * f))).map(v => (
            <button key={v} onClick={() => setAmount(String(v))}
              className="flex-1 py-1.5 rounded-lg text-[11px] font-mono border border-white/10 text-[var(--color-surface-400)] hover:text-white hover:border-white/20 cursor-pointer">
              {money(v, 0)}
            </button>
          ))}
        </div>
        <p className="mt-3 text-[11px] text-[var(--color-surface-500)] leading-relaxed">
          {mode === 'deposit'
            ? 'Adds simulated cash. Your starting capital rises by the same amount, so profit/loss and risk limits are not distorted.'
            : <>You can withdraw up to <span className="text-white font-mono">{money(free)}</span> — money backing open positions stays locked.</>}
        </p>
        {err && <p className="mt-3 text-xs text-[var(--color-loss)]">{err}</p>}
        <button onClick={submit} disabled={busy}
          className="mt-5 w-full py-2.5 rounded-xl text-xs font-bold tracking-widest bg-[var(--color-gold-600)] hover:bg-[var(--color-gold-500)] text-black cursor-pointer disabled:opacity-60 flex items-center justify-center gap-2">
          {busy && <Loader size={14} className="animate-spin" />} {mode === 'deposit' ? 'DEPOSIT' : 'WITHDRAW'}
        </button>
      </div>
    </div>,
    document.body
  );
}

/** Controls how much of the account the strategy may put to work. */
export default function CapitalCard({ capital, isConnected, onNotice }) {
  const [pctVal, setPctVal] = useState(100);
  const [usd, setUsd] = useState('');
  const [size, setSize] = useState('');
  const [busy, setBusy] = useState(false);
  const [funds, setFunds] = useState(false);

  // sync from the server unless the user is mid-edit
  useEffect(() => {
    if (capital && !busy) {
      setPctVal(Math.round((capital.budget_pct ?? 1) * 100));
      setUsd(capital.budget_usd > 0 ? String(capital.budget_usd) : '');
      setSize(capital.trade_size_usd > 0 ? String(capital.trade_size_usd) : '');
    }
  }, [capital?.budget_pct, capital?.budget_usd, capital?.trade_size_usd]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!capital) return null;
  const capped = capital.budget_usd > 0;

  const save = async (execution, okText) => {
    setBusy(true);
    try {
      const r = await api('/api/settings', { method: 'PUT', body: { risk: {}, execution } });
      if (r.status === 'error') throw new Error(r.message);
      onNotice?.({ type: 'ok', text: okText });
    } catch (e) { onNotice?.({ type: 'error', text: e.message || 'Could not save' }); }
    setBusy(false);
  };

  const applyPct = (p) => { setPctVal(p); save({ trade_budget_pct: p / 100, trade_budget_usd: 0 }, `Trading budget set to ${p}% of the account`); setUsd(''); };
  const applyUsd = () => {
    const n = parseFloat(usd);
    if (!(n > 0)) { onNotice?.({ type: 'error', text: 'Enter a dollar amount greater than 0' }); return; }
    setPctVal(100);
    save({ trade_budget_pct: 1, trade_budget_usd: n }, `Trading budget capped at ${money(n, 0)}`);
  };

  const idle = Math.max(capital.equity - capital.budget, 0);
  const fixedSize = capital.trade_size_usd > 0;
  const applySize = () => {
    const n = parseFloat(size);
    if (!(n > 0)) { onNotice?.({ type: 'error', text: 'Enter an amount greater than 0 (or press Clear)' }); return; }
    save({ trade_size_usd: n }, `Each trade will now use ${money(n, 0)}`);
  };
  const clearSize = () => { setSize(''); save({ trade_size_usd: 0 }, 'Back to automatic trade sizing'); };

  return (
    <div className={`${CARD} p-5 flex flex-col gap-4`}>
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 text-[10px] font-heading font-bold tracking-[0.16em] text-[var(--color-surface-400)]"><Banknote size={12} /> TRADING CAPITAL</span>
        <button onClick={() => setFunds(true)} disabled={!isConnected}
          className="text-[10px] uppercase tracking-wider text-[var(--color-gold-400)] hover:text-[var(--color-gold-300)] cursor-pointer disabled:opacity-40">
          Deposit / Withdraw
        </button>
      </div>

      <div>
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-heading font-bold text-white tabular-nums">{money(capital.budget, 0)}</span>
          <span className="text-[11px] font-mono text-[var(--color-surface-500)]">of {money(capital.equity, 0)} account</span>
        </div>
        <div className="mt-2 h-2 rounded-full bg-[var(--color-surface-800)] overflow-hidden flex">
          <div className="h-full bg-[var(--color-gold-500)] transition-all duration-500" style={{ width: `${Math.min(capital.budget / (capital.equity || 1), 1) * 100}%` }} />
        </div>
        <div className="flex justify-between mt-1.5 text-[10px] font-mono text-[var(--color-surface-500)]">
          <span>deployed {money(capital.deployed, 0)}</span>
          <span>kept in cash {money(idle, 0)}</span>
        </div>
      </div>

      {/* fixed amount per trade */}
      <div className="rounded-xl border border-[var(--color-gold-500)]/20 bg-[var(--color-gold-500)]/[0.04] p-3">
        <label className="text-[10px] uppercase tracking-wider text-[var(--color-gold-400)] font-bold">Amount per trade</label>
        <div className="flex gap-2 mt-1.5">
          <div className="relative flex-1">
            <DollarSign size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--color-surface-500)]" />
            <input type="number" min="0" step="any" placeholder="e.g. 100" value={size} onChange={e => setSize(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && applySize()}
              className="w-full bg-[var(--color-surface-950)] border border-white/10 rounded-lg pl-7 pr-2 py-1.5 text-sm font-mono text-white focus:outline-none focus:border-[var(--color-gold-500)]/50" />
          </div>
          <button onClick={applySize} disabled={busy || !isConnected}
            className="px-3.5 rounded-lg text-[11px] font-bold cursor-pointer disabled:opacity-50 bg-[var(--color-gold-600)] hover:bg-[var(--color-gold-500)] text-black">
            {fixedSize ? 'Update' : 'Set'}
          </button>
          {fixedSize && (
            <button onClick={clearSize} disabled={busy} title="Back to automatic sizing"
              className="px-2.5 rounded-lg border border-white/10 text-[var(--color-surface-400)] hover:text-white cursor-pointer"><X size={13} /></button>
          )}
        </div>
        <p className="mt-2 text-[10px] leading-relaxed text-[var(--color-surface-500)]">
          {fixedSize
            ? `Every position the bot opens uses exactly ${money(capital.trade_size_usd, 0)} (long or short), e.g. 3 signals = ${money(capital.trade_size_usd * 3, 0)} in play.`
            : 'Off: position sizes come from the strategy weights. Set e.g. 100 to put exactly $100 into each trade.'}
        </p>
      </div>

      {/* percentage */}
      <div>
        <div className="flex justify-between text-[10px] mb-1.5">
          <span className="uppercase tracking-wider text-[var(--color-surface-500)]">Share of account</span>
          <span className="font-mono text-white">{capped || fixedSize ? '—' : `${pctVal}%`}</span>
        </div>
        <input type="range" min="5" max="100" step="5" value={pctVal} disabled={busy || !isConnected}
          onChange={e => { setPctVal(Number(e.target.value)); setUsd(''); }}
          onMouseUp={() => applyPct(pctVal)} onTouchEnd={() => applyPct(pctVal)} onKeyUp={() => applyPct(pctVal)}
          className="w-full accent-[var(--color-gold-500)] cursor-pointer" />
        <div className="grid grid-cols-4 gap-1.5 mt-2">
          {PRESETS.map(p => (
            <button key={p} onClick={() => applyPct(p * 100)} disabled={busy || !isConnected}
              className={`py-1.5 rounded-lg text-[11px] font-mono border cursor-pointer transition-colors disabled:opacity-50 ${!capped && pctVal === p * 100 ? 'bg-[var(--color-gold-500)]/15 border-[var(--color-gold-500)]/40 text-[var(--color-gold-400)]' : 'border-white/10 text-[var(--color-surface-400)] hover:text-white hover:border-white/20'}`}>
              {p * 100}%
            </button>
          ))}
        </div>
      </div>

      {/* fixed dollar cap */}
      <div>
        <label className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)]">Or cap at a fixed amount</label>
        <div className="flex gap-2 mt-1.5">
          <div className="relative flex-1">
            <DollarSign size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--color-surface-500)]" />
            <input type="number" min="0" step="any" placeholder="e.g. 2000" value={usd} onChange={e => setUsd(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && applyUsd()}
              className="w-full bg-[var(--color-surface-950)] border border-white/10 rounded-lg pl-7 pr-2 py-1.5 text-sm font-mono text-white focus:outline-none focus:border-[var(--color-gold-500)]/50" />
          </div>
          <button onClick={applyUsd} disabled={busy || !isConnected}
            className={`px-3.5 rounded-lg text-[11px] font-bold cursor-pointer disabled:opacity-50 border ${capped ? 'bg-[var(--color-gold-500)]/15 border-[var(--color-gold-500)]/40 text-[var(--color-gold-400)]' : 'border-white/10 text-[var(--color-surface-300)] hover:text-white hover:border-white/20'}`}>
            {busy ? <Loader size={12} className="animate-spin" /> : capped ? 'Update' : 'Apply'}
          </button>
        </div>
      </div>

      <p className="text-[10px] leading-relaxed text-[var(--color-surface-500)]">
        The strategy sizes every position against this budget; the rest stays in cash. Changes re-size open positions within seconds.
      </p>
      {funds && <FundsModal capital={capital} onClose={() => setFunds(false)} onDone={onNotice} />}
    </div>
  );
}

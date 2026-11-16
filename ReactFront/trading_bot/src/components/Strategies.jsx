import React, { useState } from 'react';
import { Cpu, Zap, Shield, Play, Square, Loader, Settings2, X, Check, FlaskConical, CheckCircle2, AlertCircle } from 'lucide-react';
import { api, usePolling, signedMoney, pct, signedPct, ago, pnlClass } from '../api';
import Tooltip from './Tooltip';

const toUi = (p, v) => (p.unit === 'pct' ? +(v * 100).toFixed(3) : v);
const fromUi = (p, v) => (p.unit === 'pct' ? v / 100 : v);
const fmtParam = (p) => (p.unit === 'pct' ? `${+(p.value * 100).toFixed(2)}%` : String(+p.value.toFixed(3)));

function Sparkline({ values }) {
  if (!values || values.length < 2) return null;
  const min = Math.min(...values), max = Math.max(...values), range = max - min || 1;
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * 100},${36 - ((v - min) / range) * 32 - 2}`).join(' ');
  const up = values[values.length - 1] >= values[0];
  return (
    <svg viewBox="0 0 100 36" preserveAspectRatio="none" className="w-full h-10">
      <polyline points={pts} fill="none" strokeWidth="1.2" vectorEffect="non-scaling-stroke"
        stroke={up ? 'var(--color-profit)' : 'var(--color-loss)'} />
    </svg>
  );
}

function EditModal({ strategy, onClose, onSaved }) {
  const [vals, setVals] = useState(() => Object.fromEntries(strategy.params.map(p => [p.key, toUi(p, p.value)])));
  const [err, setErr] = useState(null);
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true); setErr(null);
    try {
      const body = Object.fromEntries(strategy.params.map(p => [p.key, fromUi(p, parseFloat(vals[p.key]))]));
      const r = await api(`/api/strategies/${strategy.id}/params`, { method: 'PUT', body: { params: body } });
      if (r.status === 'error') throw new Error(r.message);
      onSaved(); onClose();
    } catch (e) { setErr(e.message); setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[var(--color-surface-900)] border border-[var(--color-surface-700)] rounded-2xl p-6 w-full max-w-md shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-1">
          <div className="flex items-center gap-2">
            <Settings2 size={18} className="text-[var(--color-gold-500)]" />
            <h3 className="font-heading font-bold text-white text-sm tracking-wider">EDIT PARAMETERS</h3>
          </div>
          <button onClick={onClose} className="text-[var(--color-surface-500)] hover:text-white cursor-pointer"><X size={18} /></button>
        </div>
        <p className="text-xs text-[var(--color-surface-400)] mb-5 font-mono">{strategy.name} · applied immediately</p>
        <div className="flex flex-col gap-4">
          {strategy.params.map(p => (
            <div key={p.key}>
              <label className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1.5 flex justify-between">
                <span>{p.label}</span>
                <span className="normal-case tracking-normal">{toUi(p, p.min)}–{toUi(p, p.max)}{p.unit === 'pct' ? '%' : ''}</span>
              </label>
              <input type="number" step={toUi(p, p.step)} min={toUi(p, p.min)} max={toUi(p, p.max)} value={vals[p.key]}
                onChange={e => setVals(v => ({ ...v, [p.key]: e.target.value }))}
                className="w-full bg-[var(--color-surface-800)] border border-[var(--color-surface-700)] rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-[var(--color-gold-500)]/50" />
              <p className="text-[10px] text-[var(--color-surface-500)] mt-1">{p.help}</p>
            </div>
          ))}
        </div>
        {err && <p className="mt-4 text-xs text-[var(--color-loss)]">{err}</p>}
        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-xl text-xs font-bold border border-[var(--color-surface-700)] text-[var(--color-surface-400)] hover:text-white cursor-pointer">Cancel</button>
          <button onClick={save} disabled={saving} className="flex-1 py-2.5 rounded-xl text-xs font-bold bg-[var(--color-gold-600)] hover:bg-[var(--color-gold-500)] text-black cursor-pointer flex items-center justify-center gap-2 disabled:opacity-60">
            {saving ? <Loader size={14} className="animate-spin" /> : <Check size={14} />} Save
          </button>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, cls = 'text-white', tip }) {
  return (
    <Tooltip wrapperClass="w-full" content={tip}>
      <div className="bg-[var(--color-surface-950)]/40 rounded-lg px-2 py-2 text-center border border-[var(--color-surface-800)]/40">
        <p className="text-[8px] uppercase tracking-widest text-[var(--color-surface-600)] mb-0.5">{label}</p>
        <p className={`text-[12px] font-mono font-bold ${cls}`}>{value}</p>
      </div>
    </Tooltip>
  );
}

function Card({ s, onChanged, setNotice }) {
  const [busy, setBusy] = useState(null);
  const [editing, setEditing] = useState(false);
  const running = s.status === 'active';
  const st = s.stats;
  const bt = s.backtest;

  const act = async (key, path, method = 'POST') => {
    setBusy(key);
    try {
      const r = await api(path, { method, timeout: 120000 });
      if (r.status === 'error') setNotice({ type: 'error', text: r.message });
      else if (r.message) setNotice({ type: 'ok', text: r.message });
    } catch (e) {
      setNotice({ type: 'error', text: 'Request failed — is the backend running?' });
    }
    setBusy(null);
    onChanged();
  };

  return (
    <div className={`bg-[var(--color-surface-900)]/60 backdrop-blur-md border rounded-2xl flex flex-col overflow-hidden transition-colors ${s.selected ? 'border-[var(--color-gold-500)]/30' : 'border-[var(--color-surface-800)]/60'}`}>
      <div className={`h-1 w-full ${running ? 'bg-[var(--color-gold-500)] shadow-[0_0_10px_rgba(245,158,11,0.3)]' : 'bg-[var(--color-surface-800)]'}`} />
      <div className="p-5 flex flex-col gap-4">
        <div className="flex justify-between items-start gap-3">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-xl ${running ? 'bg-[var(--color-gold-500)]/20 text-[var(--color-gold-400)]' : 'bg-[var(--color-surface-800)] text-[var(--color-surface-500)]'}`}><Zap size={18} /></div>
            <div>
              <h3 className="font-bold text-white">{s.name}</h3>
              <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                <span className="text-[9px] font-mono text-[var(--color-surface-400)] uppercase">{s.type}</span>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${running ? 'bg-[var(--color-profit)]/10 text-[var(--color-profit)]' : s.selected ? 'bg-[var(--color-gold-500)]/10 text-[var(--color-gold-400)]' : 'bg-[var(--color-surface-800)] text-[var(--color-surface-500)]'}`}>
                  {running ? 'RUNNING' : s.selected ? 'SELECTED' : 'IDLE'}
                </span>
              </div>
            </div>
          </div>
          <button onClick={() => setEditing(true)} title="Edit parameters"
            className="p-1.5 rounded-lg text-[var(--color-surface-500)] hover:text-white hover:bg-[var(--color-surface-800)] cursor-pointer"><Settings2 size={15} /></button>
        </div>

        <p className="text-[11px] text-[var(--color-surface-400)] leading-relaxed">{s.description}</p>
        <p className="text-[10px] font-mono text-[var(--color-surface-500)]">Universe: {s.universe}</p>

        {s.summary && (
          <div className="text-[11px] text-[var(--color-surface-300)] bg-[var(--color-surface-950)]/40 border border-[var(--color-surface-800)]/50 rounded-lg px-3 py-2 leading-relaxed">
            <span className="font-bold text-white">Right now: </span>{s.summary}
          </div>
        )}

        <div className="grid grid-cols-4 gap-2">
          <Stat label="Realised" value={signedMoney(st.realized_pnl)} cls={pnlClass(st.realized_pnl)} tip="Profit/loss from this strategy's closed trades." />
          <Stat label="Open P&L" value={signedMoney(st.unrealized_pnl)} cls={pnlClass(st.unrealized_pnl)} tip="Unrealised profit/loss on its current positions." />
          <Stat label="Win rate" value={st.win_rate == null ? '—' : pct(st.win_rate, 0)} cls={st.win_rate == null ? 'text-[var(--color-surface-500)]' : 'text-[var(--color-gold-400)]'} tip="Closed trades that made money. — means none closed yet." />
          <Stat label="Trades" value={st.trades} tip="Number of closed trades." />
        </div>

        <div className="rounded-xl border border-[var(--color-surface-800)]/40 px-3 py-1 bg-[var(--color-surface-950)]/30">
          {s.params.map(p => (
            <div key={p.key} className="flex justify-between items-center py-1.5 border-b border-[var(--color-surface-800)]/40 last:border-0">
              <span className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)]">{p.label}</span>
              <span className="text-xs font-mono font-bold text-[var(--color-gold-400)]">{fmtParam(p)}</span>
            </div>
          ))}
        </div>

        <ul className="text-[10px] text-[var(--color-surface-500)] space-y-0.5 list-disc pl-4">
          {s.rules.map(r => <li key={r}>{r}</li>)}
        </ul>

        {/* Backtest */}
        <div className="rounded-xl border border-[var(--color-surface-800)]/50 p-3 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-widest font-bold text-[var(--color-surface-500)] flex items-center gap-1.5"><FlaskConical size={12} /> Backtest on real history</span>
            <button onClick={() => act('bt', `/api/strategies/${s.id}/backtest`)} disabled={busy === 'bt'}
              className="text-[10px] font-bold px-3 py-1 rounded-lg bg-[var(--color-surface-800)] border border-[var(--color-surface-700)] text-[var(--color-surface-300)] hover:text-white hover:border-[var(--color-gold-500)]/50 cursor-pointer disabled:opacity-60 flex items-center gap-1.5">
              {busy === 'bt' ? <><Loader size={11} className="animate-spin" /> Running…</> : bt ? 'Re-run' : 'Run'}
            </button>
          </div>
          {bt ? (
            <>
              <div className="grid grid-cols-4 gap-2 text-center">
                {[['Return', signedPct(bt.total_return_percent, 0), pnlClass(bt.total_return_percent)],
                  ['Sharpe', (bt.sharpe_ratio ?? 0).toFixed(2), 'text-white'],
                  ['Max DD', pct(bt.max_drawdown, 0), 'text-[var(--color-loss)]'],
                  ['Win', bt.total_trades ? pct(bt.win_rate, 0) : (bt.avg_exposure != null ? `exp ${pct(bt.avg_exposure, 0)}` : '—'), 'text-[var(--color-gold-400)]']]
                  .map(([l, v, c]) => (
                    <div key={l}><p className="text-[8px] uppercase tracking-widest text-[var(--color-surface-600)]">{l}</p><p className={`text-[12px] font-mono font-bold ${c}`}>{v}</p></div>
                  ))}
              </div>
              <Sparkline values={bt.curve} />
              <p className="text-[9px] text-[var(--color-surface-600)] font-mono">{bt.label} · costs included · ran {ago(bt.ran_at)}. Past results are an estimate, not a promise.</p>
            </>
          ) : <p className="text-[10px] text-[var(--color-surface-600)]">Not run yet. Click Run to test this strategy on recent real market data.</p>}
        </div>

        <div className="flex items-center gap-2 pt-3 border-t border-[var(--color-surface-800)]/40">
          <div className="flex-1 flex items-center gap-2">
            <Shield size={12} className="text-[var(--color-gold-500)]" />
            <span className="text-[9px] font-bold text-[var(--color-surface-500)] uppercase">{s.risk} profile</span>
          </div>
          {!s.selected && (
            <button onClick={() => act('sel', `/api/strategies/${s.id}/select`)} disabled={!!busy}
              className="px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-widest border border-[var(--color-surface-700)] text-[var(--color-surface-300)] hover:text-white hover:border-[var(--color-gold-500)]/50 cursor-pointer disabled:opacity-60">
              Select
            </button>
          )}
          <button onClick={() => act('run', `/api/strategies/${s.id}/${running ? 'stop' : 'start'}`)} disabled={!!busy}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-widest border cursor-pointer disabled:opacity-60 ${
              running ? 'bg-[var(--color-loss-dim)] border-[var(--color-loss)]/30 text-[var(--color-loss)] hover:bg-[var(--color-loss)] hover:text-white'
                      : 'bg-[var(--color-profit)]/15 border-[var(--color-profit)]/30 text-[var(--color-profit)] hover:bg-[var(--color-profit)] hover:text-white'}`}>
            {busy === 'run' ? <Loader size={10} className="animate-spin" /> : running ? <Square size={10} fill="currentColor" /> : <Play size={10} fill="currentColor" />}
            {running ? 'Stop' : 'Start'}
          </button>
        </div>
      </div>
      {editing && <EditModal strategy={s} onClose={() => setEditing(false)} onSaved={onChanged} />}
    </div>
  );
}

export default function Strategies() {
  const { data, error, loading, reload } = usePolling('/api/strategies', 4000);
  const [notice, setNotice] = useState(null);
  const flash = (n) => { setNotice(n); setTimeout(() => setNotice(null), 5000); };

  return (
    <div className="flex flex-col gap-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-heading font-bold text-white flex items-center gap-3">
          <Cpu className="text-[var(--color-gold-500)]" size={24} /> Trading Strategies
        </h2>
        {data && <span className="text-[10px] uppercase tracking-wider font-bold text-[var(--color-surface-500)]">
          {data.filter(s => s.status === 'active').length} running / {data.length} available
        </span>}
      </div>

      {notice && (
        <div className={`rounded-xl px-4 py-2.5 text-xs flex items-center gap-2 border ${notice.type === 'error' ? 'bg-[var(--color-loss-dim)] border-[var(--color-loss)]/30 text-[var(--color-loss)]' : 'bg-[var(--color-profit-dim)] border-[var(--color-profit)]/30 text-[var(--color-profit)]'}`}>
          {notice.type === 'error' ? <AlertCircle size={14} /> : <CheckCircle2 size={14} />} {notice.text}
        </div>
      )}

      {loading && !data ? (
        <div className="flex justify-center py-20"><Loader className="animate-spin text-[var(--color-gold-500)]" size={28} /></div>
      ) : error && !data ? (
        <div className="py-16 text-center text-sm text-[var(--color-loss)]">{error}. <button className="underline cursor-pointer" onClick={reload}>Retry</button></div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-5 pb-4">
          {data.map(s => <Card key={s.id} s={s} onChanged={reload} setNotice={flash} />)}
        </div>
      )}
    </div>
  );
}

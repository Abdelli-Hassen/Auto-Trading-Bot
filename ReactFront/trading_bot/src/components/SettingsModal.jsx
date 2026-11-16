import React, { useState, useEffect } from 'react';
import { X, Save, ShieldAlert, Sliders, Database, Loader } from 'lucide-react';
import { api } from '../api';

const toUi = (spec, v) => (spec.unit === 'pct' ? +(v * 100).toFixed(4) : v);
const fromUi = (spec, v) => (spec.unit === 'pct' ? v / 100 : v);
const suffix = (spec) => (spec.unit === 'pct' ? '%' : spec.unit === 'usd' ? '$' : '');

const TABS = [
  { id: 'risk', label: 'Risk Limits', icon: ShieldAlert, group: 'risk' },
  { id: 'execution', label: 'Execution & Costs', icon: Sliders, group: 'execution' },
  { id: 'data', label: 'Market Data', icon: Database },
];

export default function SettingsModal({ isOpen, onClose, onSaved }) {
  const [tab, setTab] = useState('risk');
  const [cfg, setCfg] = useState(null);
  const [form, setForm] = useState({});
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [loadErr, setLoadErr] = useState(null);

  useEffect(() => {
    if (!isOpen) return;
    setError(null); setLoadErr(null);
    api('/api/settings').then(c => {
      setCfg(c);
      const f = {};
      for (const g of ['risk', 'execution'])
        for (const [k, spec] of Object.entries(c.schema[g])) f[`${g}.${k}`] = toUi(spec, c.values[g][k]);
      setForm(f);
    }).catch(() => setLoadErr('Cannot reach the trading engine.'));
  }, [isOpen]);

  if (!isOpen) return null;

  const save = async () => {
    setSaving(true); setError(null);
    const body = { risk: {}, execution: {} };
    for (const g of ['risk', 'execution'])
      for (const [k, spec] of Object.entries(cfg.schema[g])) body[g][k] = fromUi(spec, parseFloat(form[`${g}.${k}`]));
    try {
      const r = await api('/api/settings', { method: 'PUT', body });
      if (r.status === 'error') throw new Error(r.message);
      onSaved?.('Settings saved');
      onClose();
    } catch (e) { setError(e.message || 'Save failed'); }
    setSaving(false);
  };

  const group = TABS.find(t => t.id === tab)?.group;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-[var(--color-surface-900)] border border-[var(--color-surface-800)] rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="px-6 py-4 border-b border-[var(--color-surface-800)] flex justify-between items-center bg-[var(--color-surface-850)]">
          <h2 className="text-xl font-heading font-bold text-white">Settings</h2>
          <button onClick={onClose} className="text-[var(--color-surface-500)] hover:text-white cursor-pointer"><X size={20} /></button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          <div className="w-48 border-r border-[var(--color-surface-800)] bg-[var(--color-surface-900)]/50 p-4 flex flex-col gap-2">
            {TABS.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer ${tab === t.id ? 'bg-[var(--color-surface-800)] text-white' : 'text-[var(--color-surface-400)] hover:bg-[var(--color-surface-800)]/50 hover:text-white'}`}>
                <t.icon size={16} /> {t.label}
              </button>
            ))}
          </div>

          <div className="flex-1 p-6 overflow-y-auto">
            {loadErr ? <p className="text-sm text-[var(--color-loss)]">{loadErr}</p>
              : !cfg ? <div className="flex justify-center py-10"><Loader className="animate-spin text-[var(--color-gold-500)]" /></div>
              : group ? (
                <div className="space-y-4">
                  <p className="text-xs text-[var(--color-surface-400)]">
                    {group === 'risk' ? 'Limits are enforced by the risk manager on every cycle. Loss limits block new buys; the drawdown limit liquidates and stops the bot.'
                      : 'Simulated trading costs and engine cadence. Changes apply immediately. Initial capital is used the next time you reset the account.'}
                  </p>
                  {Object.entries(cfg.schema[group]).map(([k, spec]) => (
                    <div key={k}>
                      <label className="flex justify-between text-xs font-medium text-[var(--color-surface-400)] mb-1">
                        <span>{spec.label}</span>
                        <span className="text-[var(--color-surface-600)]">{toUi(spec, spec.min)}–{toUi(spec, spec.max)}{suffix(spec)}</span>
                      </label>
                      <div className="relative">
                        <input type="number" step="any" value={form[`${group}.${k}`] ?? ''}
                          onChange={e => setForm(f => ({ ...f, [`${group}.${k}`]: e.target.value }))}
                          className="w-full bg-[var(--color-surface-950)] border border-[var(--color-surface-800)] rounded-lg pl-3 pr-8 py-2 text-sm text-white font-mono focus:outline-none focus:border-[var(--color-gold-500)]" />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[var(--color-surface-500)]">{suffix(spec)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4 text-sm">
                  <h3 className="text-lg font-medium text-white">Market data</h3>
                  <dl className="grid grid-cols-2 gap-y-3 text-xs">
                    <dt className="text-[var(--color-surface-500)]">Exchange</dt><dd className="font-mono text-white capitalize">{cfg.exchange} (public data)</dd>
                    <dt className="text-[var(--color-surface-500)]">Current feed</dt>
                    <dd className={`font-mono ${cfg.data_source === 'synthetic' ? 'text-[var(--color-gold-400)]' : 'text-[var(--color-profit)]'}`}>
                      {cfg.data_source === 'synthetic' ? 'Simulated (exchange unreachable)' : 'Live exchange prices'}</dd>
                    <dt className="text-[var(--color-surface-500)]">API keys</dt><dd className="font-mono text-white">Not needed</dd>
                    <dt className="text-[var(--color-surface-500)]">Order execution</dt><dd className="font-mono text-white">Simulated locally (paper)</dd>
                  </dl>
                  <p className="text-xs text-[var(--color-surface-500)] leading-relaxed">
                    The bot reads public prices only and never places real orders, so no exchange keys are stored or required.
                    Set the <code className="text-[var(--color-gold-400)]">FORCE_SYNTHETIC=true</code> environment variable before starting the backend to force the simulated feed.
                  </p>
                </div>
              )}
            {error && <p className="mt-4 text-xs text-[var(--color-loss)]">{error}</p>}
          </div>
        </div>

        <div className="px-6 py-4 border-t border-[var(--color-surface-800)] bg-[var(--color-surface-850)] flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-medium text-[var(--color-surface-300)] hover:text-white hover:bg-[var(--color-surface-800)] cursor-pointer">Cancel</button>
          <button onClick={save} disabled={saving || !cfg || !group}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold bg-[var(--color-gold-600)] hover:bg-[var(--color-gold-500)] text-black cursor-pointer disabled:opacity-50">
            {saving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />} Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

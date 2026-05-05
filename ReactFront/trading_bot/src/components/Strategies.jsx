import React, { useState, useEffect, useCallback } from 'react';
import {
  Cpu, Zap, Shield, Play, Square, Loader,
  ChevronDown, ChevronUp, Settings2, X, Check, AlertCircle
} from 'lucide-react';

const API_URL = 'http://localhost:8000';

const DEFAULT_PARAMS = {
  entry_threshold: 2.0,
  exit_threshold: 0.5,
  stop_threshold: 3.0,
  lookback: 100,
  risk_per_trade: 0.01,
};

function ParamRow({ label, value, unit = '' }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-[var(--color-surface-800)]/40 last:border-0">
      <span className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)]">{label}</span>
      <span className="text-xs font-mono font-bold text-[var(--color-gold-400)]">{value}{unit}</span>
    </div>
  );
}

function EditModal({ strategy, onClose, onSave }) {
  const [params, setParams] = useState({ ...DEFAULT_PARAMS });

  const handleSave = () => {
    onSave(strategy.id, params);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[var(--color-surface-900)] border border-[var(--color-surface-700)] rounded-2xl p-6 w-full max-w-sm shadow-2xl animate-fade-in-up">
        <div className="flex justify-between items-center mb-5">
          <div className="flex items-center gap-2">
            <Settings2 size={18} className="text-[var(--color-gold-500)]" />
            <h3 className="font-heading font-bold text-white text-sm tracking-wider">EDIT PARAMETERS</h3>
          </div>
          <button onClick={onClose} className="text-[var(--color-surface-500)] hover:text-white transition-colors cursor-pointer">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-[var(--color-surface-400)] mb-5 font-mono">{strategy.name}</p>

        <div className="flex flex-col gap-4">
          {Object.entries(params).map(([key, val]) => (
            <div key={key}>
              <label className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1.5 block">
                {key.replace(/_/g, ' ')}
              </label>
              <input
                type="number"
                step="0.001"
                value={val}
                onChange={e => setParams(p => ({ ...p, [key]: parseFloat(e.target.value) }))}
                className="w-full bg-[var(--color-surface-800)] border border-[var(--color-surface-700)] rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-[var(--color-gold-500)]/50 transition-colors"
              />
            </div>
          ))}
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-xl text-xs font-bold border border-[var(--color-surface-700)] text-[var(--color-surface-400)] hover:text-white transition-colors cursor-pointer">
            Cancel
          </button>
          <button onClick={handleSave} className="flex-1 py-2.5 rounded-xl text-xs font-bold bg-[var(--color-gold-600)] hover:bg-[var(--color-gold-500)] text-black transition-colors cursor-pointer flex items-center justify-center gap-2">
            <Check size={14} />
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

function ConfirmModal({ strategy, action, onConfirm, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[var(--color-surface-900)] border border-[var(--color-surface-700)] rounded-2xl p-6 w-full max-w-xs shadow-2xl animate-fade-in-up">
        <div className="flex items-center gap-3 mb-4">
          <div className={`p-2 rounded-lg ${action === 'stop' ? 'bg-[var(--color-loss)]/15' : 'bg-[var(--color-profit)]/15'}`}>
            <AlertCircle size={18} className={action === 'stop' ? 'text-[var(--color-loss)]' : 'text-[var(--color-profit)]'} />
          </div>
          <h3 className="font-heading font-bold text-white text-sm">
            {action === 'stop' ? 'Stop' : 'Start'} Strategy?
          </h3>
        </div>
        <p className="text-xs text-[var(--color-surface-400)] mb-5">
          Are you sure you want to {action} <span className="text-white font-bold">{strategy.name}</span>?
        </p>
        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-xl text-xs font-bold border border-[var(--color-surface-700)] text-[var(--color-surface-400)] hover:text-white transition-colors cursor-pointer">
            Cancel
          </button>
          <button
            onClick={() => { onConfirm(); onClose(); }}
            className={`flex-1 py-2.5 rounded-xl text-xs font-bold text-white transition-colors cursor-pointer ${action === 'stop' ? 'bg-[var(--color-loss)] hover:opacity-90' : 'bg-[var(--color-profit)] hover:opacity-90'}`}
          >
            {action === 'stop' ? 'Stop It' : 'Start It'}
          </button>
        </div>
      </div>
    </div>
  );
}

const Strategies = () => {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState({});
  const [editTarget, setEditTarget] = useState(null);
  const [confirmTarget, setConfirmTarget] = useState(null);

  const load = useCallback(() => {
    fetch(`${API_URL}/api/test/strategies`)
      .then(r => { if (!r.ok) throw new Error('Failed'); return r.json(); })
      .then(d => { setStrategies(d); setLoading(false); })
      .catch(err => { setError('Failed to load strategies'); setLoading(false); });
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggleExpand = (id) => setExpanded(e => ({ ...e, [id]: !e[id] }));

  const handleToggleStatus = (strategy) => {
    setStrategies(prev =>
      prev.map(s => s.id === strategy.id
        ? { ...s, status: s.status === 'active' ? 'inactive' : 'active' }
        : s
      )
    );
  };

  const handleSaveParams = (id, params) => {
    // TODO: POST to API
    console.log('Save params for strategy', id, params);
  };

  return (
    <div className="flex flex-col gap-6 min-h-[calc(100vh-140px)] p-2 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h2 className="text-2xl font-heading font-bold text-white flex items-center gap-3">
          <Cpu className="text-[var(--color-gold-500)]" size={26} />
          Trading Strategies
        </h2>
        <div className="flex items-center gap-3">
          <span className="text-xs text-[var(--color-surface-500)]">
            {strategies.filter(s => s.status === 'active').length} active / {strategies.length} total
          </span>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center flex-1 py-20">
          <Loader className="animate-spin text-[var(--color-gold-500)]" size={28} />
        </div>
      ) : error ? (
        <div className="flex items-center justify-center flex-1 py-20 text-sm text-[var(--color-loss)]">{error}</div>
      ) : strategies.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 py-20 gap-3">
          <Cpu size={36} className="text-[var(--color-surface-700)]" />
          <p className="text-sm text-[var(--color-surface-500)]">No strategies found. Start the bot to load strategies.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {strategies.map((strategy) => {
            const isActive = strategy.status === 'active';
            const isExpanded = expanded[strategy.id];
            const profitPositive = strategy.profit?.startsWith('+') || (parseFloat(strategy.profit?.replace(/[^0-9.-]/g, '')) >= 0);

            return (
              <div
                key={strategy.id}
                className="bg-[var(--color-surface-900)]/60 backdrop-blur-md border border-[var(--color-surface-800)] hover:border-[var(--color-surface-700)] rounded-2xl transition-all duration-300 flex flex-col group overflow-hidden"
              >
                {/* Active Indicator */}
                <div className={`h-0.5 w-full ${isActive ? 'bg-gradient-to-r from-[var(--color-gold-600)] to-[var(--color-gold-400)]' : 'bg-[var(--color-surface-800)]'}`} />

                <div className="p-5 flex flex-col gap-4">
                  {/* Top Row */}
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-xl ${isActive ? 'bg-[var(--color-gold-500)]/15 text-[var(--color-gold-500)]' : 'bg-[var(--color-surface-800)] text-[var(--color-surface-500)]'}`}>
                        <Zap size={18} />
                      </div>
                      <div>
                        <h3 className="font-bold text-white text-base">{strategy.name}</h3>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] font-mono text-[var(--color-surface-400)]">{strategy.type}</span>
                          <span className="text-[var(--color-surface-700)]">•</span>
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${isActive ? 'bg-[var(--color-profit)]/10 text-[var(--color-profit)]' : 'bg-[var(--color-surface-800)] text-[var(--color-surface-500)]'}`}>
                            {isActive ? 'ACTIVE' : 'INACTIVE'}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => setEditTarget(strategy)}
                      className="p-1.5 rounded-lg text-[var(--color-surface-500)] hover:text-white hover:bg-[var(--color-surface-800)] transition-colors cursor-pointer"
                    >
                      <Settings2 size={15} />
                    </button>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-[var(--color-surface-400)] leading-relaxed">{strategy.description}</p>

                  {/* Mini Stats */}
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-[var(--color-surface-900)]/50 rounded-lg px-2 py-2 text-center border border-[var(--color-surface-800)]/50">
                      <p className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] mb-0.5">PnL</p>
                      <p className={`text-xs font-mono font-bold ${profitPositive ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>{strategy.profit}</p>
                    </div>
                    <div className="bg-[var(--color-surface-900)]/50 rounded-lg px-2 py-2 text-center border border-[var(--color-surface-800)]/50">
                      <p className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] mb-0.5">Risk</p>
                      <p className={`text-xs font-mono font-bold ${strategy.risk === 'High' ? 'text-[var(--color-loss)]' : strategy.risk === 'Medium' ? 'text-[var(--color-gold-500)]' : 'text-[var(--color-profit)]'}`}>{strategy.risk}</p>
                    </div>
                    <div className="bg-[var(--color-surface-900)]/50 rounded-lg px-2 py-2 text-center border border-[var(--color-surface-800)]/50">
                      <p className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] mb-0.5">Type</p>
                      <p className="text-[9px] font-bold text-[var(--color-surface-300)] truncate">Stat.Arb</p>
                    </div>
                  </div>

                  {/* Expandable Parameters */}
                  <button
                    onClick={() => toggleExpand(strategy.id)}
                    className="flex items-center justify-between w-full px-3 py-2 rounded-lg bg-[var(--color-surface-900)]/50 border border-[var(--color-surface-800)]/50 text-[10px] font-bold uppercase tracking-wider text-[var(--color-surface-400)] hover:text-white hover:border-[var(--color-surface-700)] transition-colors cursor-pointer"
                  >
                    <span>Parameters</span>
                    {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                  </button>

                  {isExpanded && (
                    <div className="rounded-xl border border-[var(--color-surface-800)]/50 px-4 py-2 bg-[var(--color-surface-950)]/50 animate-fade-in-up">
                      <ParamRow label="Entry Threshold" value="2.0" unit="σ" />
                      <ParamRow label="Exit Threshold" value="0.5" unit="σ" />
                      <ParamRow label="Stop Threshold" value="3.0" unit="σ" />
                      <ParamRow label="Lookback" value="100" unit=" bars" />
                      <ParamRow label="Risk / Trade" value="1.0" unit="%" />
                    </div>
                  )}

                  {/* Bottom Controls */}
                  <div className="flex items-center gap-2 pt-2 border-t border-[var(--color-surface-800)]/50">
                    <Shield size={13} className={strategy.risk === 'High' ? 'text-[var(--color-loss)]' : strategy.risk === 'Medium' ? 'text-[var(--color-gold-500)]' : 'text-[var(--color-profit)]'} />
                    <span className="text-[10px] text-[var(--color-surface-400)] flex-1">{strategy.risk} Risk</span>
                    <button
                      onClick={() => setConfirmTarget({ strategy, action: isActive ? 'stop' : 'start' })}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-colors border cursor-pointer ${
                        isActive
                          ? 'bg-[var(--color-loss-dim)]/50 border-[var(--color-loss)]/30 text-[var(--color-loss)] hover:bg-[var(--color-loss-dim)]'
                          : 'bg-[var(--color-surface-800)] border-[var(--color-surface-700)] text-[var(--color-surface-300)] hover:text-white hover:border-[var(--color-surface-600)]'
                      }`}
                    >
                      {isActive ? <><Square size={10} fill="currentColor" /> Stop</> : <><Play size={10} fill="currentColor" /> Start</>}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Edit Modal */}
      {editTarget && (
        <EditModal
          strategy={editTarget}
          onClose={() => setEditTarget(null)}
          onSave={handleSaveParams}
        />
      )}

      {/* Confirm Modal */}
      {confirmTarget && (
        <ConfirmModal
          strategy={confirmTarget.strategy}
          action={confirmTarget.action}
          onConfirm={() => handleToggleStatus(confirmTarget.strategy)}
          onClose={() => setConfirmTarget(null)}
        />
      )}
    </div>
  );
};

export default Strategies;

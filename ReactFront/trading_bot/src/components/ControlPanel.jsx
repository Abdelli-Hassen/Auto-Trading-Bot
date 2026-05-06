import React, { useState, useEffect } from 'react';
import { Activity, Zap, Play, Square, AlertTriangle, ChevronDown, ToggleLeft, ToggleRight, Clock, TrendingUp } from 'lucide-react';
import Tooltip from './Tooltip';

const SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'];
const MODES = ['Live', 'Paper'];

export default function ControlPanel({ status, isConnected, onStart, onStop, onLiquidate, symbol, onSymbolChange }) {
  const isRunning = status?.running || false;
  const risk = status?.risk_metrics || {};
  const daily = status?.daily_stats || {};

  const [mode, setMode] = useState('Live');
  const [showSymbolDropdown, setShowSymbolDropdown] = useState(false);
  const [sessionSeconds, setSessionSeconds] = useState(0);
  const [isExpanded, setIsExpanded] = useState(true);

  // Session timer
  useEffect(() => {
    if (!isRunning) { setSessionSeconds(0); return; }
    const id = setInterval(() => setSessionSeconds(s => s + 1), 1000);
    return () => clearInterval(id);
  }, [isRunning]);

  const formatSession = (s) => {
    const h = Math.floor(s / 3600).toString().padStart(2, '0');
    const m = Math.floor((s % 3600) / 60).toString().padStart(2, '0');
    const sec = (s % 60).toString().padStart(2, '0');
    return `${h}:${m}:${sec}`;
  };

  const dailyPnl = daily.pnl || 0;
  const dailyTrades = daily.trades || 0;
  const winRate = daily.win_rate || 0;
  const drawdown = risk.current_drawdown || 0;
  const maxDrawdown = 0.03; // from config

  return (
    <div className="glass-strong rounded-2xl flex flex-col gap-0 animate-fade-in-up overflow-hidden" style={{ animationDelay: '0.2s' }}>
      {/* Header */}
      <Tooltip wrapperClass="w-full" position="bottom" content="The core AI trading engine. 'Standby' means it is disconnected or paused. 'Session' shows how long it has been actively trading.">
        <div 
          className="px-5 py-4 border-b border-[var(--color-surface-800)]/60 bg-[var(--color-surface-900)]/30 flex justify-between items-center cursor-pointer transition-colors hover:bg-[var(--color-surface-800)]/40"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center transition-colors duration-500 ${isConnected ? 'bg-[var(--color-gold-500)]/20 border border-[var(--color-gold-500)]/30' : 'bg-[var(--color-surface-800)] border border-[var(--color-surface-700)]'}`}>
              <Zap size={18} className={isConnected ? 'text-[var(--color-gold-400)]' : 'text-[var(--color-surface-500)]'} />
            </div>
            <div>
              <h2 className="text-sm font-heading font-bold text-white tracking-widest">AI ENGINE</h2>
              <p className="text-[10px] text-[var(--color-surface-500)] mt-0.5">{isRunning ? `Session ${formatSession(sessionSeconds)}` : 'Standby'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[var(--color-profit)] animate-pulse-soft' : 'bg-[var(--color-loss)]'}`} />
            <span className="text-[10px] font-bold tracking-wider uppercase text-[var(--color-surface-400)] mr-2">
              {isConnected ? 'Live' : 'Offline'}
            </span>
            <ChevronDown size={16} className={`text-[var(--color-surface-400)] transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} />
          </div>
        </div>
      </Tooltip>

      {isExpanded && (
      <div className="p-5 flex flex-col gap-4">
        {/* Symbol + Mode Row */}
        <div className="grid grid-cols-2 gap-3">
          {/* Symbol Selector */}
          <div className="relative">
            <p className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1.5 font-medium">Symbol</p>
            <button
              onClick={() => setShowSymbolDropdown(v => !v)}
              className="w-full flex items-center justify-between px-3 py-2 bg-[var(--color-surface-900)]/60 border border-[var(--color-surface-700)] rounded-lg text-sm font-mono text-white hover:border-[var(--color-gold-500)]/40 transition-colors cursor-pointer"
            >
              <span>{symbol || 'BTC/USDT'}</span>
              <ChevronDown size={14} className={`text-[var(--color-surface-400)] transition-transform ${showSymbolDropdown ? 'rotate-180' : ''}`} />
            </button>
            {showSymbolDropdown && (
              <div className="absolute top-full left-0 right-0 mt-1 z-30 bg-[var(--color-surface-850)] border border-[var(--color-surface-700)] rounded-xl shadow-2xl overflow-hidden">
                {SYMBOLS.map(s => (
                  <button
                    key={s}
                    onClick={() => { onSymbolChange?.(s); setShowSymbolDropdown(false); }}
                    className={`w-full text-left px-4 py-2.5 text-sm font-mono hover:bg-[var(--color-surface-800)] transition-colors cursor-pointer ${s === symbol ? 'text-[var(--color-gold-400)] bg-[var(--color-surface-800)]/50' : 'text-[var(--color-surface-300)]'}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Mode Selector */}
          <Tooltip wrapperClass="w-full" position="bottom" content="Paper mode simulates trades without risking real money. Live mode places actual orders on the exchange.">
            <div>
              <p className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1.5 font-medium">Mode</p>
              <div className="flex gap-1 bg-[var(--color-surface-900)]/60 border border-[var(--color-surface-700)] rounded-lg p-1">
                {MODES.map(m => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    className={`flex-1 py-1.5 rounded-md text-xs font-bold tracking-wider transition-all cursor-pointer ${mode === m ? 'bg-[var(--color-gold-600)] text-black shadow-sm' : 'text-[var(--color-surface-400)] hover:text-white'}`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>
          </Tooltip>
        </div>

        {/* Status Banner */}
        <div className={`rounded-xl px-4 py-3 text-center transition-all duration-500 ${
          isRunning
            ? 'bg-[var(--color-profit-dim)]/40 border border-[var(--color-profit)]/20'
            : 'bg-[var(--color-surface-900)]/50 border border-[var(--color-surface-800)]'
        }`}>
          <div className="flex items-center justify-center gap-2">
            <Activity size={14} className={isRunning ? 'text-[var(--color-profit)] animate-pulse' : 'text-[var(--color-surface-500)]'} />
            <span className={`text-sm font-heading font-bold tracking-widest ${isRunning ? 'text-[var(--color-profit)]' : 'text-[var(--color-surface-500)]'}`}>
              {isRunning ? 'BOT ACTIVE' : 'BOT STOPPED'}
            </span>
          </div>
        </div>

        {/* Live Risk Row */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-[var(--color-surface-900)]/50 rounded-lg px-3 py-2 border border-[var(--color-surface-800)]/50">
            <p className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1">Daily PnL</p>
            <p className={`text-sm font-mono font-bold ${dailyPnl >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
              {dailyPnl >= 0 ? '+' : ''}${dailyPnl.toFixed(2)}
            </p>
          </div>
          <div className="bg-[var(--color-surface-900)]/50 rounded-lg px-3 py-2 border border-[var(--color-surface-800)]/50">
            <p className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1">Trades</p>
            <p className="text-sm font-mono font-bold text-white">{dailyTrades}</p>
          </div>
          <div className="bg-[var(--color-surface-900)]/50 rounded-lg px-3 py-2 border border-[var(--color-surface-800)]/50">
            <p className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1">Win Rate</p>
            <p className="text-sm font-mono font-bold text-[var(--color-gold-400)]">{(winRate * 100).toFixed(0)}%</p>
          </div>
        </div>

        {/* Drawdown Gauge */}
        <Tooltip wrapperClass="w-full" position="top" content="Drawdown measures the current loss from your highest peak balance. If it hits the limit, the bot automatically stops to protect your funds.">
          <div>
          <div className="flex justify-between items-center mb-1.5">
            <p className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)] font-medium">Drawdown Risk</p>
            <p className="text-[10px] font-mono text-[var(--color-surface-400)]">
              {(drawdown * 100).toFixed(2)}% / {(maxDrawdown * 100).toFixed(0)}% limit
            </p>
          </div>
          <div className="h-1.5 rounded-full bg-[var(--color-surface-800)] overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${Math.min((drawdown / maxDrawdown) * 100, 100)}%`,
                background: drawdown > maxDrawdown * 0.8
                  ? 'var(--color-loss)'
                  : drawdown > maxDrawdown * 0.5
                  ? 'var(--color-gold-500)'
                  : 'var(--color-profit)'
              }}
            />
          </div>
        </div>
        </Tooltip>
        </div>
      )}

      {/* Action Buttons Always Visible */}
      <div className={`p-5 flex flex-col gap-3 ${isExpanded ? 'pt-0' : ''}`}>
        <div className="grid grid-cols-2 gap-3">
          <Tooltip wrapperClass="w-full" position="top" content="Starts the AI engine. It will begin analyzing data and placing trades according to your current Mode (Live/Paper).">
            <button
            onClick={onStart}
            disabled={isRunning || !isConnected}
            className={`btn-primary flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-heading font-bold text-xs tracking-wider transition-all duration-300 ${
              isRunning || !isConnected
                ? 'bg-[var(--color-surface-800)] text-[var(--color-surface-600)] cursor-not-allowed border border-[var(--color-surface-700)]'
                : 'bg-gradient-to-r from-[var(--color-profit)] to-emerald-400 text-white cursor-pointer glow-profit border border-emerald-400/50'
            }`}
          >
            <Play size={14} fill="currentColor" />
            START
            </button>
          </Tooltip>
          <Tooltip wrapperClass="w-full" position="top" content="Safely halts the AI engine. It will stop opening new positions, but it will NOT automatically close existing ones unless they hit their take-profit or stop-loss.">
            <button
            onClick={onStop}
            disabled={!isRunning || !isConnected}
            className={`btn-primary flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-heading font-bold text-xs tracking-wider transition-all duration-300 ${
              !isRunning || !isConnected
                ? 'bg-[var(--color-surface-800)] text-[var(--color-surface-600)] cursor-not-allowed border border-[var(--color-surface-700)]'
                : 'bg-[var(--color-surface-800)] hover:bg-[var(--color-loss)] text-[var(--color-surface-300)] hover:text-white cursor-pointer border border-[var(--color-surface-700)] hover:border-[var(--color-loss)]'
            }`}
          >
            <Square size={12} fill="currentColor" />
            STOP
            </button>
          </Tooltip>
        </div>

        {/* Emergency Liquidate */}
        <Tooltip wrapperClass="w-full" position="top" content="PANIC BUTTON. Immediately force-closes all open positions at market price and halts the bot. Use only in extreme market conditions to prevent further loss.">
          <button
          onClick={onLiquidate}
          disabled={!isRunning || !isConnected}
          className={`w-full py-3 rounded-xl text-xs font-heading font-bold tracking-widest transition-all duration-300 flex justify-center items-center gap-2 ${
            !isRunning || !isConnected
              ? 'bg-[var(--color-surface-900)]/50 text-[var(--color-surface-700)] border border-[var(--color-surface-800)] cursor-not-allowed'
              : 'bg-[var(--color-loss-dim)] hover:bg-[var(--color-loss)] text-[var(--color-loss)] hover:text-white border border-[var(--color-loss)]/30 hover:border-[var(--color-loss)] cursor-pointer'
          }`}
        >
          <AlertTriangle size={14} />
          EMERGENCY LIQUIDATE
        </button>
        </Tooltip>
      </div>
    </div>
  );
}

import React, { useState, useEffect, useMemo } from 'react';
import {
  History as HistoryIcon, ArrowUpRight, ArrowDownRight, Search, Filter, Loader,
  ChevronDown, ChevronUp, Download, ChevronLeft, ChevronRight, Maximize2
} from 'lucide-react';

import { API_URL } from '../api';

export default function History() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [sideFilter, setSideFilter] = useState('All'); // All, Buy, Sell
  const [symbolFilter, setSymbolFilter] = useState('All');

  // Sort
  const [sortConfig, setSortConfig] = useState({ key: 'rawId', direction: 'desc' });

  // Pagination
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(15);

  // Expand
  const [expandedRow, setExpandedRow] = useState(null);

  useEffect(() => {
    const load = () => {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 8000);
      fetch(`${API_URL}/api/test/history`, { signal: controller.signal })
        .then(r => { if (!r.ok) throw new Error('Failed'); return r.json(); })
        .then(d => { clearTimeout(timeout); setTrades(d); setError(null); setLoading(false); })
        .catch(() => { clearTimeout(timeout); setError('Cannot reach the trading engine.'); setLoading(false); });
    };
    load();
    const id = setInterval(load, 8000);       // new fills appear without a refresh
    return () => clearInterval(id);
  }, []);

  // Compute unique symbols for filter dropdown
  const uniqueSymbols = useMemo(() => {
    const syms = new Set(trades.map(t => t.symbol).filter(s => s && s !== '—'));
    return ['All', ...Array.from(syms)];
  }, [trades]);

  // Compute stats
  const stats = useMemo(() => {
    const exits = trades.filter(t => t.kind === 'close' || t.kind === 'reduce');   // every fill that realised profit/loss
    const closed = trades.filter(t => t.kind === 'close');                         // fully closed trades only
    const wins = closed.filter(t => t.rawPnl > 0);
    const totalPnl = exits.reduce((acc, t) => acc + (t.rawPnl || 0), 0);
    return {
      total: trades.length,
      closed: closed.length,
      winRate: closed.length > 0 ? (wins.length / closed.length) * 100 : 0,
      pnl: totalPnl
    };
  }, [trades]);

  // Apply Filter & Sort
  const processedTrades = useMemo(() => {
    let result = [...trades];

    // Search
    if (search) {
      const lower = search.toLowerCase();
      result = result.filter(t => t.id.toLowerCase().includes(lower) || t.symbol.toLowerCase().includes(lower));
    }

    // Side filter
    if (sideFilter !== 'All') {
      result = result.filter(t => t.type === sideFilter);
    }

    // Symbol filter
    if (symbolFilter !== 'All') {
      result = result.filter(t => t.symbol === symbolFilter);
    }

    // Sort
    if (sortConfig.key) {
      result.sort((a, b) => {
        let valA = a[sortConfig.key];
        let valB = b[sortConfig.key];

        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();

        if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
        if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return result;
  }, [trades, search, sideFilter, symbolFilter, sortConfig]);

  // Pagination
  const totalPages = Math.ceil(processedTrades.length / perPage);
  const currentData = processedTrades.slice((page - 1) * perPage, page * perPage);

  // Reset page when filters change
  useEffect(() => { setPage(1); }, [search, sideFilter, symbolFilter]);

  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') direction = 'desc';
    setSortConfig({ key, direction });
  };

  const exportCSV = () => {
    if (processedTrades.length === 0) return;
    const headers = ['ID', 'Time', 'Symbol', 'Side', 'Amount', 'Price', 'Fee', 'Notional', 'Realised PnL', 'Status'];
    const rows = processedTrades.map(t => [
      t.id, t.timestamp, t.symbol, t.type, t.rawAmount, t.rawPrice, t.fee, t.rawCost, t.rawPnl, t.status
    ]);
    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', 'trade_history.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const SortIcon = ({ col }) => {
    if (sortConfig.key !== col) return null;
    return sortConfig.direction === 'asc' ? <ChevronUp size={12} className="ml-1 inline" /> : <ChevronDown size={12} className="ml-1 inline" />;
  };

  return (
    <div className="flex flex-col min-h-[500px] animate-fade-in bg-[var(--color-surface-900)]/40 rounded-2xl border border-[var(--color-surface-800)]/60 overflow-hidden backdrop-blur-md">
      {/* Header & Filters */}
      <div className="p-4 border-b border-[var(--color-surface-800)]/80 flex flex-col gap-3 shrink-0">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-heading font-bold text-white flex items-center gap-3">
            <HistoryIcon className="text-[var(--color-gold-500)]" size={20} />
            Trade History
          </h2>
          <button
            onClick={exportCSV}
            disabled={processedTrades.length === 0}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--color-surface-800)] border border-[var(--color-surface-700)] text-[9px] font-bold uppercase tracking-wider text-[var(--color-surface-300)] hover:text-white hover:border-[var(--color-gold-500)]/50 transition-all disabled:opacity-50 cursor-pointer"
          >
            <Download size={12} />
            Export
          </button>
        </div>

        {/* Filters Row */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-surface-500)]" />
            <input
              type="text"
              placeholder="Search ID or Symbol..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-[var(--color-surface-950)] border border-[var(--color-surface-700)] rounded-lg pl-9 pr-4 py-1.5 text-[11px] font-mono focus:outline-none focus:border-[var(--color-gold-500)]/50 transition-colors text-white"
            />
          </div>
          
          <select
            value={sideFilter}
            onChange={e => setSideFilter(e.target.value)}
            className="bg-[var(--color-surface-950)] border border-[var(--color-surface-700)] rounded-lg px-3 py-1.5 text-[10px] font-bold text-[var(--color-surface-400)] focus:outline-none cursor-pointer hover:border-[var(--color-surface-600)] transition-colors"
          >
            <option value="All">All Sides</option>
            <option value="Buy">Buy Only</option>
            <option value="Sell">Sell Only</option>
          </select>

          <select
            value={symbolFilter}
            onChange={e => setSymbolFilter(e.target.value)}
            className="bg-[var(--color-surface-950)] border border-[var(--color-surface-700)] rounded-lg px-3 py-1.5 text-[10px] font-bold text-[var(--color-surface-400)] focus:outline-none cursor-pointer hover:border-[var(--color-surface-600)] transition-colors"
          >
            {uniqueSymbols.map(s => <option key={s} value={s}>{s === 'All' ? 'All Symbols' : s}</option>)}
          </select>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-3 gap-2 bg-[var(--color-surface-950)]/40 rounded-xl p-2 border border-[var(--color-surface-800)]/50">
          <div className="flex items-center justify-between px-2">
            <span className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] font-bold">Total</span>
            <span className="font-mono text-[11px] font-bold text-white">{stats.total}</span>
          </div>
          <div className="flex items-center justify-between border-l border-[var(--color-surface-800)]/50 px-2">
            <span className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] font-bold" title="Fully closed trades that made money">Win Rate (closed trades)</span>
            <span className="font-mono text-[11px] font-bold text-[var(--color-gold-400)]">{stats.closed ? `${stats.winRate.toFixed(1)}%` : '—'}</span>
          </div>
          <div className="flex items-center justify-between border-l border-[var(--color-surface-800)]/50 px-2">
            <span className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] font-bold">Realised PnL</span>
            <span className={`font-mono text-[11px] font-bold ${stats.pnl >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
              {stats.pnl >= 0 ? '+' : ''}${stats.pnl.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Table Area */}
      <div className="overflow-x-auto">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader className="animate-spin text-[var(--color-gold-500)]" size={32} />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-16 text-sm text-[var(--color-loss)] font-mono uppercase tracking-tighter">{error}</div>
        ) : (
          <table className="w-full text-left text-[11px] whitespace-nowrap">
            <thead className="bg-[var(--color-surface-900)] sticky top-0 z-10 border-b border-[var(--color-surface-800)]/80 shadow-sm">
              <tr>
                <th className="px-4 py-2 cursor-pointer hover:bg-[var(--color-surface-800)]/50 transition-colors group" onClick={() => requestSort('timestamp')}>
                  <span className="font-bold text-[var(--color-surface-500)] group-hover:text-white uppercase tracking-widest text-[9px]">Time <SortIcon col="timestamp" /></span>
                </th>
                <th className="px-4 py-2 cursor-pointer hover:bg-[var(--color-surface-800)]/50 transition-colors group" onClick={() => requestSort('symbol')}>
                  <span className="font-bold text-[var(--color-surface-500)] group-hover:text-white uppercase tracking-widest text-[9px]">Symbol <SortIcon col="symbol" /></span>
                </th>
                <th className="px-4 py-2 cursor-pointer hover:bg-[var(--color-surface-800)]/50 transition-colors group" onClick={() => requestSort('type')}>
                  <span className="font-bold text-[var(--color-surface-500)] group-hover:text-white uppercase tracking-widest text-[9px]">Side <SortIcon col="type" /></span>
                </th>
                <th className="px-4 py-2 text-right cursor-pointer hover:bg-[var(--color-surface-800)]/50 transition-colors group" onClick={() => requestSort('rawPrice')}>
                  <span className="font-bold text-[var(--color-surface-500)] group-hover:text-white uppercase tracking-widest text-[9px]">Price <SortIcon col="rawPrice" /></span>
                </th>
                <th className="px-4 py-2 text-right cursor-pointer hover:bg-[var(--color-surface-800)]/50 transition-colors group" onClick={() => requestSort('rawPnl')}>
                  <span className="font-bold text-[var(--color-surface-500)] group-hover:text-white uppercase tracking-widest text-[9px]">P&L <SortIcon col="rawPnl" /></span>
                </th>
                <th className="px-4 py-2 w-8"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-surface-800)]/20">
              {currentData.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center">
                    <HistoryIcon size={24} className="mx-auto text-[var(--color-surface-700)] mb-2" />
                    <p className="text-[var(--color-surface-500)] text-[10px] uppercase font-bold tracking-widest">{trades.length === 0 ? 'No trades yet — they appear here as soon as the bot trades' : 'No matching trades'}</p>
                  </td>
                </tr>
              ) : (
                currentData.map((trade) => {
                  const isExpanded = expandedRow === trade.id;
                  const isBuy = trade.type === 'Buy';
                  const isPositive = (trade.rawPnl || 0) >= 0;

                  return (
                    <React.Fragment key={trade.id}>
                      <tr 
                        className={`hover:bg-[var(--color-surface-800)]/40 transition-colors cursor-pointer group ${isExpanded ? 'bg-[var(--color-surface-800)]/20' : ''}`}
                        onClick={() => setExpandedRow(isExpanded ? null : trade.id)}
                      >
                        <td className="px-4 py-2">
                          <span className="text-[var(--color-surface-300)] font-mono">{trade.time}</span>
                        </td>
                        <td className="px-4 py-2 font-mono font-bold text-white tracking-tighter">{trade.symbol}</td>
                        <td className="px-4 py-2">
                          <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-[4px] text-[9px] font-bold uppercase tracking-widest ${isBuy ? 'text-[var(--color-profit)] bg-[var(--color-profit)]/10 border border-[var(--color-profit)]/20' : 'text-[var(--color-loss)] bg-[var(--color-loss)]/10 border border-[var(--color-loss)]/20'}`}>
                            {trade.type}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right font-mono text-[var(--color-surface-400)]">{trade.price}</td>
                        <td className={`px-4 py-2 text-right font-mono font-bold ${isPositive ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                          {trade.pnl}
                        </td>
                        <td className="px-4 py-2 text-center text-[var(--color-surface-600)] group-hover:text-white transition-colors">
                          <Maximize2 size={12} className={`transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} />
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-[var(--color-surface-950)]/50">
                          <td colSpan={6} className="px-6 py-4 border-t border-[var(--color-surface-800)]/30">
                            <div className="grid grid-cols-4 gap-6 p-1">
                              <div>
                                <p className="text-[8px] uppercase tracking-widest text-[var(--color-surface-500)] font-bold mb-1">Trade ID</p>
                                <p className="text-[10px] font-mono font-medium text-white break-all">{trade.id}</p>
                              </div>
                              <div>
                                <p className="text-[8px] uppercase tracking-widest text-[var(--color-surface-500)] font-bold mb-1">Fee</p>
                                <p className="text-[10px] font-mono text-[var(--color-surface-300)]">{trade.fee}</p>
                              </div>
                              <div>
                                <p className="text-[8px] uppercase tracking-widest text-[var(--color-surface-500)] font-bold mb-1">Amount</p>
                                <p className="text-[10px] font-mono text-[var(--color-surface-300)]">{trade.amount}</p>
                              </div>
                              <div>
                                <p className="text-[8px] uppercase tracking-widest text-[var(--color-surface-500)] font-bold mb-1">Status</p>
                                <div className="flex items-center gap-1.5">
                                  <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-profit)]" />
                                  <p className="text-[10px] font-bold text-white uppercase">{trade.status || 'closed'}</p>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Footer */}
      <div className="px-4 py-2 border-t border-[var(--color-surface-800)]/80 bg-[var(--color-surface-900)]/30 flex justify-between items-center text-[10px] text-[var(--color-surface-500)] font-bold uppercase tracking-widest shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span>Show</span>
            <select
              value={perPage}
              onChange={e => { setPerPage(Number(e.target.value)); setPage(1); }}
              className="bg-[var(--color-surface-800)] border border-[var(--color-surface-700)] rounded px-2 py-0.5 focus:outline-none text-white cursor-pointer"
            >
              <option value={15}>15</option>
              <option value={50}>50</option>
            </select>
          </div>
          <span className="hidden sm:inline opacity-50">•</span>
          <span className="hidden sm:inline">Page {page} of {totalPages || 1}</span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="p-1 rounded bg-[var(--color-surface-800)] hover:bg-[var(--color-surface-700)] disabled:opacity-30 transition-colors cursor-pointer border border-[var(--color-surface-700)]"
          >
            <ChevronLeft size={14} />
          </button>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages || totalPages === 0}
            className="p-1 rounded bg-[var(--color-surface-800)] hover:bg-[var(--color-surface-700)] disabled:opacity-30 transition-colors cursor-pointer border border-[var(--color-surface-700)]"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

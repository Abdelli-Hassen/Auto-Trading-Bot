import React, { useState, useEffect, useMemo } from 'react';
import {
  History as HistoryIcon, ArrowUpRight, ArrowDownRight, Search, Filter, Loader,
  ChevronDown, ChevronUp, Download, ChevronLeft, ChevronRight, Maximize2
} from 'lucide-react';

const API_URL = 'http://localhost:8000';

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
    fetch(`${API_URL}/api/test/history`)
      .then(r => { if (!r.ok) throw new Error('Failed'); return r.json(); })
      .then(d => { setTrades(d); setLoading(false); })
      .catch(err => { setError('Failed to load history'); setLoading(false); });
  }, []);

  // Compute unique symbols for filter dropdown
  const uniqueSymbols = useMemo(() => {
    const syms = new Set(trades.map(t => t.symbol).filter(s => s && s !== '—'));
    return ['All', ...Array.from(syms)];
  }, [trades]);

  // Compute stats
  const stats = useMemo(() => {
    const closed = trades.filter(t => t.status === 'closed');
    const wins = closed.filter(t => t.rawCost > 0); // simplistic assumption for test
    const totalPnl = closed.reduce((acc, t) => acc + (t.rawCost || 0), 0);
    return {
      total: trades.length,
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
    const headers = ['ID', 'Time', 'Symbol', 'Side', 'Amount', 'Price', 'Fee', 'Cost (PnL)', 'Status'];
    const rows = processedTrades.map(t => [
      t.id, t.time, t.symbol, t.type, t.rawAmount, t.rawPrice, t.fee, t.rawCost, t.status
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
    <div className="flex flex-col min-h-[calc(100vh-140px)] animate-fade-in bg-[var(--color-surface-900)]/40 rounded-2xl border border-[var(--color-surface-800)]/60 overflow-hidden backdrop-blur-md">
      {/* Header & Filters */}
      <div className="p-5 border-b border-[var(--color-surface-800)]/80 flex flex-col gap-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-heading font-bold text-white flex items-center gap-3">
            <HistoryIcon className="text-[var(--color-gold-500)]" size={24} />
            Trade History
          </h2>
          <button
            onClick={exportCSV}
            disabled={processedTrades.length === 0}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--color-surface-800)] border border-[var(--color-surface-700)] text-[10px] font-bold uppercase tracking-wider text-[var(--color-surface-300)] hover:text-white hover:bg-[var(--color-surface-700)] transition-colors disabled:opacity-50 cursor-pointer"
          >
            <Download size={14} />
            Export CSV
          </button>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-3 gap-3 bg-[var(--color-surface-900)]/50 rounded-xl p-3 border border-[var(--color-surface-800)]/50">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)] font-medium">Total Trades</span>
            <span className="font-mono font-bold text-white">{stats.total}</span>
          </div>
          <div className="flex items-center justify-between border-l border-[var(--color-surface-800)] pl-3">
            <span className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)] font-medium">Win Rate</span>
            <span className="font-mono font-bold text-[var(--color-gold-400)]">{stats.winRate.toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between border-l border-[var(--color-surface-800)] pl-3">
            <span className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)] font-medium">Realized PnL</span>
            <span className={`font-mono font-bold ${stats.pnl >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
              {stats.pnl >= 0 ? '+' : ''}${stats.pnl.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Filters Row */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-surface-500)]" />
            <input
              type="text"
              placeholder="Search ID or Symbol..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-[var(--color-surface-950)] border border-[var(--color-surface-700)] rounded-lg pl-9 pr-4 py-2 text-xs font-mono focus:outline-none focus:border-[var(--color-gold-500)]/50 transition-colors text-white"
            />
          </div>
          
          <select
            value={sideFilter}
            onChange={e => setSideFilter(e.target.value)}
            className="bg-[var(--color-surface-950)] border border-[var(--color-surface-700)] rounded-lg px-3 py-2 text-xs font-mono text-[var(--color-surface-300)] focus:outline-none cursor-pointer"
          >
            <option value="All">All Sides</option>
            <option value="Buy">Buy Only</option>
            <option value="Sell">Sell Only</option>
          </select>

          <select
            value={symbolFilter}
            onChange={e => setSymbolFilter(e.target.value)}
            className="bg-[var(--color-surface-950)] border border-[var(--color-surface-700)] rounded-lg px-3 py-2 text-xs font-mono text-[var(--color-surface-300)] focus:outline-none cursor-pointer"
          >
            {uniqueSymbols.map(s => <option key={s} value={s}>{s === 'All' ? 'All Symbols' : s}</option>)}
          </select>
        </div>
      </div>

      {/* Table Area */}
      <div className="flex-1 overflow-auto relative">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <Loader className="animate-spin text-[var(--color-gold-500)]" size={32} />
          </div>
        ) : error ? (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-[var(--color-loss)]">{error}</div>
        ) : (
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead className="bg-[var(--color-surface-900)] sticky top-0 z-10 border-b border-[var(--color-surface-800)]/80 shadow-md">
              <tr>
                <th className="px-4 py-3 cursor-pointer hover:bg-[var(--color-surface-800)]/50 transition-colors group" onClick={() => requestSort('timestamp')}>
                  <span className="font-medium text-[var(--color-surface-400)] group-hover:text-white uppercase tracking-wider text-[10px]">Time <SortIcon col="timestamp" /></span>
                </th>
                <th className="px-4 py-3 cursor-pointer hover:bg-[var(--color-surface-800)]/50 transition-colors group" onClick={() => requestSort('symbol')}>
                  <span className="font-medium text-[var(--color-surface-400)] group-hover:text-white uppercase tracking-wider text-[10px]">Symbol <SortIcon col="symbol" /></span>
                </th>
                <th className="px-4 py-3 cursor-pointer hover:bg-[var(--color-surface-800)]/50 transition-colors group" onClick={() => requestSort('type')}>
                  <span className="font-medium text-[var(--color-surface-400)] group-hover:text-white uppercase tracking-wider text-[10px]">Side <SortIcon col="type" /></span>
                </th>
                <th className="px-4 py-3 cursor-pointer hover:bg-[var(--color-surface-800)]/50 transition-colors group" onClick={() => requestSort('rawAmount')}>
                  <span className="font-medium text-[var(--color-surface-400)] group-hover:text-white uppercase tracking-wider text-[10px]">Amount <SortIcon col="rawAmount" /></span>
                </th>
                <th className="px-4 py-3 cursor-pointer hover:bg-[var(--color-surface-800)]/50 transition-colors group" onClick={() => requestSort('rawPrice')}>
                  <span className="font-medium text-[var(--color-surface-400)] group-hover:text-white uppercase tracking-wider text-[10px]">Price <SortIcon col="rawPrice" /></span>
                </th>
                <th className="px-4 py-3 cursor-pointer hover:bg-[var(--color-surface-800)]/50 transition-colors group text-right" onClick={() => requestSort('rawCost')}>
                  <span className="font-medium text-[var(--color-surface-400)] group-hover:text-white uppercase tracking-wider text-[10px]">P&L <SortIcon col="rawCost" /></span>
                </th>
                <th className="px-4 py-3 w-8"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-surface-800)]/30">
              {currentData.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-16 text-center">
                    <HistoryIcon size={32} className="mx-auto text-[var(--color-surface-700)] mb-3" />
                    <p className="text-[var(--color-surface-500)] text-sm">No trades match your filters</p>
                  </td>
                </tr>
              ) : (
                currentData.map((trade) => {
                  const isExpanded = expandedRow === trade.id;
                  const isBuy = trade.type === 'Buy';
                  const isPositive = (trade.rawCost || 0) >= 0;

                  return (
                    <React.Fragment key={trade.id}>
                      <tr 
                        className={`hover:bg-[var(--color-surface-800)]/40 transition-colors cursor-pointer ${isExpanded ? 'bg-[var(--color-surface-800)]/20' : ''}`}
                        onClick={() => setExpandedRow(isExpanded ? null : trade.id)}
                      >
                        <td className="px-4 py-3">
                          <div className="flex flex-col gap-0.5">
                            <span className="text-[var(--color-surface-300)] font-medium">{trade.time}</span>
                            <span className="text-[9px] text-[var(--color-surface-500)] font-mono">{trade.id}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 font-mono font-bold text-white">{trade.symbol}</td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${isBuy ? 'bg-[var(--color-profit)]/15 text-[var(--color-profit)] border border-[var(--color-profit)]/20' : 'bg-[var(--color-loss)]/15 text-[var(--color-loss)] border border-[var(--color-loss)]/20'}`}>
                            {isBuy ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                            {trade.type}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-[var(--color-surface-300)]">{trade.amount}</td>
                        <td className="px-4 py-3 font-mono text-[var(--color-surface-300)]">{trade.price}</td>
                        <td className={`px-4 py-3 text-right font-mono font-bold ${isPositive ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                          {trade.pnl}
                        </td>
                        <td className="px-4 py-3 text-center text-[var(--color-surface-500)]">
                          <Maximize2 size={14} className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-[var(--color-surface-950)]/50">
                          <td colSpan={7} className="px-4 py-3 border-t border-[var(--color-surface-800)]/30">
                            <div className="grid grid-cols-4 gap-4 p-2">
                              <div>
                                <p className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1">Status</p>
                                <p className="text-xs font-mono font-medium text-white">{trade.status || 'closed'}</p>
                              </div>
                              <div>
                                <p className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1">Fee</p>
                                <p className="text-xs font-mono text-[var(--color-surface-400)]">{trade.fee}</p>
                              </div>
                              <div>
                                <p className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1">Raw Amount</p>
                                <p className="text-xs font-mono text-[var(--color-surface-400)]">{trade.rawAmount}</p>
                              </div>
                              <div>
                                <p className="text-[9px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1">Timestamp</p>
                                <p className="text-[10px] font-mono text-[var(--color-surface-500)]">{trade.timestamp}</p>
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
      <div className="p-3 border-t border-[var(--color-surface-800)]/80 bg-[var(--color-surface-900)]/30 flex justify-between items-center text-xs text-[var(--color-surface-400)]">
        <div className="flex items-center gap-2">
          <span>Show</span>
          <select
            value={perPage}
            onChange={e => { setPerPage(Number(e.target.value)); setPage(1); }}
            className="bg-[var(--color-surface-800)] border border-[var(--color-surface-700)] rounded px-2 py-1 focus:outline-none"
          >
            <option value={15}>15</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span>entries</span>
        </div>
        
        <div className="flex items-center gap-4">
          <span>Showing {(page - 1) * perPage + 1} to {Math.min(page * perPage, processedTrades.length)} of {processedTrades.length} entries</span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded bg-[var(--color-surface-800)] hover:bg-[var(--color-surface-700)] disabled:opacity-50 transition-colors cursor-pointer"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages || totalPages === 0}
              className="p-1.5 rounded bg-[var(--color-surface-800)] hover:bg-[var(--color-surface-700)] disabled:opacity-50 transition-colors cursor-pointer"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

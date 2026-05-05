import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp, TrendingDown, Activity, DollarSign, BarChart3,
  PieChart, Loader, BarChart2, Award, Zap
} from 'lucide-react';

const API_URL = 'http://localhost:8000';
const TIMEFRAMES = [
  { label: '7D', value: '7d' },
  { label: '30D', value: '30d' },
  { label: 'All', value: 'all' },
];

const Analytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState('all');

  const load = useCallback((tf) => {
    setLoading(true);
    fetch(`${API_URL}/api/test/analytics?timeframe=${tf}`)
      .then(r => r.json())
      .then(json => { setData(json); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => { load(timeframe); }, [timeframe]);

  const getIcon = (label) => {
    if (label.includes('Profit') && !label.includes('Factor')) return DollarSign;
    if (label.includes('Rate')) return PieChart;
    if (label.includes('Drawdown')) return Activity;
    if (label.includes('Sharpe')) return Award;
    if (label.includes('Factor')) return Zap;
    return TrendingUp;
  };

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <Loader className="animate-spin text-[var(--color-gold-500)]" size={32} />
    </div>
  );

  if (!data) return <div className="p-4 text-red-500">Failed to load analytics</div>;

  // Build equity SVG path
  const chartData = data.chartData || [];
  const equityPath = (() => {
    if (chartData.length < 2) return { points: '', fill: '' };
    const vals = chartData.map(d => d.value);
    const maxV = Math.max(...vals);
    const minV = Math.min(...vals);
    const range = maxV - minV || 1;
    const pts = vals.map((v, i) => {
      const x = (i / (vals.length - 1)) * 100;
      const y = 100 - ((v - minV) / range) * 80 - 10;
      return `${x},${y}`;
    }).join(' L ');
    return { points: pts, fill: `M 0,100 L ${pts} L 100,100 Z`, maxV, minV };
  })();

  // Daily PnL bars
  const dailyChart = data.dailyChart || [];
  const maxPnl = Math.max(...dailyChart.map(d => Math.abs(d.pnl)), 1);

  return (
    <div className="flex flex-col gap-5 min-h-[calc(100vh-140px)] p-2 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-heading font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-[var(--color-surface-400)] flex items-center gap-3">
          <BarChart3 className="text-[var(--color-gold-500)]" size={26} />
          Performance Analytics
        </h2>
        <div className="flex gap-1 bg-[var(--color-surface-900)]/60 border border-[var(--color-surface-700)] rounded-xl p-1">
          {TIMEFRAMES.map(tf => (
            <button
              key={tf.value}
              onClick={() => setTimeframe(tf.value)}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                timeframe === tf.value
                  ? 'bg-[var(--color-gold-600)] text-black shadow-sm'
                  : 'text-[var(--color-surface-400)] hover:text-white'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* 6-KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {(data.metrics || []).map((metric, i) => {
          const Icon = getIcon(metric.label);
          return (
            <div
              key={i}
              className="bg-[var(--color-surface-900)]/40 backdrop-blur-xl border border-[var(--color-surface-800)]/60 rounded-2xl p-5 flex flex-col relative overflow-hidden group hover:border-[var(--color-gold-500)]/30 hover:bg-[var(--color-surface-900)]/60 transition-all duration-300 hover:-translate-y-0.5 cursor-default"
            >
              <div className="absolute -right-8 -top-8 w-24 h-24 bg-gradient-to-br from-[var(--color-gold-500)] to-transparent rounded-full opacity-[0.03] group-hover:opacity-[0.08] transition-opacity duration-500" />
              <div className="flex justify-between items-start mb-4">
                <div className="p-2 rounded-lg bg-[var(--color-surface-800)] text-[var(--color-gold-500)] border border-[var(--color-surface-700)]/50">
                  <Icon size={16} strokeWidth={2.5} />
                </div>
                <div className={`w-2 h-2 rounded-full mt-1 ${metric.isPositive ? 'bg-[var(--color-profit)]' : 'bg-[var(--color-loss)]'}`} />
              </div>
              <p className="text-[10px] font-medium text-[var(--color-surface-500)] mb-1 tracking-wide uppercase">{metric.label}</p>
              <div className="text-xl font-bold text-white font-mono tracking-tight group-hover:text-[var(--color-gold-400)] transition-colors duration-300">
                {metric.value}
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 min-h-[300px]">
        {/* Equity Curve */}
        <div className="xl:col-span-2 bg-[var(--color-surface-900)]/40 backdrop-blur-xl border border-[var(--color-surface-800)]/60 rounded-2xl p-5 flex flex-col min-h-[350px]">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[var(--color-gold-500)] animate-pulse" />
              Equity Curve
            </h3>
            <span className="text-[10px] font-mono text-[var(--color-surface-500)]">{chartData.length} data points</span>
          </div>
          <div className="flex-1 relative">
            {chartData.length >= 2 ? (
              <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 100 100">
                <defs>
                  <linearGradient id="eqGrad" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-gold-500)" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="var(--color-gold-500)" stopOpacity="0.0" />
                  </linearGradient>
                </defs>
                <path d={equityPath.fill} fill="url(#eqGrad)" />
                <polyline
                  points={equityPath.points}
                  fill="none"
                  stroke="var(--color-gold-500)"
                  strokeWidth="0.6"
                  vectorEffect="non-scaling-stroke"
                  className="drop-shadow-[0_0_6px_rgba(245,158,11,0.5)]"
                />
              </svg>
            ) : (
              <div className="h-full flex flex-col items-center justify-center gap-2">
                <BarChart2 size={28} className="text-[var(--color-surface-700)]" />
                <p className="text-xs text-[var(--color-surface-500)]">Equity data will appear after first trades</p>
              </div>
            )}
          </div>
          {chartData.length >= 2 && (
            <div className="flex justify-between text-[9px] text-[var(--color-surface-500)] font-mono mt-2 pt-2 border-t border-[var(--color-surface-800)]/50">
              <span>{chartData[0]?.date}</span>
              <span>${equityPath.maxV?.toLocaleString()}</span>
              <span>{chartData[chartData.length - 1]?.date}</span>
            </div>
          )}
        </div>

        {/* Daily PnL Bars */}
        <div className="bg-[var(--color-surface-900)]/40 backdrop-blur-xl border border-[var(--color-surface-800)]/60 rounded-2xl p-5 flex flex-col min-h-[350px]">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[var(--color-profit)]" />
            Daily P&L
          </h3>
          {dailyChart.length > 0 ? (
            <div className="flex-1 flex items-end gap-1">
              {dailyChart.slice(-14).map((d, i) => {
                const pct = Math.abs(d.pnl) / maxPnl;
                const positive = d.pnl >= 0;
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1 group cursor-default" title={`${d.date}: $${d.pnl.toFixed(2)}`}>
                    <div className="w-full flex flex-col items-center" style={{ height: '120px' }}>
                      <div
                        className="w-full rounded-t-sm transition-all duration-300 group-hover:opacity-80"
                        style={{
                          height: `${Math.max(pct * 100, 4)}%`,
                          marginTop: 'auto',
                          background: positive ? 'var(--color-profit)' : 'var(--color-loss)',
                          opacity: 0.7,
                        }}
                      />
                    </div>
                    <span className="text-[7px] text-[var(--color-surface-600)] font-mono rotate-45 origin-left truncate">{d.date?.slice(5)}</span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center gap-2">
              <BarChart3 size={28} className="text-[var(--color-surface-700)]" />
              <p className="text-xs text-[var(--color-surface-500)]">No trade data yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Symbol Performance Table */}
      <div className="bg-[var(--color-surface-900)]/40 backdrop-blur-xl border border-[var(--color-surface-800)]/60 rounded-2xl overflow-hidden">
        <div className="px-5 py-3.5 border-b border-[var(--color-surface-800)]/60 bg-[var(--color-surface-900)]/30">
          <h3 className="text-xs font-heading font-bold text-[var(--color-surface-400)] tracking-widest">PERFORMANCE BY SYMBOL</h3>
        </div>
        {(data.symbolPerf || []).length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-surface-800)]/50">
                {['Symbol', 'Total Trades', 'Sells', 'P&L'].map(h => (
                  <th key={h} className="px-5 py-3 text-left text-[10px] uppercase tracking-wider font-medium text-[var(--color-surface-500)]">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-surface-800)]/40">
              {data.symbolPerf.map((row, i) => (
                <tr key={i} className="hover:bg-[var(--color-surface-800)]/20 transition-colors">
                  <td className="px-5 py-3 font-mono font-bold text-white">{row.symbol}</td>
                  <td className="px-5 py-3 font-mono text-[var(--color-surface-300)]">{row.total}</td>
                  <td className="px-5 py-3 font-mono text-[var(--color-surface-300)]">{row.sells}</td>
                  <td className={`px-5 py-3 font-mono font-bold ${row.pnl >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                    {row.pnl >= 0 ? '+' : ''}${row.pnl.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="py-8 flex items-center justify-center text-sm text-[var(--color-surface-500)]">
            No symbol data — start the bot to see per-symbol performance
          </div>
        )}
      </div>
    </div>
  );
};

export default Analytics;

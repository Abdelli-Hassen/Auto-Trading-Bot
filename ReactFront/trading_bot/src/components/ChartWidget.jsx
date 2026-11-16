import React, { useState, useEffect, useRef } from 'react';
import { Maximize2, BarChart2, Activity } from 'lucide-react';
import { createChart, ColorType, CandlestickSeries, HistogramSeries, createSeriesMarkers } from 'lightweight-charts';
import Tooltip from './Tooltip';
import { API_URL } from '../api';

const TIMEFRAMES = ['1m', '5m', '15m', '30m', '1H', '4H', '1D'];
const TF_TO_API  = { '1m':'1m','5m':'5m','15m':'15m','30m':'30m','1H':'1h','4H':'4h','1D':'1d' };
const TF_SECS    = { '1m':60,'5m':300,'15m':900,'30m':1800,'1H':3600,'4H':14400,'1D':86400 };

const TV = {
  bg:      '#131722',
  topbar:  '#1e222d',
  grid:    'rgba(42, 46, 57, 0.6)',
  text:    '#B2B5BE',
  border:  '#2A2E39',
  up:      '#26a69a',
  down:    '#ef5350',
  volUp:   'rgba(38, 166, 154, 0.45)',
  volDown: 'rgba(239, 83, 80, 0.45)',
  cross:   '#758696',
  crossBg: '#2A2E39',
  active:  '#2962FF',
  accent:  '#f59e0b',
};

export default function ChartWidget({ symbol, priceData, signals = [], prediction, positions = [], dataSource }) {
  const [loadState, setLoadState] = useState('loading');
  const linesR = useRef([]);
  const [tf, setTf]   = useState('1m');
  const [ohlc, setOhlc] = useState(null);

  // DOM refs
  const wrapRef   = useRef(null);
  const canvasRef = useRef(null);

  // Library refs (survive re-renders without state)
  const chartR    = useRef(null);
  const candleR   = useRef(null);
  const volR      = useRef(null);
  const markersR  = useRef(null);
  const liveC     = useRef(null);  // current live candle
  const liveV     = useRef(null);  // current live vol bar
  const roRef     = useRef(null);  // ResizeObserver
  const ready     = useRef(false); // chart initialised?

  const chg  = priceData?.change || 0;
  const isUp = chg >= 0;

  // ── 1. Mount: Create chart synchronously ─────────────────────────────────
  //   canvasRef has an explicit pixel height (420px), so it ALWAYS has
  //   real dimensions when this effect fires — no deferred RAF needed.
  useEffect(() => {
    const el = canvasRef.current;
    if (!el || chartR.current) return;  // already created

    const chart = createChart(el, {
      width:  el.clientWidth || 800,
      height: 460,
      layout: {
        background: { type: ColorType.Solid, color: TV.bg },
        textColor:  TV.text,
        fontSize:   11,
        fontFamily: "'JetBrains Mono','Fira Code',monospace",
      },
      grid: {
        vertLines: { color: TV.grid, style: 1 },
        horzLines: { color: TV.grid, style: 1 },
      },
      rightPriceScale: {
        borderColor:  TV.border,
        scaleMargins: { top: 0.08, bottom: 0.22 },
      },
      timeScale: {
        borderColor:    TV.border,
        timeVisible:    true,
        secondsVisible: false,
      },
      crosshair: {
        mode:     1,
        vertLine: { color: TV.cross, width: 1, style: 2, labelBackgroundColor: TV.crossBg },
        horzLine: { color: TV.cross, width: 1, style: 2, labelBackgroundColor: TV.crossBg },
      },
      handleScroll: { vertTouchDrag: false },
    });

    const candles = chart.addSeries(CandlestickSeries, {
      upColor: TV.up, downColor: TV.down,
      borderVisible: false,
      wickUpColor: TV.up, wickDownColor: TV.down,
    });

    const vol = chart.addSeries(HistogramSeries, {
      color: TV.volUp, priceFormat: { type: 'volume' }, priceScaleId: 'vol',
    });
    chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });

    markersR.current = createSeriesMarkers(candles);
    chart.subscribeCrosshairMove(p => {
      if (!p.time) { setOhlc(null); return; }
      const c = p.seriesData?.get(candles);
      if (c) setOhlc({ ...c, isUp: c.close >= c.open });
    });

    chartR.current  = chart;
    candleR.current = candles;
    volR.current    = vol;
    ready.current   = true;

    // ResizeObserver for width-only updates (height is fixed at 420px)
    const ro = new ResizeObserver(() => {
      if (!wrapRef.current || !chartR.current) return;
      const w = wrapRef.current.clientWidth;
      if (w > 0) chartR.current.applyOptions({ width: w });
    });
    if (wrapRef.current) ro.observe(wrapRef.current);
    roRef.current = ro;

    return () => {
      ro.disconnect();
      chart.remove();
      chartR.current = null;
      ready.current  = false;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── 2. Fetch real OHLCV from API (runs after chart is ready) ─────────────
  useEffect(() => {
    if (!ready.current) return;
    liveC.current = null;
    liveV.current = null;

    let cancelled = false;

    setLoadState('loading');
    const loadFromAPI = async () => {
      const ctrl    = new AbortController();
      const timeout = setTimeout(() => ctrl.abort(), 4000);
      try {
        const res  = await fetch(
          `${API_URL}/api/test/ohlcv?symbol=${encodeURIComponent(symbol)}&timeframe=${TF_TO_API[tf]||'1m'}&limit=300`,
          { signal: ctrl.signal }
        );
        clearTimeout(timeout);
        if (cancelled) return;
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0 && candleR.current) {
          candleR.current.setData(data);
          volR.current.setData(data.map(d => ({
            time: d.time, value: d.volume || 0,
            color: d.close >= d.open ? TV.volUp : TV.volDown,
          })));
          chartR.current.timeScale().fitContent();
          setLoadState('ok');
        } else if (!cancelled) {
          setLoadState('error');
        }
      } catch {
        clearTimeout(timeout);
        if (!cancelled) setLoadState('error');
      }
    };

    loadFromAPI();

    return () => { cancelled = true; };
  }, [symbol, tf]);

  // ── Entry-price lines for open positions in this symbol ──────────────────
  useEffect(() => {
    const series = candleR.current;
    if (!series) return;
    linesR.current.forEach(l => { try { series.removePriceLine(l); } catch { /* ignore */ } });
    linesR.current = [];
    positions.filter(p => p.symbol === symbol).forEach(p => {
      linesR.current.push(series.createPriceLine({
        price: p.entry_price, color: p.side === 'long' ? TV.up : TV.down, lineWidth: 1, lineStyle: 2,
        axisLabelVisible: true, title: `${p.side.toUpperCase()} entry`,
      }));
    });
  }, [positions, symbol]);

  // ── 3. Live tick ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!ready.current || !candleR.current || !priceData?.price || !priceData?.timestamp) return;
    try {
      const ts     = Math.floor(new Date(priceData.timestamp).getTime() / 1000);
      if (isNaN(ts)) return;
      const bucket = ts - (ts % (TF_SECS[tf] || 60));
      const price  = priceData.price;

      if (!liveC.current || liveC.current.time !== bucket) {
        liveC.current = { time: bucket, open: price, high: price, low: price, close: price };
        liveV.current = { time: bucket, value: 0, color: TV.volUp };
      } else {
        liveC.current.high  = Math.max(liveC.current.high, price);
        liveC.current.low   = Math.min(liveC.current.low,  price);
        liveC.current.close = price;
        liveV.current.color = price >= liveC.current.open ? TV.volUp : TV.volDown;
      }

      candleR.current.update(liveC.current);
      volR.current.update(liveV.current);
    } catch { /* ignore */ }
  }, [priceData, tf]);

  // ── 4. Markers ────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!markersR.current) return;
    markersR.current.setMarkers(
      (signals || []).filter(s => s.timestamp && (!s.symbol || s.symbol === symbol))
        .sort((a, b) => a.timestamp - b.timestamp).map(s => ({
        time:     s.timestamp,
        position: s.direction === 'long' ? 'belowBar' : 'aboveBar',
        color:    s.direction === 'long' ? TV.up : TV.down,
        shape:    s.direction === 'long' ? 'arrowUp' : 'arrowDown',
        text:     (s.direction === 'long' ? 'BUY ' : 'SELL ') + (s.rule || ''),
        size: 1,
      }))
    );
  }, [signals, symbol]);

  // ── Fullscreen ─────────────────────────────────────────────────────────────
  const toggleFS = () => {
    if (!document.fullscreenElement) wrapRef.current?.requestFullscreen();
    else document.exitFullscreen();
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div
      ref={wrapRef}
      className="w-full rounded-2xl overflow-hidden border"
      style={{ background: TV.bg, borderColor: TV.border }}
    >
      {/* ── Top Bar ── */}
      <div
        className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2 px-3 sm:px-4 py-2.5"
        style={{ background: TV.topbar, borderBottom: `1px solid ${TV.border}` }}
      >
        {/* Left */}
        <div className="flex items-center gap-3 sm:gap-5 flex-wrap min-w-0">
          {/* Symbol */}
          <Tooltip content="The current trading pair being analyzed and traded by the bot.">
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: TV.accent }} />
              <span className="text-white font-bold text-sm sm:text-base tracking-tight">{symbol}</span>
              <span className="text-[9px] font-mono uppercase tracking-wider hidden sm:inline" style={{ color: TV.text }}>{dataSource === 'synthetic' ? 'SIMULATED' : 'BINANCE'}</span>
            </div>
          </Tooltip>

          {/* Price */}
          <Tooltip content="Real-time price feed from the exchange. Green means the price went up in the current candle, red means down.">
            <div className="flex flex-col leading-none shrink-0">
              <span className="text-lg sm:text-2xl font-mono font-bold tabular-nums" style={{ color: isUp ? TV.up : TV.down }}>
                {(priceData?.price || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className="text-[10px] font-mono font-semibold mt-0.5" style={{ color: isUp ? TV.up : TV.down }}>
                {isUp ? '▲' : '▼'} {Math.abs(chg).toFixed(2)}%
              </span>
            </div>
          </Tooltip>

          {/* OHLC tooltip on hover */}
          {ohlc ? (
            <div className="hidden sm:flex items-center gap-3 text-[10px] font-mono">
              {[['O', ohlc.open], ['H', ohlc.high], ['L', ohlc.low], ['C', ohlc.close]].map(([label, val]) => (
                <span key={label} style={{ color: TV.text }}>
                  {label} <span style={{ color: label === 'H' ? TV.up : label === 'L' ? TV.down : ohlc.isUp ? TV.up : TV.down }}>{Number(val).toFixed(2)}</span>
                </span>
              ))}
            </div>
          ) : (
            <span className="hidden md:inline text-[10px] font-mono opacity-40" style={{ color: TV.text }}>Hover to inspect</span>
          )}

          {/* AI prediction badge */}
          {prediction && (
            <Tooltip content="The AI's current sentiment and action recommendation based on its internal strategy rules. More bars = higher confidence.">
              <div
                className="hidden lg:flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-mono font-bold uppercase"
                style={{ background: 'rgba(42,46,57,0.9)', border: `1px solid ${TV.border}`, color: prediction.sentiment === 'BULLISH' ? TV.up : prediction.sentiment === 'BEARISH' ? TV.down : TV.accent }}
              >
                <Activity size={10} />
                BOT: {prediction.action || 'ANALYZING'}
                <div className="flex gap-0.5 ml-1">
                  {[1,2,3,4,5].map(i => (
                    <div key={i} style={{ width: 3, height: 10, borderRadius: 2, background: i <= Math.round((prediction.confidence || 0.5) * 5) ? (prediction.sentiment === 'BULLISH' ? TV.up : prediction.sentiment === 'BEARISH' ? TV.down : TV.accent) : TV.border }} />
                  ))}
                </div>
              </div>
            </Tooltip>
          )}
        </div>

        {/* Right */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="flex rounded overflow-hidden" style={{ border: `1px solid ${TV.border}` }}>
            {TIMEFRAMES.map(t => (
              <button
                key={t}
                onClick={() => setTf(t)}
                className="px-2 sm:px-2.5 py-1 text-[10px] sm:text-[11px] font-mono font-bold cursor-pointer"
                style={{
                  background:  tf === t ? TV.active : 'transparent',
                  color:       tf === t ? '#fff' : TV.text,
                  borderRight: `1px solid ${TV.border}`,
                }}
              >{t}</button>
            ))}
          </div>
          <button onClick={toggleFS} className="p-1.5 rounded cursor-pointer" style={{ color: TV.text }}>
            <Maximize2 size={14} />
          </button>
        </div>
      </div>

      {/* ── Chart Canvas (explicit 770px height — never zero) ── */}
      <div className="relative">
        <div ref={canvasRef} style={{ width: '100%', height: 460 }} />
        {loadState !== 'ok' && (
          <div className="absolute inset-0 flex items-center justify-center text-xs font-mono" style={{ background: 'rgba(19,23,34,0.85)', color: TV.text }}>
            {loadState === 'loading' ? `Loading ${symbol} candles…` : 'No market data available — is the backend running?'}
          </div>
        )}
      </div>
    </div>
  );
}

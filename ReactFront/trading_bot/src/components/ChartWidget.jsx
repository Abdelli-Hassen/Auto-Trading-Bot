import React, { useState, useEffect, useRef } from 'react';
import { Maximize2, Settings2, BarChart2 } from 'lucide-react';
import { createChart, ColorType, CandlestickSeries } from 'lightweight-charts';

export default function ChartWidget({ symbol, priceData }) {
  const [timeframe, setTimeframe] = useState('1m');
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const currentCandleRef = useRef(null);

  const tfs = ['1m', '5m', '15m', '1H', '4H', '1D'];

  const chg = priceData?.change || 0;
  const isUp = chg >= 0;

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 0,
      }
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#f43f5e',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#f43f5e',
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current.clientWidth, height: chartContainerRef.current.clientHeight });
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  const historyGeneratedRef = useRef(false);

  // Update chart when price changes
  useEffect(() => {
    if (seriesRef.current && priceData?.price && priceData?.timestamp) {
      // In a real app we'd receive complete OHLCV from WS.
      // Since we only get 'last price', we simulate a live updating candle
      // by updating the close price of the current timeframe candle.
      
      try {
        const timestamp = Math.floor(new Date(priceData.timestamp).getTime() / 1000);
        // Normalize time to 1m boundary for simulation
        const currentMinute = timestamp - (timestamp % 60);
        const price = priceData.price;
        
        if (!historyGeneratedRef.current) {
            const history = [];
            let lastClose = price;
            for (let i = 100; i >= 1; i--) {
                const time = currentMinute - (i * 60);
                const open = lastClose;
                const close = open * (1 + (Math.random() - 0.5) * 0.002);
                const high = Math.max(open, close) * (1 + Math.random() * 0.001);
                const low = Math.min(open, close) * (1 - Math.random() * 0.001);
                history.push({ time, open, high, low, close });
                lastClose = close;
            }
            seriesRef.current.setData(history);
            chartRef.current.timeScale().fitContent();
            historyGeneratedRef.current = true;
        }

        if (!currentCandleRef.current || currentCandleRef.current.time !== currentMinute) {
          // Start a new candle for the new minute
          currentCandleRef.current = {
            time: currentMinute,
            open: price,
            high: price,
            low: price,
            close: price
          };
        } else {
          // Update the current minute's candle OHLC
          currentCandleRef.current.high = Math.max(currentCandleRef.current.high, price);
          currentCandleRef.current.low = Math.min(currentCandleRef.current.low, price);
          currentCandleRef.current.close = price;
        }
        
        seriesRef.current.update(currentCandleRef.current);
      } catch(e) {}
    }
  }, [priceData]);

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-[var(--color-surface-900)] to-[var(--color-surface-950)] relative">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between px-4 lg:px-6 py-3 lg:py-4 border-b border-[var(--color-surface-800)]/60 bg-[var(--color-surface-900)]/40 gap-4 z-10 relative">
        {/* Symbol & Price Info */}
        <div className="flex items-center gap-4 lg:gap-8">
          <div>
            <h2 className="text-xl lg:text-2xl font-heading font-bold text-white tracking-wide flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--color-gold-500)] animate-pulse" />
              {symbol}
            </h2>
            <div className="flex items-center gap-3 mt-1 text-[10px] lg:text-xs font-mono">
              <span className="text-[var(--color-surface-400)] tracking-wider">BINANCE</span>
              <span className="w-1 h-1 rounded-full bg-[var(--color-surface-600)]" />
              <span className="text-[var(--color-surface-400)] tracking-wider">SPOT</span>
            </div>
          </div>
          
          <div className="h-8 w-px bg-[var(--color-surface-800)] hidden sm:block" />
          
          <div className="flex flex-col">
            <span className={`text-xl lg:text-3xl font-mono font-bold tracking-tight leading-none ${isUp ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'} transition-colors duration-300`}>
              ${(priceData?.price || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className={`text-[10px] lg:text-xs font-mono font-bold mt-1 ${isUp ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
              {isUp ? '+' : ''}{chg.toFixed(2)}% (24h)
            </span>
          </div>

          <div className="h-8 w-px bg-[var(--color-surface-800)] hidden md:block" />

          <div className="hidden md:flex flex-col">
            <span className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)] mb-1 font-medium">24h Vol</span>
            <span className="text-xs font-mono text-white">{(priceData?.volume || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
          </div>
        </div>

        {/* Tools & Timeframe */}
        <div className="flex items-center gap-2 lg:gap-4 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0 hide-scrollbar">
          <div className="flex bg-[var(--color-surface-900)] border border-[var(--color-surface-800)] rounded-lg p-1 shrink-0">
            {tfs.map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-2.5 lg:px-4 py-1.5 rounded-md text-[10px] lg:text-xs font-bold font-mono tracking-wider transition-all duration-200 cursor-pointer ${
                  timeframe === tf
                    ? 'bg-[var(--color-gold-600)] text-black shadow-sm'
                    : 'text-[var(--color-surface-400)] hover:text-white hover:bg-[var(--color-surface-800)]/50'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1 shrink-0 ml-auto sm:ml-0">
            <button className="p-2 rounded-lg text-[var(--color-surface-400)] hover:text-white hover:bg-[var(--color-surface-800)] transition-colors cursor-pointer">
              <Settings2 size={16} />
            </button>
            <button className="p-2 rounded-lg text-[var(--color-surface-400)] hover:text-white hover:bg-[var(--color-surface-800)] transition-colors cursor-pointer">
              <Maximize2 size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Chart Area */}
      <div className="flex-1 relative w-full h-full" ref={chartContainerRef}>
        {!priceData?.price && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-8 z-20 bg-[var(--color-surface-950)]/80 backdrop-blur-sm">
             <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--color-surface-800)] to-[var(--color-surface-900)] border border-[var(--color-surface-700)] flex items-center justify-center mb-6 animate-pulse">
               <BarChart2 size={32} className="text-[var(--color-gold-500)]" />
             </div>
             <h3 className="text-xl font-heading font-bold text-white mb-2">Connecting to Data Feed</h3>
             <p className="text-sm text-[var(--color-surface-400)]">Waiting for real-time WebSocket tick data...</p>
          </div>
        )}
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import ChartWidget from './components/ChartWidget';
import OrderBook from './components/OrderBook';
import ControlPanel from './components/ControlPanel';
import Analytics from './components/Analytics';
import Strategies from './components/Strategies';
import History from './components/History';
import Profile from './components/Profile';
import SettingsModal from './components/SettingsModal';
import NotificationsDropdown from './components/NotificationsDropdown';
import { useWebSocket } from './hooks/useWebSocket';
import { Hexagon, LayoutGrid, Settings, Bell, Search } from 'lucide-react';

const API_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/stream';

function App() {
  const { data, isConnected } = useWebSocket(WS_URL);
  const [error, setError] = useState(null);
  
  // Navigation State
  const [activeTab, setActiveTab] = useState('Trading');
  const [showSettings, setShowSettings] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  // Global Trading State
  const [symbol, setSymbol] = useState('BTC/USDT');

  const handleStart = async () => {
    try {
      const res = await fetch(`${API_URL}/api/bot/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'live' })
      });
      const result = await res.json();
      if (result.status === 'error') setError(result.message);
      else setError(null);
    } catch (err) {
      setError('Failed to contact API server');
    }
  };

  const handleStop = async () => {
    try {
      const res = await fetch(`${API_URL}/api/bot/stop`, { method: 'POST' });
      const result = await res.json();
      if (result.status === 'error') setError(result.message);
    } catch (err) {
      setError('Failed to contact API server');
    }
  };

  const handleLiquidate = async () => {
    if (window.confirm("Are you sure you want to liquidate all positions immediately?")) {
      try {
        const res = await fetch(`${API_URL}/api/bot/liquidate`, { method: 'POST' });
        const result = await res.json();
        if (result.status === 'error') setError(result.message);
        else { setError(null); alert(result.message); }
      } catch (err) {
        setError('Failed to contact API server');
      }
    }
  };

  // Main Trading Workspace Content
  const renderTradingWorkspace = () => (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-5">
      {/* Chart — full width on mobile, 9/12 on desktop */}
      <div className="lg:col-span-8 xl:col-span-9">
        <ChartWidget
          symbol={symbol}
          priceData={{
            timestamp: data?.timestamp,
            price: data?.prices?.[symbol]?.last || 0,
            change: data?.prices?.[symbol]?.change || 0,
            volume: data?.prices?.[symbol]?.volume || 0,
          }}
          signals={data?.status?.recent_signals}
          prediction={data?.status?.prediction}
        />
      </div>

      {/* Sidebar — stacks below chart on mobile, right column on desktop */}
      <div className="lg:col-span-4 xl:col-span-3 flex flex-col gap-4">
        <ControlPanel
          status={data?.status}
          isConnected={isConnected}
          onStart={handleStart}
          onStop={handleStop}
          onLiquidate={handleLiquidate}
          symbol={symbol}
          onSymbolChange={setSymbol}
        />
        <OrderBook status={data?.status} prices={data?.prices} />
      </div>
    </div>
  );

  return (
    <div className="min-h-screen w-full bg-[var(--color-surface-950)] text-[var(--color-surface-300)] flex flex-col font-sans relative">
      {/* Ambient Glow */}
      <div className="fixed top-0 left-[-10%] lg:left-[20%] w-[400px] lg:w-[600px] h-[400px] lg:h-[600px] bg-[var(--color-gold-600)]/5 rounded-full blur-[100px] lg:blur-[120px] pointer-events-none" />
      <div className="fixed bottom-0 right-[-10%] lg:right-[10%] w-[300px] lg:w-[500px] h-[300px] lg:h-[500px] bg-[var(--color-profit)]/5 rounded-full blur-[80px] lg:blur-[100px] pointer-events-none" />

      {/* Modern Top Navigation */}
      <header className="relative z-20 h-auto lg:h-16 px-4 lg:px-6 py-4 lg:py-0 flex flex-col lg:flex-row justify-between items-center bg-[var(--color-surface-900)]/80 backdrop-blur-xl border-b border-[var(--color-surface-800)]/80 gap-4 lg:gap-0">
        <div className="flex w-full lg:w-auto justify-between lg:justify-start items-center gap-8">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--color-gold-400)] to-[var(--color-gold-600)] flex items-center justify-center shadow-lg shadow-[var(--color-gold-500)]/20">
              <Hexagon size={18} className="text-black" fill="currentColor" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-lg font-heading font-bold text-white leading-none tracking-wide">
                NEXTRADE<span className="text-[var(--color-gold-500)]">AI</span>
              </h1>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {['Trading', 'Analytics', 'Strategies', 'History', 'Profile'].map((item) => (
              <button 
                key={item} 
                onClick={() => setActiveTab(item)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === item 
                    ? 'bg-[var(--color-surface-800)] text-white shadow-inner shadow-white/5' 
                    : 'text-[var(--color-surface-400)] hover:text-white hover:bg-[var(--color-surface-800)]/50'
                }`}
              >
                {item}
              </button>
            ))}
          </nav>
        </div>

        {/* Right Tools */}
        <div className="flex items-center justify-between w-full lg:w-auto gap-4 relative">
          <div className="hidden xl:flex relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-surface-500)]" />
            <input type="text" placeholder="Search markets..." className="bg-[var(--color-surface-950)] border border-[var(--color-surface-800)] rounded-lg pl-9 pr-4 py-1.5 text-sm focus:outline-none focus:border-[var(--color-gold-500)]/50 transition-colors w-48 text-[var(--color-surface-300)]" />
          </div>
          <div className="hidden md:flex items-center gap-2">
            <button 
              onClick={() => setShowNotifications(!showNotifications)}
              className={`relative w-9 h-9 flex items-center justify-center rounded-lg transition-colors ${showNotifications ? 'bg-[var(--color-surface-800)] text-white' : 'text-[var(--color-surface-400)] hover:text-white hover:bg-[var(--color-surface-800)]'}`}
            >
              <Bell size={18} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-[var(--color-gold-500)] rounded-full border-2 border-[var(--color-surface-900)]"></span>
            </button>
            <NotificationsDropdown isOpen={showNotifications} onClose={() => setShowNotifications(false)} />
            
            <button 
              onClick={() => setShowSettings(true)}
              className="w-9 h-9 flex items-center justify-center rounded-lg text-[var(--color-surface-400)] hover:text-white hover:bg-[var(--color-surface-800)] transition-colors"
            >
              <Settings size={18} />
            </button>
          </div>
          <div className="hidden lg:block w-px h-6 bg-[var(--color-surface-800)] mx-2" />
          <div className="flex w-full lg:w-auto justify-center lg:justify-start items-center gap-2 bg-[var(--color-surface-850)] px-3 py-1.5 rounded-lg border border-[var(--color-surface-800)]">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[var(--color-profit)] animate-pulse-soft' : 'bg-[var(--color-loss)]'}`} />
            <span className="text-[11px] font-bold tracking-widest uppercase text-[var(--color-surface-300)]">
              {isConnected ? 'Connected' : 'Offline'}
            </span>
          </div>
        </div>
      </header>

      {error && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-50 bg-[var(--color-loss-dim)] border border-[var(--color-loss)]/30 text-[var(--color-loss)] px-6 py-3 rounded-xl text-sm font-medium shadow-xl shadow-[var(--color-loss)]/10 animate-fade-in-up flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-[var(--color-loss)]" />
          {error}
          <button onClick={() => setError(null)} className="ml-4 opacity-70 hover:opacity-100">×</button>
        </div>
      )}

      {/* Main Dynamic Workspace */}
      <main className="relative z-10 flex-1 w-full px-4 lg:px-6 py-4 pb-6">
        <div className="max-w-[1920px] mx-auto w-full">
          {activeTab === 'Trading'    && renderTradingWorkspace()}
          {activeTab === 'Analytics'  && <Analytics />}
          {activeTab === 'Strategies' && <Strategies />}
          {activeTab === 'History'    && <History />}
          {activeTab === 'Profile'    && <Profile data={data} />}
        </div>
      </main>

      {/* Bottom Status Bar */}
      <footer className="relative z-10 px-4 lg:px-8 py-3 lg:py-2 border-t border-[var(--color-surface-800)]/60 bg-[var(--color-surface-900)]/80 flex flex-col sm:flex-row justify-between items-center text-[11px] text-[var(--color-surface-500)] tracking-wide gap-2 sm:gap-0 mt-auto">
        <span className="font-mono text-center sm:text-left">NexTrade AI v2.0-pro-max</span>
        <div className="flex flex-wrap justify-center sm:justify-end gap-4 lg:gap-6">
          <span>Latency: <span className="text-[var(--color-profit)] font-mono">{isConnected ? '12ms' : '—'}</span></span>
          <span className="hidden sm:inline">Endpoint: <span className="font-mono text-[var(--color-surface-400)]">{isConnected ? 'ws://localhost:8000/ws/stream' : 'offline'}</span></span>
        </div>
      </footer>

      {/* Settings Modal */}
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  );
}

export default App;

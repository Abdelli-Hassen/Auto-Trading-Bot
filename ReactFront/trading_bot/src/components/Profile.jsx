import React from 'react';
import { 
  User, Wallet, Shield, TrendingUp, History, 
  Settings as SettingsIcon, LogOut, CheckCircle, 
  Globe, Zap, CreditCard, Award
} from 'lucide-react';

const Profile = ({ data }) => {
  const status = data?.status || {};
  const risk = status?.risk_metrics || {};
  const stats = status?.daily_stats || {};
  const balance = data?.prices?.['USDT']?.last || 0; // Fallback or mock balance if needed

  const accountStats = [
    { label: 'Total Balance', value: `$${(10000 + (risk.total_pnl || 0)).toLocaleString()}`, icon: Wallet, color: 'text-[var(--color-gold-500)]' },
    { label: 'Total PnL', value: `${(risk.total_pnl || 0) >= 0 ? '+' : ''}${(risk.total_pnl || 0).toFixed(2)}`, icon: TrendingUp, color: (risk.total_pnl || 0) >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]' },
    { label: 'Win Rate', value: `${((stats.win_rate || 0) * 100).toFixed(1)}%`, icon: Award, color: 'text-blue-400' },
    { label: 'Daily Trades', value: stats.trades || 0, icon: Zap, color: 'text-purple-400' },
  ];

  const sections = [
    {
      title: 'Security & Access',
      icon: Shield,
      items: [
        { label: 'API Keys', status: 'Connected', detail: 'Binance (Trading Only)', action: 'Manage' },
        { label: 'Two-Factor Auth', status: 'Enabled', detail: 'Google Authenticator', action: 'Setup' },
        { label: 'Active Sessions', status: '1 Active', detail: 'Last login: 2 mins ago', action: 'View' },
      ]
    },
    {
      title: 'Preferences',
      icon: SettingsIcon,
      items: [
        { label: 'Trading Mode', status: 'Paper', detail: 'Mock execution active', action: 'Switch' },
        { label: 'Risk Profile', status: 'Moderate', detail: '1% per trade limit', action: 'Change' },
        { label: 'Language', status: 'English', detail: 'System-wide', action: 'Select' },
      ]
    }
  ];

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Profile Header Card */}
      <div className="relative overflow-hidden bg-[var(--color-surface-900)]/60 backdrop-blur-xl border border-[var(--color-surface-800)]/60 rounded-3xl p-8">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-[var(--color-gold-500)]/10 to-transparent rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        
        <div className="flex flex-col md:flex-row items-center gap-8 relative z-10">
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-[var(--color-surface-800)] to-[var(--color-surface-700)] p-1 border border-[var(--color-surface-600)]/50 shadow-2xl">
              <div className="w-full h-full rounded-full bg-[var(--color-surface-950)] flex items-center justify-center">
                <User size={48} className="text-[var(--color-surface-500)]" />
              </div>
            </div>
            <div className="absolute bottom-1 right-1 w-6 h-6 bg-[var(--color-profit)] rounded-full border-4 border-[var(--color-surface-900)] flex items-center justify-center">
              <CheckCircle size={10} className="text-white" fill="currentColor" />
            </div>
          </div>

          <div className="flex-1 text-center md:text-left">
            <h2 className="text-3xl font-heading font-bold text-white mb-2">Alex NexTrade</h2>
            <p className="text-sm text-[var(--color-surface-400)] font-mono flex items-center justify-center md:justify-start gap-2">
              <Globe size={14} />
              Pro Account • ID: 4859-NX-2025
            </p>
            <div className="flex flex-wrap justify-center md:justify-start gap-4 mt-6">
              <button className="px-5 py-2 rounded-xl bg-[var(--color-gold-600)] text-black font-bold text-xs hover:bg-[var(--color-gold-500)] transition-all shadow-lg shadow-[var(--color-gold-500)]/20 cursor-pointer">
                Upgrade to Enterprise
              </button>
              <button className="px-5 py-2 rounded-xl bg-[var(--color-surface-800)] text-white font-bold text-xs hover:bg-[var(--color-surface-700)] transition-all border border-[var(--color-surface-700)] cursor-pointer">
                View Public Profile
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {accountStats.map((stat, i) => (
          <div key={i} className="bg-[var(--color-surface-900)]/40 backdrop-blur-md border border-[var(--color-surface-800)]/60 rounded-2xl p-5 group hover:border-[var(--color-gold-500)]/30 transition-all cursor-default">
            <div className="flex justify-between items-start mb-3">
              <div className="p-2 rounded-lg bg-[var(--color-surface-800)] border border-[var(--color-surface-700)]/50">
                <stat.icon size={16} className={stat.color} />
              </div>
              <TrendingUp size={14} className="text-[var(--color-profit)] opacity-40" />
            </div>
            <p className="text-[10px] uppercase tracking-wider text-[var(--color-surface-500)] font-medium mb-1">{stat.label}</p>
            <p className="text-xl font-bold text-white font-mono">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Main Sections Area */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 pb-6">
        {sections.map((section, i) => (
          <div key={i} className="bg-[var(--color-surface-900)]/40 backdrop-blur-md border border-[var(--color-surface-800)]/60 rounded-3xl overflow-hidden">
            <div className="px-6 py-4 border-b border-[var(--color-surface-800)]/60 bg-[var(--color-surface-900)]/30 flex items-center gap-3">
              <section.icon size={18} className="text-[var(--color-gold-500)]" />
              <h3 className="text-sm font-heading font-bold text-white tracking-widest">{section.title.toUpperCase()}</h3>
            </div>
            <div className="p-2">
              {section.items.map((item, j) => (
                <div key={j} className="flex items-center justify-between p-4 rounded-2xl hover:bg-[var(--color-surface-800)]/30 transition-all group">
                  <div className="flex flex-col gap-1">
                    <p className="text-sm font-bold text-white">{item.label}</p>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${item.status === 'Enabled' || item.status === 'Connected' ? 'bg-[var(--color-profit)]/10 text-[var(--color-profit)]' : 'bg-[var(--color-gold-500)]/10 text-[var(--color-gold-500)]'}`}>
                        {item.status}
                      </span>
                      <span className="text-xs text-[var(--color-surface-500)]">• {item.detail}</span>
                    </div>
                  </div>
                  <button className="px-4 py-1.5 rounded-lg border border-[var(--color-surface-700)] text-[10px] font-bold uppercase tracking-wider text-[var(--color-surface-400)] group-hover:text-white group-hover:border-[var(--color-gold-500)]/50 transition-all cursor-pointer">
                    {item.action}
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Danger Zone */}
        <div className="bg-red-500/5 backdrop-blur-md border border-red-500/20 rounded-3xl overflow-hidden xl:col-span-2">
          <div className="px-6 py-4 border-b border-red-500/10 bg-red-500/10 flex items-center gap-3">
            <LogOut size={18} className="text-red-500" />
            <h3 className="text-sm font-heading font-bold text-red-500 tracking-widest">DANGER ZONE</h3>
          </div>
          <div className="p-6 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="text-center md:text-left">
              <p className="text-sm font-bold text-white mb-1">Delete Account</p>
              <p className="text-xs text-[var(--color-surface-500)]">Permanently remove all data, trade history, and active bots.</p>
            </div>
            <button className="px-6 py-3 rounded-xl bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white border border-red-500/30 transition-all font-bold text-xs tracking-widest cursor-pointer">
              DELETE EVERYTHING
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;

import React, { useState } from 'react';
import { X, Save, Key, ShieldAlert, Sliders } from 'lucide-react';

const SettingsModal = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState('API Keys');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-[var(--color-surface-900)] border border-[var(--color-surface-800)] rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[var(--color-surface-800)] flex justify-between items-center bg-[var(--color-surface-850)]">
          <h2 className="text-xl font-heading font-bold text-white">Settings</h2>
          <button onClick={onClose} className="text-[var(--color-surface-500)] hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-48 border-r border-[var(--color-surface-800)] bg-[var(--color-surface-900)]/50 p-4 flex flex-col gap-2">
            {[
              { id: 'API Keys', icon: Key },
              { id: 'Risk Limits', icon: ShieldAlert },
              { id: 'Preferences', icon: Sliders },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab.id 
                      ? 'bg-[var(--color-surface-800)] text-white' 
                      : 'text-[var(--color-surface-400)] hover:bg-[var(--color-surface-800)]/50 hover:text-white'
                  }`}
                >
                  <Icon size={16} />
                  {tab.id}
                </button>
              );
            })}
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {activeTab === 'API Keys' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Exchange API Integration</h3>
                  <p className="text-sm text-[var(--color-surface-400)] mb-4">
                    Enter your API keys to allow the bot to execute trades on your behalf. Ensure IP whitelisting is enabled on your exchange.
                  </p>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-medium text-[var(--color-surface-400)] mb-1">Exchange</label>
                      <select className="w-full bg-[var(--color-surface-950)] border border-[var(--color-surface-800)] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--color-gold-500)]">
                        <option>Binance</option>
                        <option>Bybit</option>
                        <option>Kraken</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-[var(--color-surface-400)] mb-1">API Key</label>
                      <input type="password" defaultValue="************************" className="w-full bg-[var(--color-surface-950)] border border-[var(--color-surface-800)] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--color-gold-500)]" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-[var(--color-surface-400)] mb-1">API Secret</label>
                      <input type="password" defaultValue="************************" className="w-full bg-[var(--color-surface-950)] border border-[var(--color-surface-800)] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--color-gold-500)]" />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'Risk Limits' && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-white mb-4">Global Risk Parameters</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-[var(--color-surface-400)] mb-1">Max Daily Drawdown (%)</label>
                    <input type="number" defaultValue="5" className="w-full bg-[var(--color-surface-950)] border border-[var(--color-surface-800)] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--color-gold-500)]" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-[var(--color-surface-400)] mb-1">Max Position Size (USDT)</label>
                    <input type="number" defaultValue="1000" className="w-full bg-[var(--color-surface-950)] border border-[var(--color-surface-800)] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--color-gold-500)]" />
                  </div>
                  <div className="pt-4 border-t border-[var(--color-surface-800)]">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-[var(--color-surface-700)] bg-[var(--color-surface-900)] text-[var(--color-gold-500)] focus:ring-[var(--color-gold-500)] focus:ring-offset-[var(--color-surface-900)]" />
                      <span className="text-sm text-white">Halt trading on severe API errors</span>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'Preferences' && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-white mb-4">UI Preferences</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-[var(--color-surface-400)] mb-1">Theme</label>
                    <select className="w-full bg-[var(--color-surface-950)] border border-[var(--color-surface-800)] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[var(--color-gold-500)]">
                      <option>Midnight Gold (Default)</option>
                      <option>Dark Void</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[var(--color-surface-800)] bg-[var(--color-surface-850)] flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-medium text-[var(--color-surface-300)] hover:text-white hover:bg-[var(--color-surface-800)] transition-colors">
            Cancel
          </button>
          <button onClick={onClose} className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold bg-[var(--color-gold-600)] hover:bg-[var(--color-gold-500)] text-black transition-colors">
            <Save size={16} />
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;

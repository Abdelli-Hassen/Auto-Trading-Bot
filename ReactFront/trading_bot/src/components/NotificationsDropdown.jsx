import React, { useState, useEffect } from 'react';
import { Bell, AlertTriangle, CheckCircle, Info, XCircle, Loader } from 'lucide-react';
import { API_URL } from '../api';

const ICON_MAP = {
  success: CheckCircle,
  warning: AlertTriangle,
  info: Info,
  error: XCircle,
};

const COLOR_MAP = {
  success: 'text-[var(--color-profit)]',
  warning: 'text-[var(--color-gold-500)]',
  info: 'text-[var(--color-surface-400)]',
  error: 'text-[var(--color-loss)]',
};

const NotificationsDropdown = ({ isOpen, onClose, lastSeenId = 0, onMarkAllRead }) => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    fetch(`${API_URL}/api/test/notifications`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch');
        return res.json();
      })
      .then(data => {
        setNotifications(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-40" onClick={onClose} />
      <div className="absolute top-16 right-4 w-80 bg-[var(--color-surface-900)] border border-[var(--color-surface-800)] rounded-xl shadow-2xl z-50 overflow-hidden animate-fade-in-up">
        <div className="px-4 py-3 border-b border-[var(--color-surface-800)] flex justify-between items-center bg-[var(--color-surface-850)]">
          <h3 className="font-bold text-white flex items-center gap-2">
            <Bell size={16} className="text-[var(--color-gold-500)]" />
            Notifications
          </h3>
          {notifications.filter(n => n.id > lastSeenId).length > 0 && (
            <span className="text-xs bg-[var(--color-gold-600)] text-black px-2 py-0.5 rounded-full font-bold">
              {notifications.filter(n => n.id > lastSeenId).length} New
            </span>
          )}
        </div>

        <div className="max-h-80 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-10">
              <Loader className="animate-spin text-[var(--color-gold-500)]" size={20} />
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex items-center justify-center py-10 text-xs text-[var(--color-surface-500)]">
              No notifications
            </div>
          ) : (
            notifications.map((notif) => {
              const Icon = ICON_MAP[notif.type] ?? Info;
              return (
                <div key={notif.id} className={`px-4 py-3 border-b border-[var(--color-surface-800)]/50 hover:bg-[var(--color-surface-800)]/30 transition-colors flex gap-3 ${notif.id > lastSeenId ? 'bg-[var(--color-gold-500)]/5' : ''}`}>
                  <div className={`mt-0.5 ${COLOR_MAP[notif.type] ?? COLOR_MAP.info}`}>
                    <Icon size={16} />
                  </div>
                  <div>
                    <div className="flex justify-between items-start gap-4 mb-1">
                      <h4 className="text-sm font-medium text-white">{notif.title}</h4>
                      <span className="text-[10px] text-[var(--color-surface-500)] whitespace-nowrap">{notif.time}</span>
                    </div>
                    <p className="text-xs text-[var(--color-surface-400)]">{notif.message}</p>
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="p-2 bg-[var(--color-surface-850)] text-center border-t border-[var(--color-surface-800)]">
          <button onClick={onMarkAllRead} className="text-xs text-[var(--color-surface-400)] hover:text-white transition-colors cursor-pointer">
            Mark all as read
          </button>
        </div>
      </div>
    </>
  );
};

export default NotificationsDropdown;

import React, { useState, useRef, useEffect } from 'react';

export default function Tooltip({ children, content, delay = 2500, position = 'top', wrapperClass = 'relative inline-block' }) {
  const [isVisible, setIsVisible] = useState(false);
  const timeoutRef = useRef(null);

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setIsVisible(false);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const positions = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <div 
      className={wrapperClass}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {isVisible && (
        <div 
          className={`absolute z-50 px-3 py-2 text-[10px] sm:text-xs font-mono text-[var(--color-surface-200)] bg-[var(--color-surface-900)]/90 border border-[var(--color-gold-500)]/40 rounded-lg shadow-[0_4px_20px_rgba(0,0,0,0.5)] backdrop-blur-md w-max max-w-[280px] whitespace-normal transition-opacity duration-300 animate-fade-in ${positions[position]}`}
          style={{ pointerEvents: 'none', lineHeight: '1.4' }}
        >
          <div className="flex items-center gap-1.5 mb-1">
            <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-gold-500)] animate-pulse" />
            <span className="text-[9px] font-bold text-white tracking-wider uppercase">AI HINT</span>
          </div>
          {content}
        </div>
      )}
    </div>
  );
}

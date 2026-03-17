import { useState } from 'react';

export default function ChatInput({ onSend, disabled, placeholder = 'Type your message...' }) {
  const [value, setValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e) => {
    e?.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-gradient-to-t from-cyber-dark/90 to-cyber-darker/80 backdrop-blur-xl border-t border-cyber-border rounded-b-2xl shrink-0 relative overflow-hidden">
      {/* Bottom edge glow */}
      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-cyber-green/30 to-transparent"></div>
      
      <div className="flex gap-3 relative z-10">
        <div className="flex-1 relative group">
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={placeholder}
            disabled={disabled}
            className={`w-full rounded-xl bg-white/90 border px-5 py-3.5 text-[15px] !text-black placeholder-gray-400 
              focus:outline-none transition-all duration-300
              disabled:bg-gray-200 disabled:cursor-not-allowed disabled:!text-gray-500
              ${isFocused 
                ? 'border-cyber-green shadow-[0_0_20px_rgba(0,255,156,0.2)] bg-white' 
                : 'border-cyber-border hover:border-cyber-border-hover shadow-cyber'
              }`}
            aria-label="Message input"
          />
          {/* Input field glow effect */}
          {isFocused && (
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-cyber-green/5 via-cyber-green/10 to-cyber-green/5 pointer-events-none blur-sm"></div>
          )}
        </div>
        
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="px-6 py-3.5 bg-gradient-to-br from-cyber-green to-cyber-green-dark text-cyber-black text-[15px] font-semibold rounded-xl 
            hover:from-cyber-green-light hover:to-cyber-green 
            disabled:opacity-40 disabled:cursor-not-allowed disabled:grayscale
            transition-all duration-300 shadow-cyber-glow hover:shadow-cyber-glow-strong
            hover:scale-[1.02] active:scale-[0.98]
            relative overflow-hidden group"
        >
          <span className="relative z-10 flex items-center gap-2">
            Send
            <svg className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </span>
          {/* Button shine effect */}
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div className="absolute inset-0 shimmer"></div>
          </div>
        </button>
      </div>
    </form>
  );
}

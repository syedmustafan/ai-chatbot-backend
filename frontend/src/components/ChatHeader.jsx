export default function ChatHeader({ title = 'AI Assistant', onClose }) {
  return (
    <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-cyber-dark/80 to-cyber-darker/80 backdrop-blur-xl border-b border-cyber-border rounded-t-2xl shrink-0 relative overflow-hidden">
      {/* Subtle glow effect on top edge */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-cyber-green/50 to-transparent"></div>
      
      <div className="flex items-center gap-3">
        {/* Status indicator */}
        <div className="relative">
          <div className="w-2.5 h-2.5 bg-cyber-green rounded-full animate-pulse"></div>
          <div className="absolute inset-0 w-2.5 h-2.5 bg-cyber-green rounded-full animate-ping opacity-75"></div>
        </div>
        <h2 className="text-lg font-semibold text-white tracking-wide">{title}</h2>
      </div>
      
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="p-2 rounded-xl text-gray-400 hover:text-cyber-green hover:bg-cyber-gray/50 transition-all duration-300 group"
          aria-label="Close chat"
        >
          <svg className="w-5 h-5 transition-transform duration-300 group-hover:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}

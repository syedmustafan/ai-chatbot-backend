export default function ChatMessage({ text, sender, timestamp }) {
  const isUser = sender === 'user';
  return (
    <div className={`flex mb-3 ${isUser ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
      <div
        className={`max-w-[85%] rounded-2xl px-5 py-3 backdrop-blur-sm transition-all duration-300 hover:scale-[1.02] ${
          isUser
            ? 'bg-gradient-to-br from-cyber-green to-cyber-green-dark text-cyber-black rounded-br-md shadow-cyber-glow font-medium'
            : 'bg-cyber-gray/60 text-gray-100 rounded-bl-md border border-cyber-border shadow-cyber hover:border-cyber-border-hover'
        }`}
      >
        <p className="text-[15px] leading-relaxed whitespace-pre-wrap break-words">{text}</p>
        {timestamp && (
          <p className={`text-xs mt-2 font-mono ${isUser ? 'text-cyber-darker/70' : 'text-gray-500'}`}>
            {typeof timestamp === 'string' ? timestamp : timestamp?.toLocaleTimeString?.()}
          </p>
        )}
      </div>
    </div>
  );
}

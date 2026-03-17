import { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';

export default function ChatWindow({ messages, isLoading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4 bg-gradient-to-b from-cyber-darker/40 to-cyber-black/40 backdrop-blur-md relative">
      {/* Subtle inner glow */}
      <div className="absolute inset-0 shadow-inner-glow pointer-events-none"></div>
      
      <div className="space-y-2 relative z-10">
        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            text={msg.text}
            sender={msg.sender}
            timestamp={msg.timestamp}
          />
        ))}
        {isLoading && (
          <div className="flex justify-start mb-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="bg-cyber-gray/60 border border-cyber-border text-gray-300 rounded-2xl rounded-bl-md px-5 py-3 shadow-cyber backdrop-blur-sm">
              <span className="inline-flex gap-1.5">
                <span className="w-2 h-2 bg-cyber-green rounded-full animate-bounce shadow-[0_0_8px_rgba(0,255,156,0.6)]" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-cyber-green rounded-full animate-bounce shadow-[0_0_8px_rgba(0,255,156,0.6)]" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-cyber-green rounded-full animate-bounce shadow-[0_0_8px_rgba(0,255,156,0.6)]" style={{ animationDelay: '300ms' }} />
              </span>
            </div>
          </div>
        )}
      </div>
      <div ref={bottomRef} />
    </div>
  );
}

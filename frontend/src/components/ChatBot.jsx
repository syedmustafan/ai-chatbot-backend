import { useState, useCallback } from 'react';
import { sendMessage } from '../services/api';
import ChatHeader from './ChatHeader';
import ChatWindow from './ChatWindow';
import ChatInput from './ChatInput';

const initialMessage = {
  id: 1,
  text: 'Hello! How can I help you today?',
  sender: 'ai',
  timestamp: new Date(),
};

export default function ChatBot() {
  const [messages, setMessages] = useState([initialMessage]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);

  const handleSend = useCallback(async (text) => {
    if (!text.trim()) return;
    setError(null);
    const userMsg = {
      id: Date.now(),
      text: text.trim(),
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const data = await sendMessage(text.trim(), conversationId);
      if (data.success && data.response != null) {
        setConversationId(data.conversation_id || null);
        const aiMsg = {
          id: Date.now() + 1,
          text: data.response,
          sender: 'ai',
          timestamp: data.timestamp ? new Date(data.timestamp) : new Date(),
        };
        setMessages((prev) => [...prev, aiMsg]);
      } else {
        setError(data.error || 'Something went wrong.');
      }
    } catch (err) {
      const message = err.response?.data?.error || err.message || 'Failed to send message.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  const handleClear = useCallback(() => {
    setMessages([initialMessage]);
    setConversationId(null);
    setError(null);
  }, []);

  return (
    <div className="flex flex-col max-w-3xl mx-auto rounded-2xl bg-gradient-to-br from-cyber-dark/60 to-cyber-darker/60 backdrop-blur-2xl border border-cyber-border shadow-cyber-lg min-h-[600px] max-h-[85vh] overflow-hidden relative group hover:border-cyber-border-hover transition-all duration-500">
      {/* Animated corner accents */}
      <div className="absolute top-0 left-0 w-20 h-20 border-t-2 border-l-2 border-cyber-green opacity-30 rounded-tl-2xl transition-opacity duration-300 group-hover:opacity-60"></div>
      <div className="absolute bottom-0 right-0 w-20 h-20 border-b-2 border-r-2 border-cyber-green opacity-30 rounded-br-2xl transition-opacity duration-300 group-hover:opacity-60"></div>
      
      {/* Ambient glow behind the card */}
      <div className="absolute -inset-[1px] bg-gradient-to-br from-cyber-green/10 to-cyber-green-dark/10 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 -z-10"></div>
      
      <ChatHeader title="AI Assistant" onClose={undefined} />
      
      {error && (
        <div className="px-5 py-3 bg-red-900/30 border-b border-red-800/50 text-red-300 text-sm flex items-center justify-between backdrop-blur-sm animate-in slide-in-from-top-2 duration-300">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-red-400 hover:text-red-200 transition-colors p-1 hover:bg-red-900/30 rounded-lg"
            aria-label="Dismiss error"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
      
      <ChatWindow messages={messages} isLoading={isLoading} />
      
      <div className="flex items-center justify-between px-5 py-2 bg-cyber-darker/50 border-t border-cyber-border/50 backdrop-blur-sm">
        <button
          type="button"
          onClick={handleClear}
          className="text-xs text-gray-500 hover:text-cyber-green transition-all duration-300 flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-cyber-gray/30 group"
        >
          <svg className="w-3.5 h-3.5 transition-transform duration-300 group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Clear conversation
        </button>
        <div className="flex items-center gap-2 text-xs text-gray-600 font-mono">
          <div className="w-1.5 h-1.5 bg-cyber-green rounded-full animate-pulse"></div>
          <span>{messages.length - 1} messages</span>
        </div>
      </div>
      
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}

import ChatBot from './components/ChatBot';

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-cyber-black via-cyber-dark to-cyber-darker py-8 px-4 relative overflow-hidden">
      {/* Ambient background glow effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyber-green opacity-5 rounded-full blur-3xl animate-pulse-slow"></div>
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyber-green-dark opacity-5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }}></div>
      
      {/* Grid pattern overlay */}
      <div className="absolute inset-0 opacity-[0.02]" style={{
        backgroundImage: `
          linear-gradient(rgba(0, 255, 156, 0.3) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0, 255, 156, 0.3) 1px, transparent 1px)
        `,
        backgroundSize: '50px 50px'
      }}></div>
      
      <div className="relative z-10">
        <ChatBot />
      </div>
    </div>
  );
}

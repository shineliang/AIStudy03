import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import HistorySidebar from './components/HistorySidebar';
import ToolUsageSidebar from './components/ToolUsageSidebar';
import MemorySidebar from './components/MemorySidebar';

function App() {
  const [showHistorySidebar, setShowHistorySidebar] = useState(false);
  const [showToolUsageSidebar, setShowToolUsageSidebar] = useState(false);
  const [showMemorySidebar, setShowMemorySidebar] = useState(false);
  
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>AI智能助手</h1>
        <div className="sidebar-controls">
          <button onClick={() => setShowHistorySidebar(!showHistorySidebar)}>
            历史对话
          </button>
          <button onClick={() => setShowToolUsageSidebar(!showToolUsageSidebar)}>
            工具记录
          </button>
          <button onClick={() => setShowMemorySidebar(!showMemorySidebar)}>
            记忆记录
          </button>
        </div>
      </header>
      
      <main className="app-main">
        <ChatInterface />
        
        {showHistorySidebar && <HistorySidebar onClose={() => setShowHistorySidebar(false)} />}
        {showToolUsageSidebar && <ToolUsageSidebar onClose={() => setShowToolUsageSidebar(false)} />}
        {showMemorySidebar && <MemorySidebar onClose={() => setShowMemorySidebar(false)} />}
      </main>
    </div>
  );
}

export default App; 
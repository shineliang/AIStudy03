import React, { useState, useEffect } from 'react';
import './Sidebar.css';

function HistorySidebar({ onClose }) {
  const [history, setHistory] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    fetchHistory();
  }, []);
  
  const fetchHistory = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/history');
      const data = await response.json();
      setHistory(data.history);
    } catch (error) {
      console.error('获取历史记录失败:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const filteredHistory = history.filter(item => 
    item.user.toLowerCase().includes(searchTerm.toLowerCase()) || 
    item.ai.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>历史对话</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      
      <div className="search-container">
        <input
          type="text"
          placeholder="搜索历史对话..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>
      
      <div className="sidebar-content">
        {isLoading ? (
          <div className="loading">加载中...</div>
        ) : filteredHistory.length > 0 ? (
          filteredHistory.map((item, index) => (
            <div key={index} className="history-item">
              <div className="timestamp">{item.timestamp}</div>
              <div className="user-message">
                <strong>用户:</strong> {item.user}
              </div>
              <div className="ai-message">
                <strong>AI:</strong> {item.ai}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-message">
            {searchTerm ? '没有找到匹配的对话' : '暂无历史对话'}
          </div>
        )}
      </div>
    </div>
  );
}

export default HistorySidebar; 
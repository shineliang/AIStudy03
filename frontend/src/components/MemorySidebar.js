import React, { useState, useEffect } from 'react';
import './Sidebar.css';

function MemorySidebar({ onClose }) {
  const [memories, setMemories] = useState([]);
  const [filterType, setFilterType] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [memoryTypes, setMemoryTypes] = useState([]);
  
  useEffect(() => {
    fetchMemories();
  }, []);
  
  const fetchMemories = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/memories');
      const data = await response.json();
      setMemories(data.memories);
      
      // 提取所有记忆类型
      const types = [...new Set(data.memories.map(item => item.type))];
      setMemoryTypes(types);
    } catch (error) {
      console.error('获取记忆记录失败:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const filteredMemories = filterType 
    ? memories.filter(item => item.type === filterType)
    : memories;
  
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>记忆记录</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      
      <div className="filter-container">
        <select 
          value={filterType} 
          onChange={(e) => setFilterType(e.target.value)}
        >
          <option value="">所有类型</option>
          {memoryTypes.map((type, index) => (
            <option key={index} value={type}>{type}</option>
          ))}
        </select>
      </div>
      
      <div className="sidebar-content">
        {isLoading ? (
          <div className="loading">加载中...</div>
        ) : filteredMemories.length > 0 ? (
          filteredMemories.map((item, index) => (
            <div key={index} className="memory-item">
              <div className="timestamp">{item.created_at}</div>
              <div className="memory-type">
                <strong>类型:</strong> {item.type}
              </div>
              <div className="memory-content">
                <strong>内容:</strong> {item.content}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-message">
            {filterType ? `没有找到${filterType}类型的记忆` : '暂无记忆记录'}
          </div>
        )}
      </div>
    </div>
  );
}

export default MemorySidebar; 
import React, { useState, useEffect } from 'react';
import './Sidebar.css';

function ToolUsageSidebar({ onClose }) {
  const [toolUsages, setToolUsages] = useState([]);
  const [filterTool, setFilterTool] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [toolTypes, setToolTypes] = useState([]);
  
  useEffect(() => {
    fetchToolUsages();
  }, []);
  
  const fetchToolUsages = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/tool-usage');
      const data = await response.json();
      setToolUsages(data.tool_usages);
      
      // 提取所有工具类型
      const types = [...new Set(data.tool_usages.map(item => item.tool_name))];
      setToolTypes(types);
    } catch (error) {
      console.error('获取工具使用记录失败:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const filteredUsages = filterTool 
    ? toolUsages.filter(item => item.tool_name === filterTool)
    : toolUsages;
  
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>工具使用记录</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      
      <div className="filter-container">
        <select 
          value={filterTool} 
          onChange={(e) => setFilterTool(e.target.value)}
        >
          <option value="">所有工具</option>
          {toolTypes.map((type, index) => (
            <option key={index} value={type}>{type}</option>
          ))}
        </select>
      </div>
      
      <div className="sidebar-content">
        {isLoading ? (
          <div className="loading">加载中...</div>
        ) : filteredUsages.length > 0 ? (
          filteredUsages.map((item, index) => (
            <div key={index} className="tool-usage-item">
              <div className="timestamp">{item.timestamp}</div>
              <div className="tool-name">
                <strong>工具:</strong> {item.tool_name}
              </div>
              <div className="parameters">
                <strong>参数:</strong> 
                <pre>{JSON.stringify(item.parameters, null, 2)}</pre>
              </div>
              <div className="result">
                <strong>结果:</strong> {item.result}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-message">
            {filterTool ? `没有找到${filterTool}的使用记录` : '暂无工具使用记录'}
          </div>
        )}
      </div>
    </div>
  );
}

export default ToolUsageSidebar; 
import React, { useState, useEffect, useRef } from 'react';
import './ChatInterface.css';
import SuggestedQuestions from './SuggestedQuestions';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const messagesEndRef = useRef(null);
  
  // 获取初始推荐问题
  useEffect(() => {
    fetchSuggestedQuestions();
  }, []);
  
  // 滚动到最新消息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const fetchSuggestedQuestions = async (context = '') => {
    try {
      console.log('正在获取推荐问题，上下文长度:', context ? context.length : 0);
      const response = await fetch(`/api/suggested-questions?context=${encodeURIComponent(context || '')}`);
      
      if (!response.ok) {
        throw new Error(`API响应错误: ${response.status} ${response.statusText}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        console.error('API返回了非JSON响应:', text.substring(0, 100) + '...');
        throw new Error('服务器返回了非JSON响应');
      }
      
      const data = await response.json();
      console.log('获取到推荐问题:', data.questions);
      setSuggestedQuestions(data.questions);
    } catch (error) {
      console.error('获取推荐问题失败:', error);
      // 设置一些默认问题，以防API调用失败
      setSuggestedQuestions([
        "今天北京的天气怎么样？",
        "查询最近的抖音热搜",
        "查询我本周的考勤记录",
        "查询我本周的排班信息",
        "我想请明天的事假"
      ]);
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    
    const userMessage = inputValue;
    setInputValue('');
    setIsLoading(true);
    
    // 添加用户消息到对话
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    
    try {
      // 使用流式API获取回复
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      });
      
      if (!response.body) {
        throw new Error('ReadableStream not supported');
      }
      
      // 创建一个临时消息用于流式更新
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let aiResponse = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        aiResponse += chunk;
        
        // 更新最后一条消息的内容
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1].content = aiResponse;
          return newMessages;
        });
      }
      
      // 对话完成后获取新的推荐问题
      fetchSuggestedQuestions(aiResponse);
      
    } catch (error) {
      console.error('发送消息失败:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '抱歉，发生了错误，请稍后再试。' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleQuestionClick = (question) => {
    setInputValue(question);
  };
  
  return (
    <div className="chat-container">
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>欢迎使用AI智能助手</h2>
            <p>您可以询问我任何问题，或者尝试以下推荐问题：</p>
            <SuggestedQuestions 
              questions={suggestedQuestions} 
              onQuestionClick={handleQuestionClick} 
            />
          </div>
        )}
        
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`message ${message.role === 'user' ? 'user-message' : 'ai-message'}`}
          >
            <div className="message-content">{message.content}</div>
          </div>
        ))}
        
        {isLoading && (
          <div className="loading-indicator">
            <div className="dot"></div>
            <div className="dot"></div>
            <div className="dot"></div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
        
        {messages.length > 0 && !isLoading && (
          <div className="suggested-questions-container">
            <h3>您可能还想问：</h3>
            <SuggestedQuestions 
              questions={suggestedQuestions} 
              onQuestionClick={handleQuestionClick} 
            />
          </div>
        )}
      </div>
      
      <form className="input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="输入您的问题..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !inputValue.trim()}>
          发送
        </button>
      </form>
    </div>
  );
}

export default ChatInterface; 
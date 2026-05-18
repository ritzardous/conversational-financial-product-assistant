import React, { useState, useEffect, useRef, type KeyboardEvent } from 'react';
import './App.css';
import type { Message, ChatResponse } from './types';
import { sendMessage, resetUser } from './api';

function App() {
  const [userId, setUserId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    let storedUserId = localStorage.getItem('financial_assistant_user_id');
    if (!storedUserId) {
      storedUserId = crypto.randomUUID();
      localStorage.setItem('financial_assistant_user_id', storedUserId);
    }
    setUserId(storedUserId);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleNewUser = async () => {
    if (window.confirm("Are you sure you want to start as a new user?")) {
      try {
        if (userId) {
          await resetUser(userId);
        }
      } catch (err) {
        console.error("Failed to reset old user", err);
      }
      const newUserId = crypto.randomUUID();
      localStorage.setItem('financial_assistant_user_id', newUserId);
      setMessages([]);
      setError(null);
      setUserId(newUserId);
    }
  };

  const handleResetChat = async () => {
    try {
      if (userId) {
        await resetUser(userId);
      }
      setMessages([]);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to reset chat");
    }
  };

  const handleSend = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || loading) return;

    const userMsgId = crypto.randomUUID();
    const newUserMsg: Message = { id: userMsgId, role: "user", content: trimmedInput };
    
    setMessages((prev) => [...prev, newUserMsg]);
    setLoading(true);
    setError(null);
    setInput('');

    try {
      const response: ChatResponse = await sendMessage(userId, trimmedInput);
      
      let assistantContent = response.reply;
      if (response.requires_more_info && response.missing_fields && response.missing_fields.length > 0) {
        assistantContent += `\n\n[Needs: ${response.missing_fields.join(", ")}]`;
      }

      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: assistantContent,
        meta: response
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="title">AI Financial Assistant</div>
        <div className="controls">
          <input 
            type="text" 
            className="user-id-display"
            readOnly 
            value={userId.slice(0, 8) + '...'} 
            title={userId}
          />
          <button className="secondary-btn" onClick={handleNewUser}>New User</button>
          <button className="secondary-btn" onClick={handleResetChat}>Reset</button>
        </div>
      </header>
      
      <main className="messages">
        <div className="messages-content">
          {messages.length === 0 && !loading && !error && (
            <div className="welcome-screen">
              <h2>How can I help you today?</h2>
              <p>Ask me about financial products, eligibility, or fees.</p>
            </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className={`msg msg-${msg.role}`}>
              <div className="msg-content">{msg.content}</div>
              {msg.role === 'assistant' && msg.meta && (
                <details className="debug-panel">
                  <summary>Debug info</summary>
                  <pre>{JSON.stringify(msg.meta, null, 2)}</pre>
                </details>
              )}
            </div>
          ))}
          {loading && (
            <div className="msg msg-assistant loading-msg">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          )}
          {error && <div className="error">{error}</div>}
          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="input-area">
        <div className="input-row">
          <textarea
            ref={textareaRef}
            rows={1}
            placeholder="Message Assistant..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button className="send-btn" onClick={handleSend} disabled={loading || !input.trim()}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </footer>
    </div>
  );
}

export default App;

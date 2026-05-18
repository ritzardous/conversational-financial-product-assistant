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

  useEffect(() => {
    let storedUserId = localStorage.getItem('kyma_user_id');
    if (!storedUserId) {
      storedUserId = crypto.randomUUID();
      localStorage.setItem('kyma_user_id', storedUserId);
    }
    setUserId(storedUserId);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
      localStorage.setItem('kyma_user_id', newUserId);
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
        <div className="title">Kyma Financial Assistant</div>
        <div className="controls">
          <input 
            type="text" 
            readOnly 
            value={userId.slice(0, 8) + '...'} 
            title={userId}
            style={{ width: '80px', marginRight: '8px', fontSize: '12px' }}
          />
          <button onClick={handleNewUser} style={{ marginRight: '8px' }}>New User</button>
          <button onClick={handleResetChat}>Reset Chat</button>
        </div>
      </header>
      
      <main className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`msg msg-${msg.role}`}>
            <div>{msg.content}</div>
            {msg.role === 'assistant' && msg.meta && (
              <details>
                <summary>Debug info</summary>
                <pre>{JSON.stringify(msg.meta, null, 2)}</pre>
              </details>
            )}
          </div>
        ))}
        {loading && <div className="msg msg-assistant">Thinking...</div>}
        {error && <div className="error">{error}</div>}
        <div ref={messagesEndRef} />
      </main>

      <footer className="input-area">
        <div className="input-row">
          <textarea
            rows={2}
            placeholder="Ask about our products..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button onClick={handleSend} disabled={loading || !input.trim()}>
            Send
          </button>
        </div>
      </footer>
    </div>
  );
}

export default App;

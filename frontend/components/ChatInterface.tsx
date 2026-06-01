'use client';

import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Image, Play } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  imageUrl?: string;
  videoUrl?: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await axios.post('http://localhost:8000/api/chat', {
        prompt: input,
        history: messages
      });

      const aiMsg: Message = {
        role: 'assistant',
        content: res.data.response,
        imageUrl: res.data.image_url,
        videoUrl: res.data.video_url
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "⚠️ Sovereign neural pathways temporarily disrupted. Please try again."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-gray-800 p-6">
        <h2 className="text-3xl font-bold">Sovereign Intelligence Portal</h2>
        <p className="text-emerald-400 text-sm">Multi-Neural • Chroma Memory • Gemini Native Vision</p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-auto p-6 space-y-8 chat-container">
        {messages.length === 0 && (
          <div className="text-center mt-20">
            <div className="mx-auto w-20 h-20 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center text-5xl mb-6">
              🌍
            </div>
            <h3 className="text-2xl font-semibold mb-2">Welcome to Effiong AI</h3>
            <p className="text-gray-400 max-w-md mx-auto">
              The finest prediction engine for human, animal, and socio-political events with deep African heritage intelligence.
            </p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-3xl ${msg.role === 'user' ? 'bg-emerald-600' : 'bg-gray-900'} rounded-2xl px-6 py-4`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
              
              {msg.imageUrl && (
                <img src={msg.imageUrl} alt="Generated" className="mt-4 rounded-xl max-w-full" />
              )}
              {msg.videoUrl && (
                <video src={msg.videoUrl} controls className="mt-4 rounded-xl max-w-full" />
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-900 rounded-2xl px-6 py-4">
              Processing through sovereign neural pathways...
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-6 border-t border-gray-800">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Engage Effiong AI — Ask anything..."
            className="flex-1 bg-gray-900 border border-gray-700 rounded-2xl px-6 py-4 focus:outline-none focus:border-emerald-500"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 px-8 rounded-2xl transition flex items-center justify-center"
          >
            <Send className="w-6 h-6" />
          </button>
        </div>
        <p className="text-center text-xs text-gray-500 mt-3">
          Powered by Gemini • Chroma Vector Memory • Sovereign African Intelligence
        </p>
      </div>
    </div>
  );
}

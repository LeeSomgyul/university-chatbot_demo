import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import { chatAPI } from '../services/api';
import type { Message, UserProfile } from '../types/chat';
import './ChatWindow.css';

const ChatWindow: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 테스트용 사용자 프로필 (나중에 폼으로 입력받을 수 있음)
  const [userProfile] = useState<UserProfile>({
    admission_year: 2020,
    track: '일반',
    courses_taken: [
      {
        course_name: '프로그래밍기초',
        course_code: 'CSE101',
        credit: 3,
        course_area: '전공필수',
      },
      {
        course_name: '자료구조',
        course_code: 'CSE201',
        credit: 3,
        course_area: '전공필수',
      },
    ],
  });

  // 자동 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 초기 환영 메시지
  useEffect(() => {
    setMessages([
      {
        role: 'assistant',
        content: '안녕하세요! 순천대학교 컴퓨터공학과 챗봇입니다. 무엇을 도와드릴까요? 😊',
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    };

    // 사용자 메시지 추가
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // API 호출
      const response = await chatAPI.sendMessage({
        message: inputValue,
        session_id: sessionId,
        user_profile: userProfile,
        history: messages,
      });

      // 세션 ID 저장
      if (response.session_id) {
        setSessionId(response.session_id);
      }

      // 챗봇 응답 추가
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // 에러 메시지 표시
      const errorMessage: Message = {
        role: 'assistant',
        content: '죄송해요, 오류가 발생했어요. 다시 시도해주세요. 😅',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>순천대 컴공 챗봇</h2>
        <p className="chat-subtitle">학사 정보를 물어보세요!</p>
      </div>

      <div className="messages-container">
        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}
        {isLoading && (
          <div className="loading-indicator">
            <div className="typing-animation">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <textarea
          className="message-input"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="메시지를 입력하세요..."
          rows={1}
          disabled={isLoading}
        />
        <button
          className="send-button"
          onClick={handleSendMessage}
          disabled={isLoading || !inputValue.trim()}
        >
          전송
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
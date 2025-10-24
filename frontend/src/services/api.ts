import axios from 'axios';
import type { ChatRequest, ChatResponse } from '../types/chat';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatAPI = {
  // 채팅 메시지 전송
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    
    const storedSessionId = sessionStorage.getItem('chat_session_id');
    const cleanRequest = {
      message: request.message,
      session_id: storedSessionId,
      user_profile: null, 
      history: []
    };

    console.log('📤 전송 데이터:', cleanRequest);

    const response = await api.post<ChatResponse>('/chat', cleanRequest);

    if (response.data.session_id) {
      sessionStorage.setItem('chat_session_id', response.data.session_id);
      console.log('💾 세션 ID 저장:', response.data.session_id);
    }
    
    return response.data;
  },

  // 헬스체크
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
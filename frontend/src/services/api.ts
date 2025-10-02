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
    const response = await api.post<ChatResponse>('/chat', request);
    return response.data;
  },

  // 헬스체크
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
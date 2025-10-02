export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface CourseInput {
  course_code?: string;
  course_name: string;
  credit: number;
  grade?: string;
  course_area: string;
}

export interface UserProfile {
  admission_year: number;
  current_semester?: number;
  courses_taken: CourseInput[];
  track: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  user_profile?: UserProfile;
  history: Message[];
}

export interface SearchSource {
  content: string;
  metadata?: Record<string, unknown>;
  score?: number;
}

export interface ChatResponse {
  message: string;
  sources?: SearchSource[];
  query_type?: 'general' | 'curriculum' | 'hybrid';
  session_id?: string;
}
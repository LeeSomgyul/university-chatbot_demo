"""
API 요청/응답 스키마 정의
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CourseInput(BaseModel):
    """사용자가 입력한 수강 과목"""
    course_code: Optional[str] = None
    course_name: str
    credit: int
    grade: Optional[str] = None  # A+, A0, B+, etc.
    course_area: str  # 전공필수, 전공선택, 교양필수, 교양선택


class UserProfile(BaseModel):
    """사용자 프로필 (세션 데이터)"""
    admission_year: int  # 학번
    current_semester: Optional[int] = None  # 현재 학기 (1~8)
    courses_taken: List[CourseInput] = Field(default_factory=list)
    track: str = "일반"  # 일반, AI트랙 등


class ChatMessage(BaseModel):
    """채팅 메시지"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """챗봇 요청"""
    message: str
    session_id: Optional[str] = None
    user_profile: Optional[UserProfile] = None
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """챗봇 응답"""
    message: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    query_type: Optional[str] = None  # "curriculum", "general", "hybrid"
    session_id: Optional[str] = None


class HealthCheck(BaseModel):
    """헬스체크 응답"""
    status: str
    timestamp: datetime
    version: str = "1.0.0"
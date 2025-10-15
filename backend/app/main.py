"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager

from app.config import settings
from app.models.schemas import (
    ChatRequest, 
    ChatResponse, 
    HealthCheck,
    UserProfile
)
from app.models.session import session_store
from app.services.chatbot import chatbot
from app.routes import graduation


# 앱 시작/종료 이벤트
@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    # 시작 시
    print("🚀 애플리케이션 시작")
    print(f"📍 환경: {settings.environment}")
    print(f"🤖 LLM 모델: {settings.model_name}")
    
    yield
    
    # 종료 시
    print("👋 애플리케이션 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="School Chatbot API",
    description="순천대학교 컴퓨터공학과 챗봇 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graduation.router)


@app.get("/", response_model=HealthCheck)
async def root():
    """헬스체크"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now()
    )


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """헬스체크"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now()
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """챗봇 대화 엔드포인트"""
    try:
        # 세션 관리 (기존 코드)
        session_id = request.session_id
        if not session_id:
            session_id = session_store.create_session(request.user_profile)
        else:
            session = session_store.get_session(session_id)
            if not session:
                session_id = session_store.create_session(request.user_profile)
            elif request.user_profile:
                session_store.update_profile(session_id, request.user_profile)
        
        # 세션에서 사용자 프로필 가져오기
        session = session_store.get_session(session_id)
        user_profile = session['user_profile'] if session else request.user_profile
        
        # 챗봇 호출
        result = chatbot.chat(
            message=request.message,
            user_profile=user_profile,
            history=request.history
        )
        
        # ⭐ 챗봇이 UserProfile을 생성했다면 세션에 저장
        # (result에 'user_profile'이 포함되어 있으면)
        if 'user_profile' in result and result['user_profile']:
            session_store.update_profile(session_id, result['user_profile'])
        
        # 세션에 메시지 저장 (기존 코드)
        session_store.add_message(session_id, {
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now()
        })
        session_store.add_message(session_id, {
            "role": "assistant",
            "content": result['message'],
            "timestamp": datetime.now()
        })
        
        return ChatResponse(
            message=result['message'],
            sources=result.get('sources', []),
            query_type=result.get('query_type'),
            session_id=session_id
        )
    
    except Exception as e:
        print(f"❌ 챗봇 오류: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"챗봇 처리 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/session/create")
async def create_session(user_profile: UserProfile = None):
    """새 세션 생성"""
    session_id = session_store.create_session(user_profile)
    return {"session_id": session_id}


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """세션 정보 조회"""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    return {
        "session_id": session_id,
        "user_profile": session.get('user_profile'),
        "history_count": len(session.get('history', [])),
        "created_at": session.get('created_at'),
        "last_accessed": session.get('last_accessed')
    }


@app.put("/session/{session_id}/profile")
async def update_profile(session_id: str, user_profile: UserProfile):
    """세션의 사용자 프로필 업데이트"""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    session_store.update_profile(session_id, user_profile)
    return {"message": "프로필이 업데이트되었습니다"}


@app.delete("/sessions/cleanup")
async def cleanup_sessions(hours: int = 24):
    """오래된 세션 정리"""
    deleted = session_store.clear_old_sessions(hours)
    return {"deleted_sessions": deleted}


# 개발용 엔드포인트
if settings.debug:
    @app.get("/debug/sessions")
    async def debug_sessions():
        """모든 세션 조회 (디버그용)"""
        return {
            "total_sessions": len(session_store.sessions),
            "sessions": {
                sid: {
                    "has_profile": data.get('user_profile') is not None,
                    "message_count": len(data.get('history', [])),
                    "created_at": data.get('created_at'),
                }
                for sid, data in session_store.sessions.items()
            }
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
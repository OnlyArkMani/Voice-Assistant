from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid

class SessionManager:
    """Manages user sessions and conversation history"""
    
    def __init__(self, timeout_seconds: int = 3600):
        self.sessions: Dict[str, Dict] = {}
        self.timeout = timeout_seconds
    
    def create_session(self, user_id: str = None) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            'id': session_id,
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'conversation_history': [],
            'context': {},
            'preferences': {}
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        self._cleanup_expired_sessions()
        
        session = self.sessions.get(session_id)
        
        if session:
            # Update last activity
            session['last_activity'] = datetime.now()
            return session
        
        return None
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None):
        """Add message to conversation history"""
        session = self.get_session(session_id)
        
        if session:
            message = {
                'role': role,  # 'user' or 'assistant'
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            session['conversation_history'].append(message)
    
    def get_conversation_history(self, session_id: str, last_n: int = None) -> List[Dict]:
        """Get conversation history"""
        session = self.get_session(session_id)
        
        if session:
            history = session['conversation_history']
            if last_n:
                return history[-last_n:]
            return history
        
        return []
    
    def update_context(self, session_id: str, key: str, value: any):
        """Update session context (e.g., current equipment being discussed)"""
        session = self.get_session(session_id)
        
        if session:
            session['context'][key] = value
    
    def get_context(self, session_id: str, key: str = None) -> any:
        """Get session context"""
        session = self.get_session(session_id)
        
        if session:
            if key:
                return session['context'].get(key)
            return session['context']
        
        return None
    
    def clear_session(self, session_id: str):
        """Clear a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = []
        
        for session_id, session in self.sessions.items():
            if (now - session['last_activity']).seconds > self.timeout:
                expired.append(session_id)
        
        for session_id in expired:
            del self.sessions[session_id]
    
    def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        self._cleanup_expired_sessions()
        return len(self.sessions)
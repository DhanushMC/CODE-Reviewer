from typing import Dict
from app.schemas.models import SessionData

# In-memory session storage (consider Redis for production)
sessions: Dict[str, SessionData] = {}


def create_session(session_data: SessionData) -> str:
    """Create a new session"""
    sessions[session_data.session_id] = session_data
    return session_data.session_id


def get_session(session_id: str) -> SessionData:
    """Retrieve session data"""
    if session_id not in sessions:
        raise ValueError(f"Session {session_id} not found")
    return sessions[session_id]


def update_session(session_id: str, **kwargs) -> SessionData:
    """Update session with new data"""
    session = get_session(session_id)
    for key, value in kwargs.items():
        if hasattr(session, key):
            setattr(session, key, value)
    sessions[session_id] = session
    return session


def delete_session(session_id: str):
    """Delete a session"""
    if session_id in sessions:
        del sessions[session_id]

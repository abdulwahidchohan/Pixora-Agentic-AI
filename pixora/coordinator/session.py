"""
Session management for Pixora AI agents.

This module handles user sessions, conversation history, and context management.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import json

from ..models import UserSession, UserRequest
from ..utils.logger import get_logger
from ..utils.embeddings import get_embeddings_manager

logger = get_logger(__name__)

@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation."""
    turn_id: str
    timestamp: datetime
    user_message: str
    system_response: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SessionContext:
    """Represents the context for a user session."""
    session_id: str
    user_id: str
    start_time: datetime
    last_activity: datetime
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    workflow_context: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

class SessionManager:
    """
    Manages user sessions and conversation context.
    
    This class handles session lifecycle, conversation history,
    and context management for personalized AI interactions.
    """
    
    def __init__(self, session_timeout_hours: int = 24):
        """Initialize the session manager."""
        self.logger = logger
        self.sessions: Dict[str, SessionContext] = {}
        self.session_timeout_hours = session_timeout_hours
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_expired_sessions())
    
    def create_session(self, user_id: str) -> str:
        """
        Create a new session for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            The session ID
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session_context = SessionContext(
            session_id=session_id,
            user_id=user_id,
            start_time=now,
            last_activity=now
        )
        
        self.sessions[session_id] = session_context
        self.logger.info(f"Created session {session_id} for user {user_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get a session by ID."""
        session = self.sessions.get(session_id)
        if session and session.is_active:
            # Update last activity
            session.last_activity = datetime.now()
            return session
        return None
    
    def get_user_session(self, user_id: str) -> Optional[SessionContext]:
        """Get the active session for a user."""
        for session in self.sessions.values():
            if session.user_id == user_id and session.is_active:
                # Update last activity
                session.last_activity = datetime.now()
                return session
        return None
    
    def add_conversation_turn(self, session_id: str, user_message: str, 
                             system_response: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a conversation turn to a session.
        
        Args:
            session_id: The session ID
            user_message: The user's message
            system_response: The system's response
            metadata: Additional metadata for the turn
            
        Returns:
            True if the turn was added successfully, False otherwise
        """
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return False
        
        turn = ConversationTurn(
            turn_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            user_message=user_message,
            system_response=system_response,
            metadata=metadata or {}
        )
        
        session.conversation_history.append(turn)
        session.last_activity = datetime.now()
        
        # Limit conversation history to prevent memory issues
        if len(session.conversation_history) > 100:
            session.conversation_history = session.conversation_history[-50:]
        
        self.logger.debug(f"Added conversation turn to session {session_id}")
        return True
    
    def update_user_preferences(self, session_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences for a session.
        
        Args:
            session_id: The session ID
            preferences: The preferences to update
            
        Returns:
            True if the preferences were updated successfully, False otherwise
        """
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return False
        
        session.user_preferences.update(preferences)
        session.last_activity = datetime.now()
        
        self.logger.info(f"Updated preferences for session {session_id}")
        return True
    
    def get_user_preferences(self, session_id: str) -> Dict[str, Any]:
        """Get user preferences for a session."""
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return {}
        return session.user_preferences.copy()
    
    def update_workflow_context(self, session_id: str, workflow_id: str, 
                               context_data: Dict[str, Any]) -> bool:
        """
        Update workflow context for a session.
        
        Args:
            session_id: The session ID
            workflow_id: The workflow ID
            context_data: The context data to update
            
        Returns:
            True if the context was updated successfully, False otherwise
        """
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return False
        
        if workflow_id not in session.workflow_context:
            session.workflow_context[workflow_id] = {}
        
        session.workflow_context[workflow_id].update(context_data)
        session.last_activity = datetime.now()
        
        self.logger.debug(f"Updated workflow context for session {session_id}, workflow {workflow_id}")
        return True
    
    def get_workflow_context(self, session_id: str, workflow_id: str) -> Dict[str, Any]:
        """Get workflow context for a session."""
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return {}
        return session.workflow_context.get(workflow_id, {}).copy()
    
    def get_conversation_summary(self, session_id: str, max_turns: int = 10) -> str:
        """
        Get a summary of recent conversation turns.
        
        Args:
            session_id: The session ID
            max_turns: Maximum number of turns to include
            
        Returns:
            A summary of the conversation
        """
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return ""
        
        recent_turns = session.conversation_history[-max_turns:]
        if not recent_turns:
            return ""
        
        summary_parts = []
        for turn in recent_turns:
            summary_parts.append(f"User: {turn.user_message}")
            summary_parts.append(f"Assistant: {turn.system_response}")
        
        return "\n".join(summary_parts)
    
    def get_relevant_context(self, session_id: str, current_request: str, 
                           max_context_length: int = 1000) -> str:
        """
        Get relevant context from the session for a current request.
        
        Args:
            session_id: The session ID
            current_request: The current user request
            max_context_length: Maximum length of context to return
            
        Returns:
            Relevant context information
        """
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return ""
        
        # Get user preferences
        preferences = []
        for key, value in session.user_preferences.items():
            preferences.append(f"{key}: {value}")
        
        # Get recent conversation summary
        conversation_summary = self.get_conversation_summary(session_id, max_turns=5)
        
        # Combine context
        context_parts = []
        if preferences:
            context_parts.append("User Preferences:")
            context_parts.extend(preferences)
            context_parts.append("")
        
        if conversation_summary:
            context_parts.append("Recent Conversation:")
            context_parts.append(conversation_summary)
        
        context = "\n".join(context_parts)
        
        # Truncate if too long
        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."
        
        return context
    
    def end_session(self, session_id: str) -> bool:
        """
        End a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if the session was ended successfully, False otherwise
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.is_active = False
        session.last_activity = datetime.now()
        
        self.logger.info(f"Ended session {session_id}")
        return True
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        cutoff_time = datetime.now() - timedelta(hours=self.session_timeout_hours)
        
        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            if session.last_activity < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            self.end_session(session_id)
        
        if sessions_to_remove:
            self.logger.info(f"Cleaned up {len(sessions_to_remove)} expired sessions")
    
    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                self.cleanup_expired_sessions()
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                self.logger.error(f"Error in session cleanup: {str(e)}")
                await asyncio.sleep(3600)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about all sessions."""
        active_sessions = sum(1 for s in self.sessions.values() if s.is_active)
        total_sessions = len(self.sessions)
        
        total_conversation_turns = sum(
            len(s.conversation_history) for s in self.sessions.values()
        )
        
        return {
            "active_sessions": active_sessions,
            "total_sessions": total_sessions,
            "total_conversation_turns": total_conversation_turns,
            "session_timeout_hours": self.session_timeout_hours
        }

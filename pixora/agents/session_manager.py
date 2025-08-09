"""
Session Manager for Pixora system.

Manages user sessions, workflow state, and session persistence.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from ..models import UserRequest, EnhancedPrompt, GeneratedImage
from ..utils.logger import get_logger
from ..utils.config import config

logger = get_logger(__name__)


class SessionManager:
    """
    Agent responsible for session management and workflow coordination.

    Performs:
    - Session creation and management
    - Workflow state tracking
    - Session persistence and recovery
    - User interaction history
    - Session cleanup and maintenance
    """

    def __init__(self):
        """Initialize the SessionManager."""
        self.logger = logger
        self.config = config
        self.active_sessions = {}
        self.session_history = {}
        self._load_session_config()

    def _load_session_config(self):
        """Load session configuration from config."""
        self.max_session_duration = getattr(self.config, 'max_session_duration_hours', 24)
        self.max_sessions_per_user = getattr(self.config, 'max_sessions_per_user', 10)
        self.session_cleanup_interval = getattr(self.config, 'session_cleanup_interval_hours', 1)

    async def create_session(self, user_id: str, initial_data: Dict[str, Any] = None) -> str:
        """
        Create a new session for a user.

        Args:
            user_id: The user ID
            initial_data: Optional initial session data

        Returns:
            Session ID string
        """
        try:
            # Check if user has too many active sessions
            user_sessions = self._get_user_active_sessions(user_id)
            if len(user_sessions) >= self.max_sessions_per_user:
                # Close oldest session
                oldest_session = min(user_sessions, key=lambda s: s.get('created_at', datetime.now()))
                await self.close_session(oldest_session['session_id'])
            
            # Generate session ID
            session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # Create session data
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "status": "active",
                "workflow_state": "initialized",
                "interaction_count": 0,
                "total_images_generated": 0,
                "current_workflow": None,
                "workflow_history": [],
                "user_preferences": {},
                "error_count": 0,
                "last_error": None,
                **(initial_data or {})
            }
            
            # Store session
            self.active_sessions[session_id] = session_data
            
            # Initialize session history
            self.session_history[session_id] = []
            
            self.logger.info("Session created",
                            session_id=session_id,
                            user_id=user_id)
            
            return session_id
            
        except Exception as e:
            self.logger.error("Failed to create session",
                            user_id=user_id,
                            error=str(e))
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session information.

        Args:
            session_id: The session ID

        Returns:
            Session data or None if not found
        """
        try:
            # Check active sessions first
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id].copy()
                session['is_active'] = True
                return session
            
            # Check session history
            if session_id in self.session_history:
                # Reconstruct session data from history
                return await self._reconstruct_session_from_history(session_id)
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to retrieve session",
                            session_id=session_id,
                            error=str(e))
            return None

    async def _reconstruct_session_from_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Reconstruct session data from history."""
        try:
            if session_id not in self.session_history:
                return None
            
            history = self.session_history[session_id]
            if not history:
                return None
            
            # Get the last session state
            last_state = history[-1]
            
            # Reconstruct session data
            session_data = {
                "session_id": session_id,
                "user_id": last_state.get('user_id'),
                "created_at": history[0].get('timestamp') if history else None,
                "last_updated": last_state.get('timestamp'),
                "status": "closed",
                "workflow_state": last_state.get('workflow_state', 'unknown'),
                "interaction_count": len(history),
                "total_images_generated": last_state.get('total_images_generated', 0),
                "current_workflow": None,
                "workflow_history": [h.get('workflow_id') for h in history if h.get('workflow_id')],
                "user_preferences": last_state.get('user_preferences', {}),
                "error_count": sum(1 for h in history if h.get('error')),
                "last_error": next((h.get('error') for h in reversed(history) if h.get('error')), None),
                "is_active": False
            }
            
            return session_data
            
        except Exception as e:
            self.logger.error("Failed to reconstruct session from history",
                            session_id=session_id,
                            error=str(e))
            return None

    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session data.

        Args:
            session_id: The session ID
            updates: Dictionary of updates to apply

        Returns:
            True if updated successfully
        """
        try:
            if session_id not in self.active_sessions:
                self.logger.warning("Attempted to update non-active session",
                                   session_id=session_id)
                return False
            
            # Apply updates
            for key, value in updates.items():
                if key in self.active_sessions[session_id]:
                    self.active_sessions[session_id][key] = value
            
            # Update timestamp
            self.active_sessions[session_id]['last_updated'] = datetime.now().isoformat()
            
            # Log the update
            self.logger.debug("Session updated",
                             session_id=session_id,
                             updates=list(updates.keys()))
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to update session",
                            session_id=session_id,
                            error=str(e))
            return False

    async def add_interaction(self, session_id: str, interaction_type: str, 
                             interaction_data: Dict[str, Any]) -> bool:
        """
        Add an interaction to the session.

        Args:
            session_id: The session ID
            interaction_type: Type of interaction
            interaction_data: Interaction data

        Returns:
            True if added successfully
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            # Create interaction record
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "type": interaction_type,
                "data": interaction_data,
                "session_id": session_id,
                "user_id": self.active_sessions[session_id]["user_id"]
            }
            
            # Add to session history
            if session_id not in self.session_history:
                self.session_history[session_id] = []
            self.session_history[session_id].append(interaction)
            
            # Update session stats
            self.active_sessions[session_id]["interaction_count"] += 1
            self.active_sessions[session_id]["last_updated"] = datetime.now().isoformat()
            
            # Update workflow state if applicable
            if interaction_type == "workflow_started":
                self.active_sessions[session_id]["workflow_state"] = "in_progress"
                self.active_sessions[session_id]["current_workflow"] = interaction_data.get("workflow_id")
            elif interaction_type == "workflow_completed":
                self.active_sessions[session_id]["workflow_state"] = "completed"
                self.active_sessions[session_id]["current_workflow"] = None
            elif interaction_type == "workflow_failed":
                self.active_sessions[session_id]["workflow_state"] = "failed"
                self.active_sessions[session_id]["error_count"] += 1
                self.active_sessions[session_id]["last_error"] = interaction_data.get("error")
            elif interaction_type == "image_generated":
                self.active_sessions[session_id]["total_images_generated"] += interaction_data.get("count", 1)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to add interaction",
                            session_id=session_id,
                            interaction_type=interaction_type,
                            error=str(e))
            return False

    async def start_workflow(self, session_id: str, workflow_id: str, 
                            workflow_type: str, workflow_data: Dict[str, Any]) -> bool:
        """
        Start a new workflow in the session.

        Args:
            session_id: The session ID
            workflow_id: The workflow ID
            workflow_type: Type of workflow
            workflow_data: Workflow-specific data

        Returns:
            True if workflow started successfully
        """
        try:
            # Add workflow start interaction
            await self.add_interaction(session_id, "workflow_started", {
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "workflow_data": workflow_data,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update session workflow state
            await self.update_session(session_id, {
                "current_workflow": workflow_id,
                "workflow_state": "in_progress"
            })
            
            self.logger.info("Workflow started",
                            session_id=session_id,
                            workflow_id=workflow_id,
                            workflow_type=workflow_type)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to start workflow",
                            session_id=session_id,
                            workflow_id=workflow_id,
                            error=str(e))
            return False

    async def complete_workflow(self, session_id: str, workflow_id: str, 
                               result: Dict[str, Any], success: bool = True) -> bool:
        """
        Complete a workflow in the session.

        Args:
            session_id: The session ID
            workflow_id: The workflow ID
            result: Workflow result data
            success: Whether the workflow succeeded

        Returns:
            True if workflow completed successfully
        """
        try:
            interaction_type = "workflow_completed" if success else "workflow_failed"
            interaction_data = {
                "workflow_id": workflow_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            if not success:
                interaction_data["error"] = result.get("error", "Unknown error")
            
            # Add workflow completion interaction
            await self.add_interaction(session_id, interaction_type, interaction_data)
            
            # Update session workflow state
            await self.update_session(session_id, {
                "current_workflow": None,
                "workflow_state": "completed" if success else "failed"
            })
            
            self.logger.info("Workflow completed",
                            session_id=session_id,
                            workflow_id=workflow_id,
                            success=success)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to complete workflow",
                            session_id=session_id,
                            workflow_id=workflow_id,
                            error=str(e))
            return False

    async def close_session(self, session_id: str, reason: str = "user_request") -> bool:
        """
        Close a session.

        Args:
            session_id: The session ID
            reason: Reason for closing the session

        Returns:
            True if closed successfully
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            # Add session close interaction
            await self.add_interaction(session_id, "session_closed", {
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update session status
            self.active_sessions[session_id]["status"] = "closed"
            self.active_sessions[session_id]["last_updated"] = datetime.now().isoformat()
            
            # Move to history (keep in memory for now)
            # In production, this would be persisted to database
            self.logger.info("Session closed",
                            session_id=session_id,
                            reason=reason)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to close session",
                            session_id=session_id,
                            error=str(e))
            return False

    def _get_user_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user."""
        return [
            session for session in self.active_sessions.values()
            if session["user_id"] == user_id and session["status"] == "active"
        ]

    async def get_user_sessions(self, user_id: str, include_closed: bool = True) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user.

        Args:
            user_id: The user ID
            include_closed: Whether to include closed sessions

        Returns:
            List of user sessions
        """
        try:
            sessions = []
            
            # Active sessions
            active_sessions = [
                session for session in self.active_sessions.values()
                if session["user_id"] == user_id
            ]
            sessions.extend(active_sessions)
            
            # Closed sessions from history
            if include_closed:
                for session_id, history in self.session_history.items():
                    if history and history[0].get("user_id") == user_id:
                        session_data = await self._reconstruct_session_from_history(session_id)
                        if session_data:
                            sessions.append(session_data)
            
            # Sort by creation date (newest first)
            sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
            
            return sessions
            
        except Exception as e:
            self.logger.error("Failed to get user sessions",
                            user_id=user_id,
                            error=str(e))
            return []

    async def cleanup_expired_sessions(self) -> Dict[str, Any]:
        """
        Clean up expired sessions.

        Returns:
            Dict containing cleanup results
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.max_session_duration)
            expired_sessions = []
            
            for session_id, session in list(self.active_sessions.items()):
                created_at = datetime.fromisoformat(session["created_at"])
                if created_at < cutoff_time:
                    await self.close_session(session_id, "expired")
                    expired_sessions.append(session_id)
            
            self.logger.info("Session cleanup completed",
                            expired_sessions_count=len(expired_sessions))
            
            return {
                "success": True,
                "expired_sessions_count": len(expired_sessions),
                "expired_sessions": expired_sessions
            }
            
        except Exception as e:
            self.logger.error("Failed to cleanup expired sessions", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get session statistics.

        Returns:
            Dict containing session statistics
        """
        try:
            active_sessions = len([s for s in self.active_sessions.values() if s["status"] == "active"])
            total_sessions = len(self.active_sessions) + len(self.session_history)
            
            # Calculate average session duration
            total_duration = 0
            session_count = 0
            
            for session in self.active_sessions.values():
                if session["status"] == "closed":
                    created_at = datetime.fromisoformat(session["created_at"])
                    last_updated = datetime.fromisoformat(session["last_updated"])
                    duration = (last_updated - created_at).total_seconds() / 3600  # hours
                    total_duration += duration
                    session_count += 1
            
            avg_duration = total_duration / session_count if session_count > 0 else 0
            
            stats = {
                "active_sessions": active_sessions,
                "total_sessions": total_sessions,
                "average_session_duration_hours": round(avg_duration, 2),
                "total_interactions": sum(s.get("interaction_count", 0) for s in self.active_sessions.values()),
                "total_images_generated": sum(s.get("total_images_generated", 0) for s in self.active_sessions.values()),
                "error_rate": sum(s.get("error_count", 0) for s in self.active_sessions.values()) / max(total_sessions, 1)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get session statistics", error=str(e))
            return {"error": str(e)}

    async def export_session_data(self, session_id: str, output_path: str = None) -> str:
        """
        Export session data to JSON file.

        Args:
            session_id: The session ID
            output_path: Optional output path

        Returns:
            Path to the exported file
        """
        try:
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"session_export_{session_id}_{timestamp}.json"
            
            # Get session data
            session_data = await self.get_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # Get session history
            history = self.session_history.get(session_id, [])
            
            export_data = {
                "session": session_data,
                "history": history,
                "export_timestamp": datetime.now().isoformat()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Session data exported",
                            session_id=session_id,
                            output_path=output_path)
            
            return output_path
            
        except Exception as e:
            self.logger.error("Failed to export session data",
                            session_id=session_id,
                            error=str(e))
            raise

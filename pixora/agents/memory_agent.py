"""
Memory Agent for Pixora system.

Manages long-term memory storage, user preferences, and
semantic search capabilities using vector embeddings.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from ..models import UserRequest, EnhancedPrompt, GeneratedImage
from ..utils.logger import get_logger
from ..utils.embeddings import get_embeddings_manager
from ..utils.config import config

logger = get_logger(__name__)


class MemoryAgent:
    """
    Agent responsible for memory management and retrieval.

    Performs:
    - User preference storage and retrieval
    - Prompt history management
    - Semantic search across past interactions
    - Memory cleanup and maintenance
    - Personalization insights
    """

    def __init__(self):
        """Initialize the MemoryAgent."""
        self.logger = logger
        self.config = config
        self.embeddings_manager = get_embeddings_manager()
        self.memory_db = self._initialize_memory_db()

    def _initialize_memory_db(self) -> Dict[str, Any]:
        """Initialize the memory database structure."""
        # For now, use in-memory storage
        # TODO: Implement persistent storage with SQLite/ChromaDB
        return {
            "user_preferences": {},
            "prompt_history": {},
            "image_metadata": {},
            "session_data": {},
            "embeddings_cache": {}
        }

    async def store_user_preference(self, user_id: str, preference_type: str, 
                                   preference_data: Dict[str, Any]) -> bool:
        """
        Store a user preference.

        Args:
            user_id: The user ID
            preference_type: Type of preference (style, subject, quality, etc.)
            preference_data: The preference data

        Returns:
            True if stored successfully
        """
        try:
            if user_id not in self.memory_db["user_preferences"]:
                self.memory_db["user_preferences"][user_id] = {}
            
            if preference_type not in self.memory_db["user_preferences"][user_id]:
                self.memory_db["user_preferences"][user_id][preference_type] = []
            
            # Add timestamp
            preference_data["timestamp"] = datetime.now().isoformat()
            preference_data["id"] = f"pref_{len(self.memory_db['user_preferences'][user_id][preference_type]) + 1}"
            
            self.memory_db["user_preferences"][user_id][preference_type].append(preference_data)
            
            self.logger.info("User preference stored",
                            user_id=user_id,
                            preference_type=preference_type,
                            preference_id=preference_data["id"])
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to store user preference",
                            user_id=user_id,
                            preference_type=preference_type,
                            error=str(e))
            return False

    async def get_user_preferences(self, user_id: str, preference_type: str = None) -> Dict[str, Any]:
        """
        Retrieve user preferences.

        Args:
            user_id: The user ID
            preference_type: Optional specific preference type

        Returns:
            Dict containing user preferences
        """
        try:
            if user_id not in self.memory_db["user_preferences"]:
                return {}
            
            if preference_type:
                return self.memory_db["user_preferences"][user_id].get(preference_type, [])
            else:
                return self.memory_db["user_preferences"][user_id]
                
        except Exception as e:
            self.logger.error("Failed to retrieve user preferences",
                            user_id=user_id,
                            error=str(e))
            return {}

    async def store_prompt_history(self, user_id: str, request: UserRequest, 
                                  enhanced_prompt: EnhancedPrompt, 
                                  generated_images: List[GeneratedImage]) -> bool:
        """
        Store prompt history and generation results.

        Args:
            user_id: The user ID
            request: The original user request
            enhanced_prompt: The enhanced prompt
            generated_images: List of generated images

        Returns:
            True if stored successfully
        """
        try:
            if user_id not in self.memory_db["prompt_history"]:
                self.memory_db["prompt_history"][user_id] = []
            
            # Create history entry
            history_entry = {
                "id": f"hist_{len(self.memory_db['prompt_history'][user_id]) + 1}",
                "timestamp": datetime.now().isoformat(),
                "original_prompt": request.prompt,
                "enhanced_prompt": enhanced_prompt.prompt,
                "style_preferences": enhanced_prompt.style_preferences,
                "generated_count": len(generated_images),
                "workflow_ids": [img.metadata.workflow_id for img in generated_images],
                "session_id": request.session_id
            }
            
            self.memory_db["prompt_history"][user_id].append(history_entry)
            
            # Store image metadata
            for image in generated_images:
                await self._store_image_metadata(image)
            
            self.logger.info("Prompt history stored",
                            user_id=user_id,
                            history_id=history_entry["id"],
                            images_count=len(generated_images))
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to store prompt history",
                            user_id=user_id,
                            error=str(e))
            return False

    async def _store_image_metadata(self, image: GeneratedImage):
        """Store image metadata for future reference."""
        try:
            image_id = image.metadata.workflow_id
            self.memory_db["image_metadata"][image_id] = {
                "user_id": image.metadata.user_id,
                "timestamp": image.metadata.timestamp,
                "prompt": image.metadata.prompt,
                "model": image.metadata.model_used,
                "provider": image.metadata.provider,
                "size": image.metadata.size,
                "style_preferences": image.metadata.style_preferences,
                "cost_estimate": image.metadata.cost_estimate
            }
        except Exception as e:
            self.logger.error("Failed to store image metadata",
                            workflow_id=image.metadata.workflow_id,
                            error=str(e))

    async def search_similar_prompts(self, user_id: str, query: str, 
                                   limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar prompts in user history.

        Args:
            user_id: The user ID
            query: The search query
            limit: Maximum number of results

        Returns:
            List of similar prompts with similarity scores
        """
        try:
            if user_id not in self.memory_db["prompt_history"]:
                return []
            
            # Get query embedding
            query_embedding = await self.embeddings_manager.get_embedding(query)
            
            # Calculate similarities with stored prompts
            similarities = []
            for history_entry in self.memory_db["prompt_history"][user_id]:
                # Get embedding for the enhanced prompt
                prompt_embedding = await self._get_or_create_embedding(
                    history_entry["enhanced_prompt"], 
                    f"hist_{history_entry['id']}"
                )
                
                # Calculate cosine similarity
                similarity = self._calculate_cosine_similarity(query_embedding, prompt_embedding)
                
                similarities.append({
                    "history_entry": history_entry,
                    "similarity_score": similarity
                })
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            self.logger.error("Failed to search similar prompts",
                            user_id=user_id,
                            query=query,
                            error=str(e))
            return []

    async def _get_or_create_embedding(self, text: str, text_id: str) -> List[float]:
        """Get existing embedding or create new one."""
        if text_id in self.memory_db["embeddings_cache"]:
            return self.memory_db["embeddings_cache"][text_id]
        
        # Create new embedding
        embedding = await self.embeddings_manager.get_embedding(text)
        self.memory_db["embeddings_cache"][text_id] = embedding
        return embedding

    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            import numpy as np
            
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except ImportError:
            # Fallback to simple calculation if numpy not available
            if len(vec1) != len(vec2):
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(a * a for a in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)

    async def get_personalization_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get personalization insights for a user.

        Args:
            user_id: The user ID

        Returns:
            Dict containing personalization insights
        """
        try:
            insights = {
                "user_id": user_id,
                "total_generations": 0,
                "favorite_styles": {},
                "common_subjects": {},
                "generation_patterns": {},
                "quality_preferences": {}
            }
            
            if user_id not in self.memory_db["prompt_history"]:
                return insights
            
            history = self.memory_db["prompt_history"][user_id]
            insights["total_generations"] = len(history)
            
            # Analyze style preferences
            for entry in history:
                if "style_preferences" in entry and entry["style_preferences"]:
                    for style, value in entry["style_preferences"].items():
                        if style not in insights["favorite_styles"]:
                            insights["favorite_styles"][style] = 0
                        insights["favorite_styles"][style] += 1
            
            # Analyze common subjects (simple keyword extraction)
            for entry in history:
                prompt_words = entry["original_prompt"].lower().split()
                for word in prompt_words:
                    if len(word) > 3:  # Filter short words
                        if word not in insights["common_subjects"]:
                            insights["common_subjects"][word] = 0
                        insights["common_subjects"][word] += 1
            
            # Sort by frequency
            insights["favorite_styles"] = dict(
                sorted(insights["favorite_styles"].items(), 
                       key=lambda x: x[1], reverse=True)[:5]
            )
            insights["common_subjects"] = dict(
                sorted(insights["common_subjects"].items(), 
                       key=lambda x: x[1], reverse=True)[:10]
            )
            
            return insights
            
        except Exception as e:
            self.logger.error("Failed to get personalization insights",
                            user_id=user_id,
                            error=str(e))
            return {"user_id": user_id, "error": str(e)}

    async def store_session_data(self, session_id: str, user_id: str, 
                                session_data: Dict[str, Any]) -> bool:
        """
        Store session-specific data.

        Args:
            session_id: The session ID
            user_id: The user ID
            session_data: The session data to store

        Returns:
            True if stored successfully
        """
        try:
            if session_id not in self.memory_db["session_data"]:
                self.memory_db["session_data"][session_id] = {}
            
            self.memory_db["session_data"][session_id].update({
                "user_id": user_id,
                "last_updated": datetime.now().isoformat(),
                **session_data
            })
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to store session data",
                            session_id=session_id,
                            error=str(e))
            return False

    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data.

        Args:
            session_id: The session ID

        Returns:
            Session data or None if not found
        """
        try:
            return self.memory_db["session_data"].get(session_id)
        except Exception as e:
            self.logger.error("Failed to retrieve session data",
                            session_id=session_id,
                            error=str(e))
            return None

    async def cleanup_old_memory(self, days_old: int = 30) -> Dict[str, Any]:
        """
        Clean up old memory entries.

        Args:
            days_old: Remove entries older than this many days

        Returns:
            Dict containing cleanup results
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleaned_count = 0
            
            # Clean up old prompt history
            for user_id in list(self.memory_db["prompt_history"].keys()):
                original_count = len(self.memory_db["prompt_history"][user_id])
                self.memory_db["prompt_history"][user_id] = [
                    entry for entry in self.memory_db["prompt_history"][user_id]
                    if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
                ]
                cleaned_count += original_count - len(self.memory_db["prompt_history"][user_id])
                
                # Remove user if no history left
                if not self.memory_db["prompt_history"][user_id]:
                    del self.memory_db["prompt_history"][user_id]
            
            # Clean up old session data
            for session_id in list(self.memory_db["session_data"].keys()):
                session = self.memory_db["session_data"][session_id]
                if "last_updated" in session:
                    last_updated = datetime.fromisoformat(session["last_updated"])
                    if last_updated < cutoff_date:
                        del self.memory_db["session_data"][session_id]
                        cleaned_count += 1
            
            self.logger.info("Memory cleanup completed",
                            entries_removed=cleaned_count)
            
            return {
                "success": True,
                "entries_removed": cleaned_count
            }
            
        except Exception as e:
            self.logger.error("Failed to cleanup old memory", error=str(e))
            return {"success": False, "error": str(e)}

    async def export_memory(self, user_id: str = None, output_path: str = None) -> str:
        """
        Export memory data to JSON file.

        Args:
            user_id: Optional specific user ID to export
            output_path: Optional output path

        Returns:
            Path to the exported file
        """
        try:
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"memory_export_{timestamp}.json"
            
            export_data = {}
            
            if user_id:
                # Export specific user data
                export_data = {
                    "user_id": user_id,
                    "preferences": self.memory_db["user_preferences"].get(user_id, {}),
                    "prompt_history": self.memory_db["prompt_history"].get(user_id, []),
                    "personalization_insights": await self.get_personalization_insights(user_id)
                }
            else:
                # Export all data
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "user_preferences": self.memory_db["user_preferences"],
                    "prompt_history": self.memory_db["prompt_history"],
                    "image_metadata": self.memory_db["image_metadata"],
                    "session_data": self.memory_db["session_data"]
                }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Memory export completed",
                            output_path=output_path,
                            user_id=user_id)
            
            return output_path
            
        except Exception as e:
            self.logger.error("Failed to export memory", error=str(e))
            raise

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.

        Returns:
            Dict containing memory statistics
        """
        try:
            stats = {
                "total_users": len(self.memory_db["user_preferences"]),
                "total_prompt_entries": sum(len(history) for history in self.memory_db["prompt_history"].values()),
                "total_images": len(self.memory_db["image_metadata"]),
                "active_sessions": len(self.memory_db["session_data"]),
                "cached_embeddings": len(self.memory_db["embeddings_cache"])
            }
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get memory statistics", error=str(e))
            return {"error": str(e)}

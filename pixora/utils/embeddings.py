"""
Embeddings management for Pixora system.

Handles text embeddings, vector storage, and similarity search
for user preferences and memory management.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import pickle
from datetime import datetime, timedelta
import chromadb
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .config import config
from .logger import get_logger, log_error, log_performance_metric


class EmbeddingManager:
    """Manages text embeddings and vector operations for Pixora."""
    
    def __init__(self, model_name: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.model_name = model_name or config.embedding_model
        
        # Initialize the embedding model
        try:
            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"Embedding model loaded: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            raise
        
        # Initialize vector database
        self._setup_vector_db()
    
    def _setup_vector_db(self):
        """Set up the vector database for storing embeddings."""
        try:
            db_path = Path(config.memory_db_path) / "embeddings"
            db_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB
            self.chroma_client = chromadb.PersistentClient(path=str(db_path))
            
            # Create or get collections
            self.prompts_collection = self.chroma_client.get_or_create_collection(
                name="prompts",
                metadata={"description": "User prompt embeddings"}
            )
            
            self.preferences_collection = self.chroma_client.get_or_create_collection(
                name="preferences",
                metadata={"description": "User preference embeddings"}
            )
            
            self.logger.info("Vector database initialized successfully")
            
        except Exception as e:
            log_error(e, context={"action": "setup_vector_db"})
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array containing the embedding vector
        """
        try:
            embedding = self.model.encode(text)
            return embedding
            
        except Exception as e:
            log_error(e, context={"action": "generate_embedding", "text_length": len(text)})
            raise
    
    def store_prompt_embedding(
        self,
        prompt: str,
        user_id: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a prompt embedding in the vector database.
        
        Args:
            prompt: The text prompt
            user_id: ID of the user
            session_id: ID of the session
            metadata: Additional metadata to store
            
        Returns:
            ID of the stored embedding
        """
        try:
            # Generate embedding
            embedding = self.generate_embedding(prompt)
            
            # Prepare metadata
            prompt_metadata = {
                "user_id": user_id,
                "session_id": session_id,
                "prompt": prompt,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "prompt"
            }
            
            if metadata:
                prompt_metadata.update(metadata)
            
            # Store in ChromaDB
            result = self.prompts_collection.add(
                embeddings=[embedding.tolist()],
                documents=[prompt],
                metadatas=[prompt_metadata],
                ids=[f"prompt_{user_id}_{session_id}_{datetime.utcnow().timestamp()}"]
            )
            
            embedding_id = result[0]
            self.logger.info(f"Prompt embedding stored: {embedding_id}")
            
            return embedding_id
            
        except Exception as e:
            log_error(e, context={
                "action": "store_prompt_embedding",
                "user_id": user_id,
                "session_id": session_id
            })
            raise
    
    def store_preference_embedding(
        self,
        preference_text: str,
        user_id: str,
        preference_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a user preference embedding.
        
        Args:
            preference_text: Text describing the preference
            user_id: ID of the user
            preference_type: Type of preference (style, category, lighting, etc.)
            metadata: Additional metadata
            
        Returns:
            ID of the stored embedding
        """
        try:
            # Generate embedding
            embedding = self.generate_embedding(preference_text)
            
            # Prepare metadata
            pref_metadata = {
                "user_id": user_id,
                "preference_type": preference_type,
                "text": preference_text,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "preference"
            }
            
            if metadata:
                pref_metadata.update(metadata)
            
            # Store in ChromaDB
            result = self.preferences_collection.add(
                embeddings=[embedding.tolist()],
                documents=[preference_text],
                metadatas=[pref_metadata],
                ids=[f"pref_{user_id}_{preference_type}_{datetime.utcnow().timestamp()}"]
            )
            
            embedding_id = result[0]
            self.logger.info(f"Preference embedding stored: {embedding_id}")
            
            return embedding_id
            
        except Exception as e:
            log_error(e, context={
                "action": "store_preference_embedding",
                "user_id": user_id,
                "preference_type": preference_type
            })
            raise
    
    def find_similar_prompts(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find prompts similar to the query text.
        
        Args:
            query_text: Text to find similar prompts for
            user_id: Optional user ID to filter results
            limit: Maximum number of results to return
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of similar prompts with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query_text)
            
            # Prepare query
            query_metadata = {}
            if user_id:
                query_metadata["user_id"] = user_id
            
            # Search in ChromaDB
            results = self.prompts_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=limit,
                where=query_metadata if query_metadata else None
            )
            
            # Process results
            similar_prompts = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Convert distance to similarity score
                similarity = 1 - distance
                
                if similarity >= threshold:
                    similar_prompts.append({
                        "prompt": doc,
                        "metadata": metadata,
                        "similarity": similarity,
                        "distance": distance
                    })
            
            # Sort by similarity
            similar_prompts.sort(key=lambda x: x["similarity"], reverse=True)
            
            self.logger.info(f"Found {len(similar_prompts)} similar prompts")
            return similar_prompts
            
        except Exception as e:
            log_error(e, context={"action": "find_similar_prompts"})
            return []
    
    def find_user_preferences(
        self,
        query_text: str,
        user_id: str,
        preference_type: Optional[str] = None,
        limit: int = 5,
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Find user preferences similar to the query text.
        
        Args:
            query_text: Text to find preferences for
            user_id: ID of the user
            preference_type: Optional preference type filter
            limit: Maximum number of results
            threshold: Similarity threshold
            
        Returns:
            List of similar preferences
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query_text)
            
            # Prepare query
            query_metadata = {"user_id": user_id}
            if preference_type:
                query_metadata["preference_type"] = preference_type
            
            # Search in ChromaDB
            results = self.preferences_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=limit,
                where=query_metadata
            )
            
            # Process results
            preferences = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                similarity = 1 - distance
                
                if similarity >= threshold:
                    preferences.append({
                        "text": doc,
                        "metadata": metadata,
                        "similarity": similarity,
                        "distance": distance
                    })
            
            # Sort by similarity
            preferences.sort(key=lambda x: x["similarity"], reverse=True)
            
            self.logger.info(f"Found {len(preferences)} user preferences")
            return preferences
            
        except Exception as e:
            log_error(e, context={"action": "find_user_preferences", "user_id": user_id})
            return []
    
    def get_user_preference_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of user preferences based on stored embeddings.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Summary of user preferences
        """
        try:
            # Get all user preferences
            results = self.preferences_collection.get(
                where={"user_id": user_id}
            )
            
            if not results['metadatas']:
                return {"user_id": user_id, "preferences": {}}
            
            # Group by preference type
            preferences_by_type = {}
            for metadata in results['metadatas']:
                pref_type = metadata.get('preference_type', 'unknown')
                if pref_type not in preferences_by_type:
                    preferences_by_type[pref_type] = []
                
                preferences_by_type[pref_type].append({
                    "text": metadata.get('text', ''),
                    "timestamp": metadata.get('timestamp', ''),
                    "metadata": metadata
                })
            
            # Generate summary
            summary = {
                "user_id": user_id,
                "total_preferences": len(results['metadatas']),
                "preferences_by_type": preferences_by_type,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return summary
            
        except Exception as e:
            log_error(e, context={"action": "get_user_preference_summary", "user_id": user_id})
            return {"user_id": user_id, "preferences": {}, "error": str(e)}
    
    def update_embedding_metadata(
        self,
        collection_name: str,
        embedding_id: str,
        new_metadata: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for an existing embedding.
        
        Args:
            collection_name: Name of the collection ('prompts' or 'preferences')
            embedding_id: ID of the embedding to update
            new_metadata: New metadata to set
            
        Returns:
            True if update was successful
        """
        try:
            collection = getattr(self, f"{collection_name}_collection")
            
            # Get existing metadata
            existing = collection.get(ids=[embedding_id])
            if not existing['metadatas']:
                return False
            
            # Merge with new metadata
            updated_metadata = existing['metadatas'][0].copy()
            updated_metadata.update(new_metadata)
            updated_metadata["updated_at"] = datetime.utcnow().isoformat()
            
            # Update in ChromaDB
            collection.update(
                ids=[embedding_id],
                metadatas=[updated_metadata]
            )
            
            self.logger.info(f"Updated metadata for {collection_name} embedding: {embedding_id}")
            return True
            
        except Exception as e:
            log_error(e, context={
                "action": "update_embedding_metadata",
                "collection": collection_name,
                "embedding_id": embedding_id
            })
            return False
    
    def delete_user_embeddings(self, user_id: str) -> bool:
        """
        Delete all embeddings for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if deletion was successful
        """
        try:
            # Delete from prompts collection
            self.prompts_collection.delete(
                where={"user_id": user_id}
            )
            
            # Delete from preferences collection
            self.preferences_collection.delete(
                where={"user_id": user_id}
            )
            
            self.logger.info(f"Deleted all embeddings for user: {user_id}")
            return True
            
        except Exception as e:
            log_error(e, context={"action": "delete_user_embeddings", "user_id": user_id})
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            prompts_count = self.prompts_collection.count()
            preferences_count = self.preferences_collection.count()
            
            stats = {
                "total_prompts": prompts_count,
                "total_preferences": preferences_count,
                "total_embeddings": prompts_count + preferences_count,
                "model_name": self.model_name,
                "embedding_dimensions": self.model.get_sentence_embedding_dimension(),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            log_error(e, context={"action": "get_database_stats"})
            return {"error": str(e)}
    
    def cleanup_old_embeddings(self, days_old: int = 30) -> int:
        """
        Clean up old embeddings based on age.
        
        Args:
            days_old: Age threshold in days
            
        Returns:
            Number of embeddings deleted
        """
        try:
            cutoff_date = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=days_old)
            
            cutoff_iso = cutoff_date.isoformat()
            
            # Find old embeddings
            old_prompts = self.prompts_collection.get(
                where={"timestamp": {"$lt": cutoff_iso}}
            )
            
            old_preferences = self.preferences_collection.get(
                where={"timestamp": {"$lt": cutoff_iso}}
            )
            
            # Delete old embeddings
            deleted_count = 0
            
            if old_prompts['ids']:
                self.prompts_collection.delete(ids=old_prompts['ids'])
                deleted_count += len(old_prompts['ids'])
            
            if old_preferences['ids']:
                self.preferences_collection.delete(ids=old_preferences['ids'])
                deleted_count += len(old_preferences['ids'])
            
            self.logger.info(f"Cleaned up {deleted_count} old embeddings")
            return deleted_count
            
        except Exception as e:
            log_error(e, context={"action": "cleanup_old_embeddings"})
            return 0


# Global embeddings manager instance
_embeddings_manager = None


def get_embeddings_manager(model_name: Optional[str] = None) -> EmbeddingManager:
    """
    Get or create a global embeddings manager instance.
    
    Args:
        model_name: Optional model name to use
        
    Returns:
        EmbeddingManager instance
    """
    global _embeddings_manager
    
    if _embeddings_manager is None:
        _embeddings_manager = EmbeddingManager(model_name)
    
    return _embeddings_manager

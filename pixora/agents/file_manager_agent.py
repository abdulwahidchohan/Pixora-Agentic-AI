"""
File Manager Agent for Pixora system.

Handles file operations including saving generated images,
managing metadata sidecar files, and organizing storage structure.
"""

import json
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from ..models import GeneratedImage, ImageMetadata
from ..utils.logger import get_logger
from ..utils.config import config

logger = get_logger(__name__)


class FileManagerAgent:
    """
    Agent responsible for file management and storage operations.

    Performs:
    - Image file saving
    - Metadata sidecar file creation
    - Storage organization and categorization
    - File naming conventions
    - Storage cleanup and maintenance
    """

    def __init__(self):
        """Initialize the FileManagerAgent."""
        self.logger = logger
        self.config = config
        self.base_storage_path = self._get_storage_path()
        self._ensure_storage_structure()

    def _get_storage_path(self) -> Path:
        """Get the base storage path for images."""
        if hasattr(self.config, 'storage_path') and self.config.storage_path:
            storage_path = Path(self.config.storage_path)
        else:
            # Default to Desktop/Pixora
            storage_path = Path.home() / "Desktop" / "Pixora"
        
        return storage_path

    def _ensure_storage_structure(self):
        """Ensure the storage directory structure exists."""
        try:
            # Create base directory
            self.base_storage_path.mkdir(parents=True, exist_ok=True)
            
            # Create category subdirectories
            categories = ["Products", "Portraits", "Landscapes", "Abstract", "Architecture", "Wildlife", "General"]
            for category in categories:
                category_path = self.base_storage_path / category
                category_path.mkdir(exist_ok=True)
                
            self.logger.info("Storage structure ensured", base_path=str(self.base_storage_path))
            
        except Exception as e:
            self.logger.error("Failed to create storage structure", error=str(e))
            raise

    async def save_image(self, image: GeneratedImage, category: str = None) -> Dict[str, Any]:
        """
        Save a generated image and its metadata.

        Args:
            image: The generated image to save
            category: Optional category override

        Returns:
            Dict containing save results and file paths
        """
        try:
            # Determine category
            if not category:
                category = await self._determine_category(image)
            
            # Create filename
            filename = self._generate_filename(image, category)
            
            # Ensure category directory exists
            category_path = self.base_storage_path / category
            category_path.mkdir(exist_ok=True)
            
            # Save image file
            image_path = category_path / f"{filename}.png"
            with open(image_path, 'wb') as f:
                f.write(image.image_data)
            
            # Save metadata sidecar
            metadata_path = category_path / f"{filename}.json"
            metadata_content = self._prepare_metadata(image, category, str(image_path))
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_content, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Image saved successfully",
                            workflow_id=image.metadata.workflow_id,
                            image_path=str(image_path),
                            metadata_path=str(metadata_path))
            
            return {
                "success": True,
                "image_path": str(image_path),
                "metadata_path": str(metadata_path),
                "category": category,
                "filename": filename
            }
            
        except Exception as e:
            self.logger.error("Failed to save image",
                            workflow_id=image.metadata.workflow_id,
                            error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def save_multiple_images(self, images: List[GeneratedImage], category: str = None) -> List[Dict[str, Any]]:
        """
        Save multiple generated images.

        Args:
            images: List of generated images to save
            category: Optional category override for all images

        Returns:
            List of save results for each image
        """
        self.logger.info("Saving multiple images", count=len(images))
        
        results = []
        for i, image in enumerate(images):
            try:
                # Use sequential numbering for multiple images
                image.metadata.workflow_id = f"{image.metadata.workflow_id}_{i+1:02d}"
                result = await self.save_image(image, category)
                results.append(result)
            except Exception as e:
                self.logger.error("Failed to save image in batch",
                                index=i,
                                workflow_id=image.metadata.workflow_id,
                                error=str(e))
                results.append({
                    "success": False,
                    "error": str(e),
                    "index": i
                })
        
        return results

    async def _determine_category(self, image: GeneratedImage) -> str:
        """
        Determine the appropriate category for an image.

        Args:
            image: The generated image

        Returns:
            Category string
        """
        # Try to extract category from metadata or prompt
        prompt = image.metadata.prompt.lower()
        
        # Simple keyword-based categorization
        if any(word in prompt for word in ["portrait", "person", "face", "human", "people"]):
            return "Portraits"
        elif any(word in prompt for word in ["landscape", "nature", "mountain", "forest", "beach"]):
            return "Landscapes"
        elif any(word in prompt for word in ["building", "architecture", "city", "urban", "house"]):
            return "Architecture"
        elif any(word in prompt for word in ["animal", "pet", "wildlife", "creature", "bird"]):
            return "Wildlife"
        elif any(word in prompt for word in ["product", "object", "item", "thing", "tool"]):
            return "Products"
        elif any(word in prompt for word in ["abstract", "pattern", "design", "art", "geometric"]):
            return "Abstract"
        else:
            return "General"

    def _generate_filename(self, image: GeneratedImage, category: str) -> str:
        """
        Generate a filename for the image.

        Args:
            image: The generated image
            category: The category

        Returns:
            Generated filename (without extension)
        """
        # Get timestamp
        timestamp = image.metadata.timestamp
        if isinstance(timestamp, str):
            date_str = timestamp.split('T')[0]  # Extract date part
        else:
            date_str = timestamp.strftime('%Y-%m-%d')
        
        # Create descriptive part from prompt
        prompt_words = image.metadata.prompt.split()[:3]  # First 3 words
        descriptive_part = "_".join(word.lower() for word in prompt_words if len(word) > 2)
        
        # Clean descriptive part
        import re
        descriptive_part = re.sub(r'[^a-zA-Z0-9_]', '', descriptive_part)
        
        # Generate unique identifier
        unique_id = image.metadata.workflow_id.split('_')[-1] if '_' in image.metadata.workflow_id else '001'
        
        filename = f"{date_str}_{descriptive_part}_{unique_id}"
        return filename

    def _prepare_metadata(self, image: GeneratedImage, category: str, image_path: str) -> Dict[str, Any]:
        """
        Prepare metadata for saving as sidecar file.

        Args:
            image: The generated image
            category: The category
            image_path: Path to the saved image

        Returns:
            Metadata dictionary
        """
        return {
            "workflow_id": image.metadata.workflow_id,
            "user_id": image.metadata.user_id,
            "timestamp": image.metadata.timestamp.isoformat() if hasattr(image.metadata.timestamp, 'isoformat') else str(image.metadata.timestamp),
            "model_used": image.metadata.model_used,
            "size": image.metadata.size,
            "prompt": image.metadata.prompt,
            "style_preferences": image.metadata.style_preferences,
            "provider": image.metadata.provider,
            "cost_estimate": image.metadata.cost_estimate,
            "category": category,
            "image_path": image_path,
            "format": image.format,
            "file_size_bytes": len(image.image_data),
            "generated_at": datetime.now().isoformat(),
            "pixora_version": "1.0.0"
        }

    async def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about storage usage and structure.

        Returns:
            Dict containing storage information
        """
        try:
            storage_info = {
                "base_path": str(self.base_storage_path),
                "total_size_bytes": 0,
                "category_counts": {},
                "total_files": 0
            }
            
            # Calculate sizes and counts
            for category_dir in self.base_storage_path.iterdir():
                if category_dir.is_dir():
                    category_name = category_dir.name
                    category_size = 0
                    file_count = 0
                    
                    for file_path in category_dir.iterdir():
                        if file_path.is_file():
                            if file_path.suffix == '.png':
                                file_count += 1
                                category_size += file_path.stat().st_size
                    
                    storage_info["category_counts"][category_name] = {
                        "file_count": file_count,
                        "size_bytes": category_size
                    }
                    storage_info["total_files"] += file_count
                    storage_info["total_size_bytes"] += category_size
            
            return storage_info
            
        except Exception as e:
            self.logger.error("Failed to get storage info", error=str(e))
            return {"error": str(e)}

    async def cleanup_old_files(self, days_old: int = 30) -> Dict[str, Any]:
        """
        Clean up old files based on age.

        Args:
            days_old: Remove files older than this many days

        Returns:
            Dict containing cleanup results
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            cleaned_files = []
            total_size_freed = 0
            
            for category_dir in self.base_storage_path.iterdir():
                if category_dir.is_dir():
                    for file_path in category_dir.iterdir():
                        if file_path.is_file() and file_path.suffix == '.png':
                            # Check file modification time
                            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_mtime < cutoff_date:
                                # Remove image and metadata files
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                
                                # Try to remove metadata file
                                metadata_path = file_path.with_suffix('.json')
                                if metadata_path.exists():
                                    metadata_path.unlink()
                                
                                cleaned_files.append(str(file_path))
                                total_size_freed += file_size
            
            self.logger.info("Cleanup completed",
                            files_removed=len(cleaned_files),
                            size_freed_bytes=total_size_freed)
            
            return {
                "success": True,
                "files_removed": len(cleaned_files),
                "size_freed_bytes": total_size_freed,
                "removed_files": cleaned_files
            }
            
        except Exception as e:
            self.logger.error("Failed to cleanup old files", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_image_by_workflow_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve image information by workflow ID.

        Args:
            workflow_id: The workflow ID to search for

        Returns:
            Dict containing image information or None if not found
        """
        try:
            for category_dir in self.base_storage_path.iterdir():
                if category_dir.is_dir():
                    for file_path in category_dir.iterdir():
                        if file_path.suffix == '.json':
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                
                                if metadata.get('workflow_id') == workflow_id:
                                    # Find corresponding image file
                                    image_path = file_path.with_suffix('.png')
                                    if image_path.exists():
                                        return {
                                            "metadata": metadata,
                                            "image_path": str(image_path),
                                            "metadata_path": str(file_path),
                                            "category": category_dir.name
                                        }
                            except (json.JSONDecodeError, IOError):
                                continue
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to search for image by workflow ID",
                            workflow_id=workflow_id,
                            error=str(e))
            return None

    async def export_metadata(self, output_path: str = None) -> str:
        """
        Export all metadata to a single JSON file.

        Args:
            output_path: Optional output path, defaults to storage base directory

        Returns:
            Path to the exported file
        """
        try:
            if not output_path:
                output_path = self.base_storage_path / f"metadata_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            all_metadata = []
            
            for category_dir in self.base_storage_path.iterdir():
                if category_dir.is_dir():
                    for file_path in category_dir.iterdir():
                        if file_path.suffix == '.json':
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                    metadata['_source_file'] = str(file_path)
                                    metadata['_category'] = category_dir.name
                                    all_metadata.append(metadata)
                            except (json.JSONDecodeError, IOError):
                                continue
            
            # Save export
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Metadata export completed",
                            output_path=str(output_path),
                            records_exported=len(all_metadata))
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error("Failed to export metadata", error=str(e))
            raise

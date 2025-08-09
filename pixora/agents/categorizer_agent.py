"""
Categorizer Agent for Pixora system.

Implements intelligent categorization and tagging of images and prompts
for better organization and searchability.
"""

import re
from typing import List, Dict, Any, Optional
from ..models import GeneratedImage, ImageMetadata
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CategorizerAgent:
    """
    Agent responsible for categorizing and tagging images and prompts.

    Performs:
    - Content categorization
    - Style classification
    - Tag generation
    - Metadata enrichment
    """

    def __init__(self):
        """Initialize the CategorizerAgent."""
        self.logger = logger
        self.categories = self._load_categories()
        self.style_patterns = self._load_style_patterns()

    def _load_categories(self) -> Dict[str, List[str]]:
        """Load predefined content categories."""
        return {
            "art_style": [
                "realistic", "abstract", "cartoon", "anime", "photorealistic",
                "impressionist", "surreal", "minimalist", "vintage", "modern"
            ],
            "subject_matter": [
                "portrait", "landscape", "still_life", "architecture", "nature",
                "urban", "fantasy", "sci_fi", "historical", "contemporary"
            ],
            "mood": [
                "serene", "dramatic", "mysterious", "joyful", "melancholic",
                "energetic", "peaceful", "intense", "whimsical", "elegant"
            ],
            "color_scheme": [
                "warm", "cool", "monochrome", "vibrant", "pastel",
                "earthy", "neon", "muted", "contrasting", "harmonious"
            ]
        }

    def _load_style_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for style detection."""
        return {
            "photography": ["photo", "photograph", "camera", "lens", "aperture"],
            "painting": ["oil painting", "watercolor", "acrylic", "canvas", "brush"],
            "digital_art": ["digital art", "digital painting", "photoshop", "procreate"],
            "illustration": ["illustration", "drawing", "sketch", "line art"],
            "3d": ["3d", "three dimensional", "rendered", "blender", "maya"],
            "minimalist": ["minimal", "simple", "clean", "sparse", "minimalist"]
        }

    async def categorize_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Categorize a text prompt.

        Args:
            prompt: The prompt text to categorize

        Returns:
            Dict containing categorization results
        """
        self.logger.info("Categorizing prompt", prompt_length=len(prompt))

        prompt_lower = prompt.lower()
        categorization = {
            "primary_category": None,
            "secondary_categories": [],
            "detected_styles": [],
            "tags": [],
            "confidence_scores": {}
        }

        # Detect primary category
        primary_category = self._detect_primary_category(prompt_lower)
        categorization["primary_category"] = primary_category

        # Detect secondary categories
        secondary_cats = self._detect_secondary_categories(prompt_lower, primary_category)
        categorization["secondary_categories"] = secondary_cats

        # Detect styles
        detected_styles = self._detect_styles(prompt_lower)
        categorization["detected_styles"] = detected_styles

        # Generate tags
        tags = self._generate_tags(prompt_lower, primary_category, detected_styles)
        categorization["tags"] = tags

        # Calculate confidence scores
        confidence_scores = self._calculate_confidence_scores(prompt_lower, categorization)
        categorization["confidence_scores"] = confidence_scores

        self.logger.info("Prompt categorization completed",
                        primary_category=primary_category,
                        tags_count=len(tags))

        return categorization

    async def categorize_image(self, image: GeneratedImage) -> Dict[str, Any]:
        """
        Categorize a generated image.

        Args:
            image: The generated image to categorize

        Returns:
            Dict containing image categorization results
        """
        self.logger.info("Categorizing generated image", workflow_id=image.metadata.workflow_id)

        # Extract information from metadata
        prompt = image.metadata.prompt
        style_preferences = image.metadata.style_preferences

        # Categorize the prompt
        prompt_categorization = await self.categorize_prompt(prompt)

        # Analyze image characteristics (placeholder for now)
        image_analysis = self._analyze_image_characteristics(image)

        # Combine results
        image_categorization = {
            "prompt_categorization": prompt_categorization,
            "image_analysis": image_analysis,
            "metadata_enrichment": self._enrich_metadata(image.metadata, prompt_categorization),
            "search_keywords": self._generate_search_keywords(prompt_categorization, image_analysis)
        }

        self.logger.info("Image categorization completed",
                        workflow_id=image.metadata.workflow_id)

        return image_categorization

    def _detect_primary_category(self, prompt: str) -> str:
        """Detect the primary category of a prompt."""
        # Simple keyword-based detection
        if any(word in prompt for word in ["portrait", "person", "face", "human"]):
            return "portrait"
        elif any(word in prompt for word in ["landscape", "nature", "mountain", "forest"]):
            return "landscape"
        elif any(word in prompt for word in ["building", "architecture", "city", "urban"]):
            return "architecture"
        elif any(word in prompt for word in ["animal", "pet", "wildlife", "creature"]):
            return "wildlife"
        elif any(word in prompt for word in ["abstract", "pattern", "design", "art"]):
            return "abstract"
        else:
            return "general"

    def _detect_secondary_categories(self, prompt: str, primary: str) -> List[str]:
        """Detect secondary categories."""
        secondary = []
        
        # Add categories based on content
        if "color" in prompt or "bright" in prompt or "dark" in prompt:
            secondary.append("color_focus")
        
        if "texture" in prompt or "rough" in prompt or "smooth" in prompt:
            secondary.append("texture_focus")
            
        if "lighting" in prompt or "shadow" in prompt or "sunset" in prompt:
            secondary.append("lighting_focus")
            
        # Avoid duplicates
        if primary in secondary:
            secondary.remove(primary)
            
        return secondary[:3]  # Limit to 3 secondary categories

    def _detect_styles(self, prompt: str) -> List[str]:
        """Detect artistic styles in the prompt."""
        detected_styles = []
        
        for style_name, patterns in self.style_patterns.items():
            if any(pattern in prompt for pattern in patterns):
                detected_styles.append(style_name)
                
        return detected_styles

    def _generate_tags(self, prompt: str, primary_category: str, styles: List[str]) -> List[str]:
        """Generate tags for the prompt."""
        tags = [primary_category]
        tags.extend(styles)
        
        # Extract additional keywords
        words = re.findall(r'\b\w+\b', prompt.lower())
        # Filter out common words and add unique ones
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        unique_words = [word for word in words if word not in common_words and len(word) > 3]
        
        # Add unique words as tags (limit to 5)
        tags.extend(unique_words[:5])
        
        return list(set(tags))  # Remove duplicates

    def _calculate_confidence_scores(self, prompt: str, categorization: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores for categorization."""
        scores = {}
        
        # Calculate confidence based on keyword presence
        prompt_lower = prompt.lower()
        
        # Primary category confidence
        primary = categorization["primary_category"]
        if primary == "portrait" and any(word in prompt_lower for word in ["portrait", "person", "face"]):
            scores["primary_category"] = 0.9
        elif primary == "landscape" and any(word in prompt_lower for word in ["landscape", "nature", "mountain"]):
            scores["primary_category"] = 0.9
        else:
            scores["primary_category"] = 0.7
            
        # Style detection confidence
        detected_styles = categorization["detected_styles"]
        if detected_styles:
            scores["style_detection"] = 0.8
        else:
            scores["style_detection"] = 0.5
            
        # Overall confidence
        scores["overall"] = sum(scores.values()) / len(scores)
        
        return scores

    def _analyze_image_characteristics(self, image: GeneratedImage) -> Dict[str, Any]:
        """Analyze characteristics of a generated image."""
        # Placeholder implementation
        # TODO: Implement actual image analysis using computer vision
        return {
            "estimated_colors": ["#f0f0f0", "#333333"],  # Placeholder
            "composition": "centered",
            "complexity": "medium",
            "texture": "smooth"
        }

    def _enrich_metadata(self, metadata: ImageMetadata, categorization: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich image metadata with categorization results."""
        return {
            "categories": categorization["primary_category"],
            "tags": categorization["tags"],
            "styles": categorization["detected_styles"],
            "confidence": categorization["confidence_scores"]["overall"]
        }

    def _generate_search_keywords(self, categorization: Dict[str, Any], image_analysis: Dict[str, Any]) -> List[str]:
        """Generate search keywords for the image."""
        keywords = []
        
        # Add primary category
        if categorization["primary_category"]:
            keywords.append(categorization["primary_category"])
            
        # Add detected styles
        keywords.extend(categorization["detected_styles"])
        
        # Add tags
        keywords.extend(categorization["tags"][:5])  # Limit to 5 tags
        
        return list(set(keywords))  # Remove duplicates

    async def get_category_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about categorization usage.

        Returns:
            Dict containing categorization statistics
        """
        # Placeholder implementation
        # TODO: Implement actual statistics tracking
        return {
            "total_categorized": 0,
            "category_distribution": {},
            "style_distribution": {},
            "average_confidence": 0.0
        }

    async def update_categories(self, new_categories: Dict[str, List[str]]) -> bool:
        """
        Update the available categories.

        Args:
            new_categories: New categories to add

        Returns:
            True if update was successful
        """
        try:
            for category, items in new_categories.items():
                if category in self.categories:
                    self.categories[category].extend(items)
                else:
                    self.categories[category] = items
                    
            self.logger.info("Categories updated", new_categories=list(new_categories.keys()))
            return True
            
        except Exception as e:
            self.logger.error("Failed to update categories", error=str(e))
            return False

"""
Prompt Enhancer Agent for Pixora.

Enhances user prompts by adding detail, style information,
and incorporating user preferences from memory.
"""

import openai
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from ..models import (
    PromptEnhancementRequest,
    PromptEnhancementResult,
    ImageStyle,
    ImageCategory
)
from ..utils.config import config
from ..utils.logger import get_logger, log_function_call, log_function_result
from ..utils.embeddings import EmbeddingManager


class PromptEnhancer:
    """Enhances user prompts using AI and user preferences."""
    
    def __init__(self, embedding_manager: Optional[EmbeddingManager] = None):
        self.logger = get_logger(__name__)
        self.embedding_manager = embedding_manager or EmbeddingManager()
        
        # Set OpenAI API key
        openai.api_key = config.openai_api_key
        
        # Enhancement templates for different styles
        self.style_templates = {
            ImageStyle.PHOTOREALISTIC: {
                "lighting": "professional studio lighting",
                "quality": "8K resolution, highly detailed",
                "camera": "professional photography"
            },
            ImageStyle.CINEMATIC: {
                "lighting": "dramatic cinematic lighting",
                "quality": "film quality, cinematic composition",
                "camera": "cinematic camera angles"
            },
            ImageStyle.ARTISTIC: {
                "lighting": "artistic lighting",
                "quality": "artistic interpretation",
                "camera": "creative composition"
            },
            ImageStyle.MINIMALIST: {
                "lighting": "clean, minimal lighting",
                "quality": "minimalist design",
                "camera": "simple composition"
            }
        }
    
    async def handle(self, message: PromptEnhancementRequest) -> PromptEnhancementResult:
        """
        Handle a prompt enhancement request.
        
        Args:
            message: The enhancement request message
            
        Returns:
            Enhanced prompt result
        """
        start_time = time.time()
        
        try:
            log_function_call("prompt_enhancement", 
                            raw_prompt=message.payload.get("raw_prompt"),
                            user_id=message.user_id,
                            session_id=message.session_id)
            
            # Extract request parameters
            raw_prompt = message.payload.get("raw_prompt", "")
            style = message.payload.get("style", ImageStyle.PHOTOREALISTIC)
            category = message.payload.get("category", ImageCategory.OTHER)
            seed = message.payload.get("seed")
            
            # Get user preferences from memory
            user_preferences = await self._get_user_preferences(message.user_id)
            
            # Enhance the prompt
            enhanced_prompt = await self._enhance_prompt(
                raw_prompt=raw_prompt,
                style=style,
                category=category,
                user_preferences=user_preferences,
                seed=seed
            )
            
            # Store the enhanced prompt in memory
            await self._store_enhanced_prompt(
                raw_prompt=raw_prompt,
                enhanced_prompt=enhanced_prompt,
                user_id=message.user_id,
                session_id=message.session_id,
                style=style,
                category=category
            )
            
            # Prepare response
            result = PromptEnhancementResult(
                session_id=message.session_id,
                user_id=message.user_id,
                payload={
                    "enhanced_prompt": enhanced_prompt,
                    "original_prompt": raw_prompt,
                    "style": style,
                    "category": category,
                    "seed": seed,
                    "enhancement_metadata": {
                        "user_preferences_used": bool(user_preferences),
                        "enhancement_method": "ai_enhanced",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
            
            duration_ms = (time.time() - start_time) * 1000
            log_function_result("prompt_enhancement", result.payload, duration_ms)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Prompt enhancement failed: {e}")
            # Return error result
            return PromptEnhancementResult(
                session_id=message.session_id,
                user_id=message.user_id,
                payload={
                    "error": str(e),
                    "enhanced_prompt": raw_prompt,  # Fallback to original
                    "original_prompt": raw_prompt
                }
            )
    
    async def _enhance_prompt(
        self,
        raw_prompt: str,
        style: ImageStyle,
        category: ImageCategory,
        user_preferences: Dict[str, Any],
        seed: Optional[int] = None
    ) -> str:
        """
        Enhance a raw prompt using AI and user preferences.
        
        Args:
            raw_prompt: The original user prompt
            style: Desired image style
            category: Image category
            user_preferences: User's style preferences
            seed: Optional seed for consistency
            
        Returns:
            Enhanced prompt string
        """
        try:
            # Build enhancement context
            enhancement_context = self._build_enhancement_context(
                raw_prompt, style, category, user_preferences
            )
            
            # Use OpenAI to enhance the prompt
            enhanced_prompt = await self._ai_enhance_prompt(
                raw_prompt, enhancement_context
            )
            
            # Apply style-specific enhancements
            enhanced_prompt = self._apply_style_enhancements(
                enhanced_prompt, style, category
            )
            
            # Add seed if provided
            if seed is not None:
                enhanced_prompt += f", seed: {seed}"
            
            return enhanced_prompt
            
        except Exception as e:
            self.logger.error(f"Prompt enhancement failed: {e}")
            # Fallback to basic enhancement
            return self._fallback_enhancement(raw_prompt, style, category)
    
    def _build_enhancement_context(
        self,
        raw_prompt: str,
        style: ImageStyle,
        category: ImageCategory,
        user_preferences: Dict[str, Any]
    ) -> str:
        """Build context for prompt enhancement."""
        context_parts = []
        
        # Add category-specific context
        if category == ImageCategory.PRODUCT:
            context_parts.append("product photography, commercial quality")
        elif category == ImageCategory.PORTRAIT:
            context_parts.append("portrait photography, professional lighting")
        elif category == ImageCategory.LANDSCAPE:
            context_parts.append("landscape photography, natural lighting")
        elif category == ImageCategory.ABSTRACT:
            context_parts.append("abstract art, creative interpretation")
        
        # Add style-specific context
        style_context = self.style_templates.get(style, {})
        if style_context:
            context_parts.extend([
                style_context.get("lighting", ""),
                style_context.get("quality", ""),
                style_context.get("camera", "")
            ])
        
        # Add user preferences
        if user_preferences:
            if user_preferences.get("lighting_preferences"):
                context_parts.extend(user_preferences["lighting_preferences"])
            if user_preferences.get("color_preferences"):
                context_parts.extend(user_preferences["color_preferences"])
        
        # Filter out empty strings and join
        context_parts = [part for part in context_parts if part.strip()]
        return ", ".join(context_parts)
    
    async def _ai_enhance_prompt(self, raw_prompt: str, context: str) -> str:
        """
        Use OpenAI to enhance the prompt.
        
        Args:
            raw_prompt: Original prompt
            context: Enhancement context
            
        Returns:
            AI-enhanced prompt
        """
        try:
            system_prompt = f"""
            You are an expert image generation prompt engineer. Your task is to enhance user prompts
            for AI image generation by adding detail, style information, and technical specifications.
            
            Enhancement context: {context}
            
            Guidelines:
            1. Keep the core concept from the original prompt
            2. Add relevant technical details (lighting, composition, quality)
            3. Incorporate the style context naturally
            4. Make the prompt specific and actionable
            5. Keep the total length reasonable (under 200 words)
            
            Return only the enhanced prompt, no explanations.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Enhance this prompt: {raw_prompt}"}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            enhanced_prompt = response.choices[0].message.content.strip()
            return enhanced_prompt
            
        except Exception as e:
            self.logger.error(f"AI enhancement failed: {e}")
            # Fallback to rule-based enhancement
            return self._rule_based_enhancement(raw_prompt, context)
    
    def _rule_based_enhancement(self, raw_prompt: str, context: str) -> str:
        """Fallback rule-based prompt enhancement."""
        enhanced_parts = [raw_prompt]
        
        # Add context if available
        if context:
            enhanced_parts.append(context)
        
        # Add quality specifications
        enhanced_parts.extend([
            "high quality",
            "detailed",
            "professional"
        ])
        
        return ", ".join(enhanced_parts)
    
    def _apply_style_enhancements(
        self,
        prompt: str,
        style: ImageStyle,
        category: ImageCategory
    ) -> str:
        """Apply style-specific enhancements to the prompt."""
        enhanced_prompt = prompt
        
        # Style-specific additions
        if style == ImageStyle.PHOTOREALISTIC:
            enhanced_prompt += ", photorealistic, 8K resolution"
        elif style == ImageStyle.CINEMATIC:
            enhanced_prompt += ", cinematic lighting, dramatic shadows"
        elif style == ImageStyle.ARTISTIC:
            enhanced_prompt += ", artistic interpretation, creative style"
        elif style == ImageStyle.MINIMALIST:
            enhanced_prompt += ", minimalist design, clean composition"
        
        # Category-specific enhancements
        if category == ImageCategory.PRODUCT:
            enhanced_prompt += ", commercial photography, studio lighting"
        elif category == ImageCategory.PORTRAIT:
            enhanced_prompt += ", professional portrait, flattering lighting"
        elif category == ImageCategory.LANDSCAPE:
            enhanced_prompt += ", natural lighting, scenic composition"
        
        return enhanced_prompt
    
    def _fallback_enhancement(
        self,
        raw_prompt: str,
        style: ImageStyle,
        category: ImageCategory
    ) -> str:
        """Basic fallback enhancement when AI enhancement fails."""
        enhanced_parts = [
            raw_prompt,
            "high quality",
            "detailed",
            "professional"
        ]
        
        # Add basic style info
        if style == ImageStyle.PHOTOREALISTIC:
            enhanced_parts.append("photorealistic")
        elif style == ImageStyle.CINEMATIC:
            enhanced_parts.append("cinematic")
        
        return ", ".join(enhanced_parts)
    
    async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from memory."""
        try:
            if not self.embedding_manager:
                return {}
            
            # Get preference summary
            preferences = self.embedding_manager.get_user_preference_summary(user_id)
            
            if "error" in preferences:
                return {}
            
            return preferences.get("preferences_by_type", {})
            
        except Exception as e:
            self.logger.warning(f"Failed to get user preferences: {e}")
            return {}
    
    async def _store_enhanced_prompt(
        self,
        raw_prompt: str,
        enhanced_prompt: str,
        user_id: str,
        session_id: str,
        style: ImageStyle,
        category: ImageCategory
    ):
        """Store the enhanced prompt in memory."""
        try:
            if not self.embedding_manager:
                return
            
            # Store the enhanced prompt
            self.embedding_manager.store_prompt_embedding(
                prompt=enhanced_prompt,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "original_prompt": raw_prompt,
                    "style": style.value,
                    "category": category.value,
                    "enhancement_type": "ai_enhanced"
                }
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to store enhanced prompt: {e}")
    
    def get_enhancement_stats(self) -> Dict[str, Any]:
        """Get statistics about prompt enhancement."""
        return {
            "agent_type": "prompt_enhancer",
            "style_templates": len(self.style_templates),
            "supported_styles": [style.value for style in ImageStyle],
            "supported_categories": [cat.value for cat in ImageCategory],
            "embedding_manager_available": self.embedding_manager is not None
        }
    
    async def enhance_prompt(
        self,
        raw_prompt: str,
        style_preferences: Dict[str, Any],
        user_id: str
    ) -> "EnhancedPrompt":
        """
        Enhanced prompt using the existing handle method.
        
        Args:
            raw_prompt: The original user prompt
            style_preferences: User's style preferences
            user_id: The user's ID
            
        Returns:
            EnhancedPrompt object
        """
        from ..models import EnhancedPrompt
        
        # Create a PromptEnhancementRequest
        request = PromptEnhancementRequest(
            session_id="temp_session",
            user_id=user_id,
            payload={
                "raw_prompt": raw_prompt,
                "style": style_preferences.get("style", ImageStyle.PHOTOREALISTIC),
                "category": ImageCategory.OTHER
            }
        )
        
        # Use the existing handle method
        result = await self.handle(request)
        
        # Convert the result to EnhancedPrompt
        return EnhancedPrompt(
            original_prompt=raw_prompt,
            enhanced_prompt=result.payload.get("enhanced_prompt", raw_prompt),
            enhancement_notes="AI-enhanced prompt",
            style_suggestions=[style_preferences.get("style", "photorealistic")],
            confidence_score=0.8
        )

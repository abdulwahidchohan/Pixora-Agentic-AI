"""
ImageFX Agent for Pixora system.

Handles image generation using various AI image generation services
including OpenAI DALL-E, Google ImageFX, and other providers.
"""

import asyncio
import base64
import io
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import requests
from PIL import Image
from ..models import EnhancedPrompt, GeneratedImage, ImageMetadata
from ..utils.logger import get_logger
from ..utils.config import config

logger = get_logger(__name__)


class ImageFXAgent:
    """
    Agent responsible for generating images from enhanced prompts.
    
    Supports multiple image generation providers:
    - OpenAI DALL-E
    - Google ImageFX
    - Vertex AI
    - Custom providers
    """
    
    def __init__(self):
        """Initialize the ImageFXAgent."""
        self.logger = logger
        self.config = config
        self.providers = self._initialize_providers()
        
    def _initialize_providers(self) -> Dict[str, Any]:
        """Initialize available image generation providers."""
        providers = {}
        
        # OpenAI DALL-E
        if self.config.openai_api_key and self.config.openai_api_key != "test_key_for_testing":
            providers["openai"] = {
                "name": "OpenAI DALL-E",
                "enabled": True,
                "config": {
                    "api_key": self.config.openai_api_key,
                    "model": self.config.openai_model
                }
            }
        
        # Google ImageFX
        if self.config.use_imagefx and self.config.imagefx_api_key:
            providers["imagefx"] = {
                "name": "Google ImageFX",
                "enabled": True,
                "config": {
                    "api_key": self.config.imagefx_api_key,
                    "base_url": self.config.imagefx_base_url
                }
            }
        
        # Vertex AI
        if self.config.use_vertex_ai:
            providers["vertex_ai"] = {
                "name": "Google Vertex AI",
                "enabled": True,
                "config": {
                    "project_id": self.config.vertex_ai_project_id,
                    "location": self.config.vertex_ai_location
                }
            }
        
        self.logger.info("Image generation providers initialized", 
                        providers=list(providers.keys()),
                        enabled_count=sum(1 for p in providers.values() if p["enabled"]))
        
        return providers
    
    async def generate_images(self, enhanced_prompt: EnhancedPrompt, 
                            count: int = 1, size: str = "1024x1024") -> List[GeneratedImage]:
        """
        Generate images from an enhanced prompt.
        
        Args:
            enhanced_prompt: The enhanced prompt to use for generation
            count: Number of images to generate
            size: Image size (e.g., "1024x1024", "1792x1024")
            
        Returns:
            List of generated images
        """
        self.logger.info("Starting image generation", 
                        prompt_length=len(enhanced_prompt.prompt),
                        count=count,
                        size=size)
        
        if not self.providers:
            raise RuntimeError("No image generation providers available")
        
        # Select the best available provider
        provider = self._select_provider()
        if not provider:
            raise RuntimeError("No enabled image generation providers")
        
        self.logger.info("Using provider", provider_name=provider["name"])
        
        # Generate images
        generated_images = []
        for i in range(count):
            try:
                image = await self._generate_single_image(enhanced_prompt, provider, size, i + 1)
                generated_images.append(image)
            except Exception as e:
                self.logger.error("Failed to generate image", 
                                attempt=i + 1,
                                error=str(e))
                # Continue with other images if one fails
        
        self.logger.info("Image generation completed", 
                        requested=count,
                        generated=len(generated_images))
        
        return generated_images
    
    def _select_provider(self) -> Optional[Dict[str, Any]]:
        """Select the best available image generation provider."""
        # Priority order: OpenAI > ImageFX > Vertex AI
        priority_order = ["openai", "imagefx", "vertex_ai"]
        
        for provider_name in priority_order:
            if (provider_name in self.providers and 
                self.providers[provider_name]["enabled"]):
                return self.providers[provider_name]
        
        return None
    
    async def _generate_single_image(self, enhanced_prompt: EnhancedPrompt, 
                                   provider: Dict[str, Any], size: str, 
                                   image_number: int) -> GeneratedImage:
        """
        Generate a single image using the specified provider.
        
        Args:
            enhanced_prompt: The enhanced prompt to use
            provider: The provider configuration
            size: Image size
            image_number: Sequential number for this image
            
        Returns:
            Generated image data
        """
        provider_name = provider["name"].lower()
        
        if "openai" in provider_name:
            return await self._generate_with_openai(enhanced_prompt, provider, size, image_number)
        elif "imagefx" in provider_name:
            return await self._generate_with_imagefx(enhanced_prompt, provider, size, image_number)
        elif "vertex" in provider_name:
            return await self._generate_with_vertex_ai(enhanced_prompt, provider, size, image_number)
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")
    
    async def _generate_with_openai(self, enhanced_prompt: EnhancedPrompt, 
                                  provider: Dict[str, Any], size: str, 
                                  image_number: int) -> GeneratedImage:
        """Generate image using OpenAI DALL-E."""
        try:
            import openai
            
            # Configure OpenAI client
            client = openai.OpenAI(api_key=provider["config"]["api_key"])
            
            # Prepare the prompt with style preferences
            full_prompt = self._build_full_prompt(enhanced_prompt)
            
            # Generate image
            response = await asyncio.to_thread(
                client.images.generate,
                model="dall-e-3",
                prompt=full_prompt,
                size=size,
                quality="standard",
                n=1
            )
            
            # Download the image
            image_url = response.data[0].url
            image_data = await self._download_image(image_url)
            
            # Create metadata
            metadata = ImageMetadata(
                workflow_id=f"openai_{image_number}",
                user_id="test_user",  # TODO: Get from context
                timestamp=enhanced_prompt.timestamp,
                model_used="dall-e-3",
                size=size,
                prompt=full_prompt,
                style_preferences=enhanced_prompt.style_preferences,
                provider="openai",
                cost_estimate=0.04  # DALL-E 3 cost
            )
            
            return GeneratedImage(
                image_data=image_data,
                metadata=metadata,
                format="png"
            )
            
        except Exception as e:
            self.logger.error("OpenAI image generation failed", error=str(e))
            raise
    
    async def _generate_with_imagefx(self, enhanced_prompt: EnhancedPrompt, 
                                   provider: Dict[str, Any], size: str, 
                                   image_number: int) -> GeneratedImage:
        """Generate image using Google ImageFX."""
        try:
            # Prepare the prompt
            full_prompt = self._build_full_prompt(enhanced_prompt)
            
            # ImageFX API call (placeholder implementation)
            # TODO: Implement actual ImageFX API integration
            self.logger.warning("ImageFX integration not yet implemented")
            
            # For now, return a placeholder image
            placeholder_image = self._create_placeholder_image(size, full_prompt)
            
            metadata = ImageMetadata(
                workflow_id=f"imagefx_{image_number}",
                user_id="test_user",
                timestamp=enhanced_prompt.timestamp,
                model_used="imagefx",
                size=size,
                prompt=full_prompt,
                style_preferences=enhanced_prompt.style_preferences,
                provider="imagefx",
                cost_estimate=0.0
            )
            
            return GeneratedImage(
                image_data=placeholder_image,
                metadata=metadata,
                format="png"
            )
            
        except Exception as e:
            self.logger.error("ImageFX image generation failed", error=str(e))
            raise
    
    async def _generate_with_vertex_ai(self, enhanced_prompt: EnhancedPrompt, 
                                     provider: Dict[str, Any], size: str, 
                                     image_number: int) -> GeneratedImage:
        """Generate image using Google Vertex AI."""
        try:
            # TODO: Implement Vertex AI integration
            self.logger.warning("Vertex AI integration not yet implemented")
            
            full_prompt = self._build_full_prompt(enhanced_prompt)
            placeholder_image = self._create_placeholder_image(size, full_prompt)
            
            metadata = ImageMetadata(
                workflow_id=f"vertex_ai_{image_number}",
                user_id="test_user",
                timestamp=enhanced_prompt.timestamp,
                model_used="vertex-ai",
                size=size,
                prompt=full_prompt,
                style_preferences=enhanced_prompt.style_preferences,
                provider="vertex_ai",
                cost_estimate=0.0
            )
            
            return GeneratedImage(
                image_data=placeholder_image,
                metadata=metadata,
                format="png"
            )
            
        except Exception as e:
            self.logger.error("Vertex AI image generation failed", error=str(e))
            raise
    
    def _build_full_prompt(self, enhanced_prompt: EnhancedPrompt) -> str:
        """Build a complete prompt including style preferences."""
        prompt_parts = [enhanced_prompt.prompt]
        
        # Add style preferences
        if enhanced_prompt.style_preferences:
            style_text = ", ".join([f"{k}: {v}" for k, v in enhanced_prompt.style_preferences.items()])
            prompt_parts.append(f"Style: {style_text}")
        
        # Add quality and technical specifications
        prompt_parts.append("High quality, detailed, professional")
        
        return ", ".join(prompt_parts)
    
    async def _download_image(self, url: str) -> bytes:
        """Download image from URL."""
        try:
            response = await asyncio.to_thread(requests.get, url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            self.logger.error("Failed to download image", url=url, error=str(e))
            raise
    
    def _create_placeholder_image(self, size: str, prompt: str) -> bytes:
        """Create a placeholder image for testing purposes."""
        try:
            # Parse size
            width, height = map(int, size.split('x'))
            
            # Create a simple placeholder image
            image = Image.new('RGB', (width, height), color='#f0f0f0')
            
            # Add text (simplified)
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(image)
            
            # Try to use a default font
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            # Add prompt text
            text = f"Placeholder: {prompt[:50]}..."
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x, y), text, fill='#333333', font=font)
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            return img_byte_arr.getvalue()
            
        except Exception as e:
            self.logger.error("Failed to create placeholder image", error=str(e))
            # Return a minimal 1x1 pixel image as fallback
            return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'
    
    async def get_generation_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the status of an image generation workflow.
        
        Args:
            workflow_id: The workflow ID to check
            
        Returns:
            Dict containing generation status
        """
        # TODO: Implement actual status tracking
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "progress": 100,
            "estimated_completion": None
        }
    
    async def cancel_generation(self, workflow_id: str) -> bool:
        """
        Cancel an ongoing image generation.
        
        Args:
            workflow_id: The workflow ID to cancel
            
        Returns:
            True if cancellation was successful
        """
        # TODO: Implement actual cancellation
        self.logger.info("Image generation cancellation requested", workflow_id=workflow_id)
        return True
    
    async def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about available image generation providers.
        
        Returns:
            Dict containing provider information
        """
        provider_info = {}
        
        for name, provider in self.providers.items():
            provider_info[name] = {
                "name": provider["name"],
                "enabled": provider["enabled"],
                "capabilities": {
                    "sizes": ["1024x1024", "1792x1024", "1024x1792"],
                    "formats": ["png", "jpeg"],
                    "quality": ["standard", "hd"]
                }
            }
        
        return provider_info

"""
Core data models for Pixora system.

Defines the data structures used for agent communication,
session management, and image metadata.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
import uuid


class MessageType(str, Enum):
    """Types of messages that can be sent between agents."""
    ENHANCE_PROMPT = "enhance_prompt"
    ENHANCE_PROMPT_RESULT = "enhance_prompt.result"
    VALIDATE_PROMPT = "validate_prompt"
    VALIDATE_PROMPT_RESULT = "validate_prompt.result"
    GENERATE_IMAGE = "generate_image"
    GENERATE_IMAGE_RESULT = "generate_image.result"
    CATEGORIZE_IMAGE = "categorize_image"
    CATEGORIZE_IMAGE_RESULT = "categorize_image.result"
    SAVE_IMAGE = "save_image"
    SAVE_IMAGE_RESULT = "save_image.result"
    STORE_MEMORY = "store_memory"
    STORE_MEMORY_RESULT = "store_memory.result"
    ERROR = "error"


class ImageCategory(str, Enum):
    """Categories for generated images."""
    PRODUCT = "product"
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    ABSTRACT = "abstract"
    ANIMAL = "animal"
    VEHICLE = "vehicle"
    FOOD = "food"
    ARCHITECTURE = "architecture"
    OTHER = "other"


class ImageStyle(str, Enum):
    """Styling options for image generation."""
    PHOTOREALISTIC = "photorealistic"
    CINEMATIC = "cinematic"
    ARTISTIC = "artistic"
    CARTOON = "cartoon"
    SKETCH = "sketch"
    PAINTING = "painting"
    MINIMALIST = "minimalist"
    VINTAGE = "vintage"


class Priority(str, Enum):
    """Priority levels for message processing."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    INTERACTIVE = "interactive"


class BaseMessage(BaseModel):
    """Base message structure for all agent communication."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    session_id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class PromptEnhancementRequest(BaseMessage):
    """Request to enhance a user prompt."""
    type: MessageType = MessageType.ENHANCE_PROMPT
    payload: Dict[str, Any] = Field(..., description="Prompt enhancement parameters")
    
    @validator('payload')
    def validate_payload(cls, v):
        required_fields = ['raw_prompt']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Missing required field: {field}")
        return v


class PromptEnhancementResult(BaseMessage):
    """Result of prompt enhancement."""
    type: MessageType = MessageType.ENHANCE_PROMPT_RESULT
    payload: Dict[str, Any] = Field(..., description="Enhanced prompt result")


class ImageGenerationRequest(BaseMessage):
    """Request to generate images."""
    type: MessageType = MessageType.GENERATE_IMAGE
    payload: Dict[str, Any] = Field(..., description="Image generation parameters")
    
    @validator('payload')
    def validate_payload(cls, v):
        required_fields = ['enhanced_prompt']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Missing required field: {field}")
        return v


class ImageGenerationResult(BaseMessage):
    """Result of image generation."""
    type: MessageType = MessageType.GENERATE_IMAGE_RESULT
    payload: Dict[str, Any] = Field(..., description="Generated images and metadata")


class ImageMetadata(BaseModel):
    """Metadata for a generated image."""
    workflow_id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_cost: float = 0.0
    model_used: str = "unknown"
    image_id: Optional[str] = None
    prompt: Optional[str] = None
    enhanced_prompt: Optional[str] = None
    category: Optional[ImageCategory] = None
    style: Optional[ImageStyle] = None
    seed: Optional[int] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    generated_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    dimensions: Optional[Dict[str, int]] = None
    tags: List[str] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class Session(BaseModel):
    """User session information."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    
    def add_event(self, event_type: str, data: Dict[str, Any]):
        """Add an event to the session."""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        self.events.append(event)
        self.last_activity = datetime.utcnow()


class MemoryEntry(BaseModel):
    """Memory entry for user preferences and patterns."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # preference, example, pattern
    text: str
    embedding_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = 0
    
    def update_access(self):
        """Update access statistics."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1


class UserPreferences(BaseModel):
    """User preferences for image generation."""
    user_id: str
    preferred_styles: List[ImageStyle] = Field(default_factory=list)
    preferred_categories: List[ImageCategory] = Field(default_factory=list)
    lighting_preferences: List[str] = Field(default_factory=list)
    color_preferences: List[str] = Field(default_factory=list)
    quality_preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def update_preferences(self, **kwargs):
        """Update user preferences."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()


class ErrorMessage(BaseMessage):
    """Error message for failed operations."""
    type: MessageType = MessageType.ERROR
    payload: Dict[str, Any] = Field(..., description="Error details")
    
    @validator('payload')
    def validate_payload(cls, v):
        required_fields = ['error_code', 'error_message']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Missing required field: {field}")
        return v


# Additional models for the coordinator system
class UserRequest(BaseModel):
    """User request for image generation."""
    user_id: str
    session_id: str
    prompt: str
    style_preferences: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class EnhancedPrompt(BaseModel):
    """Enhanced prompt result from the prompt enhancer agent."""
    original_prompt: str
    enhanced_prompt: str
    enhancement_notes: Optional[str] = None
    style_suggestions: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.8)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class GeneratedImage(BaseModel):
    """Generated image with metadata."""
    image_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    enhanced_prompt: str
    image_data: Optional[bytes] = None  # Binary image data
    image_url: Optional[str] = None     # URL if stored externally
    file_path: Optional[str] = None     # Local file path
    category: ImageCategory = ImageCategory.OTHER
    style: ImageStyle = ImageStyle.PHOTOREALISTIC
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class WorkflowResult(BaseModel):
    """Result of a complete workflow execution."""
    workflow_id: str
    user_id: str
    original_prompt: str
    enhanced_prompt: str
    generated_images: List[GeneratedImage] = Field(default_factory=list)
    metadata: "ImageMetadata"
    status: str  # "completed", "failed", "cancelled"
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class UserSession(BaseModel):
    """User session information for the coordinator."""
    session_id: str
    user_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


# Type aliases for convenience
Message = Union[
    PromptEnhancementRequest,
    PromptEnhancementResult,
    ImageGenerationRequest,
    ImageGenerationResult,
    ErrorMessage
]

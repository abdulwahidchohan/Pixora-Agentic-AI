"""
Configuration management for Pixora system.

Handles environment variables, configuration validation,
and provides a centralized configuration interface.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Config(BaseSettings):
    """Centralized configuration for Pixora system."""
    
    # OpenAI Configuration
    openai_api_key: str = Field("test_key_for_testing", env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # Image Provider Selection
    use_imagefx: bool = Field(False, env="USE_IMAGEFX")
    use_vertex_ai: bool = Field(False, env="USE_VERTEX_AI")
    
    # ImageFX Configuration (Prototype/Development)
    imagefx_auth_token: Optional[str] = Field(None, env="IMAGEFX_AUTH_TOKEN")
    imagefx_base_url: str = Field("https://labs.google/fx", env="IMAGEFX_BASE_URL")
    
    # Vertex AI Configuration (Production)
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    vertex_ai_project_id: Optional[str] = Field(None, env="VERTEX_AI_PROJECT_ID")
    vertex_ai_location: str = Field("us-central1", env="VERTEX_AI_LOCATION")
    
    # Application Settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    debug_mode: bool = Field(False, env="DEBUG_MODE")
    memory_db_path: str = Field("./data/memory", env="MEMORY_DB_PATH")
    session_timeout_hours: int = Field(24, env="SESSION_TIMEOUT_HOURS")
    
    # Security & Rate Limiting
    max_images_per_request: int = Field(4, env="MAX_IMAGES_PER_REQUEST")
    rate_limit_per_minute: int = Field(10, env="RATE_LIMIT_PER_MINUTE")
    enable_moderation: bool = Field(True, env="ENABLE_MODERATION")
    
    # Storage Configuration
    desktop_storage_path: str = Field("~/Desktop/Pixora", env="DESKTOP_STORAGE_PATH")
    enable_metadata_storage: bool = Field(True, env="ENABLE_METADATA_STORAGE")
    image_format: str = Field("PNG", env="IMAGE_FORMAT")
    image_quality: int = Field(95, env="IMAGE_QUALITY")
    
    # Memory & Personalization
    memory_enabled: bool = Field(True, env="MEMORY_ENABLED")
    vector_db_type: str = Field("chroma", env="VECTOR_DB_TYPE")
    embedding_model: str = Field("all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    max_memory_entries: int = Field(1000, env="MAX_MEMORY_ENTRIES")
    
    # Monitoring & Observability
    enable_telemetry: bool = Field(False, env="ENABLE_TELEMETRY")
    log_to_file: bool = Field(True, env="LOG_TO_FILE")
    log_file_path: str = Field("./logs/pixora.log", env="LOG_FILE_PATH")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator('desktop_storage_path')
    def expand_desktop_path(cls, v):
        """Expand the desktop storage path to absolute path."""
        return str(Path(v).expanduser().resolve())
    
    @validator('memory_db_path')
    def expand_memory_path(cls, v):
        """Expand the memory database path to absolute path."""
        return str(Path(v).resolve())
    
    @validator('log_file_path')
    def expand_log_path(cls, v):
        """Expand the log file path to absolute path."""
        return str(Path(v).resolve())
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the configuration and return any issues."""
        issues = []
        
        # Check required ImageFX configuration
        if self.use_imagefx and not self.imagefx_auth_token:
            issues.append("ImageFX is enabled but no auth token provided")
        
        # Check required Vertex AI configuration
        if self.use_vertex_ai and not self.google_application_credentials:
            issues.append("Vertex AI is enabled but no service account credentials provided")
        
        # Check OpenAI configuration
        if not self.openai_api_key:
            issues.append("OpenAI API key is required")
        
        # Validate paths
        try:
            Path(self.desktop_storage_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create desktop storage path: {e}")
        
        try:
            Path(self.memory_db_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create memory database path: {e}")
        
        try:
            Path(self.log_file_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create log directory: {e}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def get_provider_config(self) -> Dict[str, Any]:
        """Get configuration for the active image provider."""
        if self.use_imagefx:
            return {
                "provider": "imagefx",
                "auth_token": self.imagefx_auth_token,
                "base_url": self.imagefx_base_url
            }
        elif self.use_vertex_ai:
            return {
                "provider": "vertex_ai",
                "credentials": self.google_application_credentials,
                "project_id": self.vertex_ai_project_id,
                "location": self.vertex_ai_location
            }
        else:
            raise ValueError("No image provider configured")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "openai": {
                "model": self.openai_model,
                "api_key_configured": bool(self.openai_api_key)
            },
            "image_provider": self.get_provider_config(),
            "storage": {
                "desktop_path": self.desktop_storage_path,
                "memory_path": self.memory_db_path,
                "log_path": self.log_file_path
            },
            "features": {
                "memory_enabled": self.memory_enabled,
                "moderation_enabled": self.enable_moderation,
                "max_images": self.max_images_per_request
            }
        }


def load_config() -> Config:
    """Load configuration from environment and .env file."""
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
    
    # Create and validate configuration
    config = Config()
    validation = config.validate_configuration()
    
    if not validation["valid"]:
        print("Configuration validation failed:")
        for issue in validation["issues"]:
            print(f"  - {issue}")
        print("\nPlease check your environment variables and .env file.")
        raise ValueError("Invalid configuration")
    
    return config


# Global configuration instance
config = load_config()

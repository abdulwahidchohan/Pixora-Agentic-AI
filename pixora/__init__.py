"""
Pixora - Agentic AI for Image Generation

A production-ready, modular architecture for AI-powered image generation
using specialized agents coordinated through OpenAI Agent SDK.
"""

__version__ = "0.1.0"
__author__ = "Pixora Team"
__description__ = "Transform ideas into high-quality images using AI agents"

from .coordinator import Coordinator
from .agents import (
    PromptEnhancer,
    GuardrailAgent,
    ImageFXAgent,
    CategorizerAgent,
    FileManagerAgent,
    MemoryAgent,
    SessionManager
)

__all__ = [
    "Coordinator",
    "PromptEnhancer",
    "GuardrailAgent", 
    "ImageFXAgent",
    "CategorizerAgent",
    "FileManagerAgent",
    "MemoryAgent",
    "SessionManager"
]

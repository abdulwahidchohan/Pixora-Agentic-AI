"""
Main Chainlit application for Pixora.

This is the entry point for the Pixora AI image generation application.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add the pixora package to the path
sys.path.append(str(Path(__file__).parent.parent))

import chainlit as cl
from chainlit import user_session, on_chat_start, on_message, on_chat_end

from pixora.coordinator import Coordinator
from pixora.models import UserRequest, WorkflowResult
from pixora.utils.logger import get_logger
from pixora.utils.config import config

# Initialize logging
logger = get_logger(__name__)

# Global coordinator instance
coordinator: Optional[Coordinator] = None

@on_chat_start
async def start():
    """Initialize the chat session."""
    global coordinator
    
    try:
        # Initialize the coordinator
        coordinator = Coordinator()
        
        # Get user session info
        user_id = user_session.get("user_id", "anonymous")
        session_id = user_session.get("session_id", "default")
        
        # Create welcome message
        welcome_message = f"""
🎨 **Welcome to Pixora - AI-Powered Image Generation!**

I'm your AI assistant for creating stunning images. Here's what I can do:

✨ **Smart Prompt Enhancement** - I'll improve your descriptions automatically
🛡️ **Safety & Moderation** - All content is checked for appropriateness  
🎭 **Style Transfer** - Apply cinematic, artistic, or photorealistic styles
📁 **Organized Storage** - Images are automatically categorized and saved locally
🧠 **Memory & Learning** - I remember your preferences and improve over time

**How to use:**
1. Describe the image you want (e.g., "a leather backpack with neon lighting")
2. I'll enhance your prompt and generate 4 high-quality variations
3. Images are automatically saved to your Desktop/Pixora folder
4. You can ask for variations or style adjustments

**Example prompts:**
- "A futuristic city skyline at sunset"
- "A cozy coffee shop interior with warm lighting"
- "A majestic dragon flying over mountains"

Ready to create something amazing? Just describe your vision! 🚀
        """
        
        await cl.Message(
            content=welcome_message,
            author="Pixora AI"
        ).send()
        
        # Store session info
        user_session.set("user_id", user_id)
        user_session.set("session_id", session_id)
        user_session.set("coordinator", coordinator)
        
        logger.info(f"Chat session started for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to start chat session: {str(e)}")
        await cl.Message(
            content="❌ Sorry, I encountered an error while starting the session. Please try again.",
            author="System"
        ).send()

@on_message
async def main(message: cl.Message):
    """Handle incoming user messages."""
    global coordinator
    
    try:
        user_id = user_session.get("user_id", "anonymous")
        session_id = user_session.get("session_id", "default")
        
        # Check if coordinator is available
        if not coordinator:
            await cl.Message(
                content="❌ System error: Coordinator not available. Please refresh the page.",
                author="System"
            ).send()
            return
        
        # Show typing indicator
        await cl.Message(
            content="🤔 Processing your request...",
            author="Pixora AI"
        ).send()
        
        # Create user request
        user_request = UserRequest(
            user_id=user_id,
            session_id=session_id,
            prompt=message.content,
            style_preferences={},  # TODO: Extract from user preferences
            timestamp=message.created_at
        )
        
        # Process the request through the coordinator
        workflow_result = await coordinator.process_request(user_request)
        
        if workflow_result.status == "completed":
            # Show enhanced prompt
            if workflow_result.enhanced_prompt:
                await cl.Message(
                    content=f"✨ **Enhanced Prompt:**\n{workflow_result.enhanced_prompt}",
                    author="Pixora AI"
                ).send()
            
            # Show results
            if workflow_result.generated_images:
                # TODO: Display actual generated images
                await cl.Message(
                    content=f"🎨 **Generated {len(workflow_result.generated_images)} images!**\n\n"
                           f"Images have been saved to your Desktop/Pixora folder and organized by category.",
                    author="Pixora AI"
                ).send()
            else:
                # Placeholder for when image generation is implemented
                await cl.Message(
                    content="🎯 **Prompt Enhanced Successfully!**\n\n"
                           f"Your enhanced prompt: *{workflow_result.enhanced_prompt}*\n\n"
                           "🔄 **Coming Soon:** Image generation will be available in the next update!\n"
                           "For now, I've enhanced your prompt to make it more detailed and effective.",
                    author="Pixora AI"
                ).send()
                
                # Show some tips
                tips = [
                    "💡 **Tip:** Be specific about lighting, style, and mood",
                    "💡 **Tip:** Mention artistic styles like 'cinematic', 'photorealistic', or 'artistic'",
                    "💡 **Tip:** Include details about composition and perspective"
                ]
                
                for tip in tips:
                    await cl.Message(
                        content=tip,
                        author="Pixora AI"
                    ).send()
        
        else:
            # Handle errors
            error_msg = workflow_result.error or "Unknown error occurred"
            await cl.Message(
                content=f"❌ **Error:** {error_msg}\n\nPlease try again or rephrase your request.",
                author="System"
            ).send()
        
        # Store conversation in session
        user_session.set("last_request", user_request)
        user_session.set("last_result", workflow_result)
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        await cl.Message(
            content=f"❌ **System Error:** {str(e)}\n\nPlease try again or contact support if the issue persists.",
            author="System"
        ).send()

@on_chat_end
async def end():
    """Clean up when chat session ends."""
    user_id = user_session.get("user_id", "anonymous")
    session_id = user_session.get("session_id", "default")
    
    logger.info(f"Chat session ended for user {user_id}, session {session_id}")
    
    # Clean up session data
    user_session.set("coordinator", None)
    user_session.set("last_request", None)
    user_session.set("last_result", None)

# Chainlit configuration
# Note: set_chat_profile and set_page_config are not available in current Chainlit version
# The app will use default configuration

# Note: Custom CSS styling is not available in current Chainlit version
# The app will use default Chainlit styling

if __name__ == "__main__":
    # This will be used when running the app directly
    print("Starting Pixora Chainlit application...")
    print("Run with: chainlit run chainlit_app/app.py")

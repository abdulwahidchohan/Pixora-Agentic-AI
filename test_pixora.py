#!/usr/bin/env python3
"""
Test script for Pixora components.

This script tests the basic functionality of the Pixora system.
"""

import asyncio
import sys
from pathlib import Path

# Add the pixora package to the path
sys.path.append(str(Path(__file__).parent))

from pixora.coordinator import Coordinator
from pixora.models import UserRequest
from pixora.utils.logger import get_logger

logger = get_logger(__name__)

async def test_coordinator():
    """Test the coordinator functionality."""
    print("🧪 Testing Pixora Coordinator...")
    
    try:
        # Initialize coordinator
        coordinator = Coordinator()
        print("✅ Coordinator initialized successfully")
        
        # Create a test user request
        test_request = UserRequest(
            user_id="test_user",
            session_id="test_session",
            prompt="a beautiful sunset over mountains",
            style_preferences={"style": "photorealistic"},
            timestamp=None
        )
        print("✅ Test user request created")
        
        # Process the request
        print("🔄 Processing test request...")
        result = await coordinator.process_request(test_request)
        
        print(f"✅ Request processed successfully!")
        print(f"   Status: {result.status}")
        print(f"   Workflow ID: {result.workflow_id}")
        print(f"   Enhanced Prompt: {result.enhanced_prompt}")
        
        if result.error:
            print(f"   Error: {result.error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        logger.error(f"Test failed: {str(e)}")
        return False

async def test_workflow_manager():
    """Test the workflow manager functionality."""
    print("\n🧪 Testing Workflow Manager...")
    
    try:
        from pixora.coordinator.workflow import WorkflowManager, WorkflowStatus, StepStatus
        
        # Initialize workflow manager
        workflow_manager = WorkflowManager()
        print("✅ Workflow manager initialized successfully")
        
        # Create a test workflow
        steps = [
            {"name": "Prompt Enhancement", "description": "Enhance user prompt"},
            {"name": "Image Generation", "description": "Generate images"},
            {"name": "Categorization", "description": "Categorize images"}
        ]
        
        workflow_id = workflow_manager.create_workflow("test_user", steps)
        print(f"✅ Test workflow created: {workflow_id}")
        
        # Get workflow state
        workflow_state = workflow_manager.get_workflow_state(workflow_id)
        print(f"✅ Workflow state retrieved: {workflow_state.status}")
        
        # Update step status
        if workflow_state.steps:
            step_id = workflow_state.steps[0].id
            workflow_manager.update_step_status(workflow_id, step_id, StepStatus.COMPLETED)
            print("✅ Step status updated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow manager test failed: {str(e)}")
        logger.error(f"Workflow manager test failed: {str(e)}")
        return False

async def test_session_manager():
    """Test the session manager functionality."""
    print("\n🧪 Testing Session Manager...")
    
    try:
        from pixora.coordinator.session import SessionManager
        
        # Initialize session manager
        session_manager = SessionManager()
        print("✅ Session manager initialized successfully")
        
        # Create a test session
        session_id = session_manager.create_session("test_user")
        print(f"✅ Test session created: {session_id}")
        
        # Get session
        session = session_manager.get_session(session_id)
        print(f"✅ Session retrieved: {session.session_id}")
        
        # Add conversation turn
        session_manager.add_conversation_turn(
            session_id, 
            "Hello, I want to generate an image", 
            "I'll help you create an image!"
        )
        print("✅ Conversation turn added successfully")
        
        # Get user preferences
        preferences = session_manager.get_user_preferences(session_id)
        print(f"✅ User preferences retrieved: {len(preferences)} items")
        
        return True
        
    except Exception as e:
        print(f"❌ Session manager test failed: {str(e)}")
        logger.error(f"Session manager test failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Pixora Component Tests...\n")
    
    tests = [
        test_coordinator,
        test_workflow_manager,
        test_session_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Pixora is ready to run.")
        print("\n🚀 To start the application, run:")
        print("   chainlit run chainlit_app/app.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

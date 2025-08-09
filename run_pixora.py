#!/usr/bin/env python3
"""
Startup script for Pixora.

This script provides an easy way to start the Pixora application.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import chainlit
        print("✅ Chainlit is installed")
    except ImportError:
        print("❌ Chainlit is not installed")
        print("   Install with: pip install chainlit")
        return False
    
    try:
        import openai
        print("✅ OpenAI is installed")
    except ImportError:
        print("❌ OpenAI is not installed")
        print("   Install with: pip install openai")
        return False
    
    return True

def check_environment():
    """Check if environment variables are set."""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("   Copy env.example to .env and configure your API keys")
        return False
    
    print("✅ Environment file found")
    return True

def start_application():
    """Start the Pixora application."""
    print("🚀 Starting Pixora...")
    
    # Change to the chainlit_app directory
    app_dir = Path("chainlit_app")
    if not app_dir.exists():
        print("❌ chainlit_app directory not found")
        return False
    
    os.chdir(app_dir)
    
    # Start the application
    try:
        subprocess.run([
            sys.executable, "-m", "chainlit", "run", "app.py", "--port", "8000"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start application: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Pixora stopped by user")
        return True
    
    return True

def main():
    """Main entry point."""
    print("🎨 Pixora - AI-Powered Image Generation")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again")
        return 1
    
    # Check environment
    if not check_environment():
        print("\n⚠️  Please configure your environment and try again")
        return 1
    
    print("\n✅ All checks passed!")
    print("\n🚀 Starting Pixora application...")
    print("   The application will open in your browser at http://localhost:8000")
    print("   Press Ctrl+C to stop the application")
    print()
    
    # Start the application
    if start_application():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())

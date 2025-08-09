# 🚀 Pixora Quick Start Guide

Get Pixora up and running in 5 minutes!

## 📋 Prerequisites

- Python 3.9 or higher
- OpenAI API key
- Git (to clone the repository)

## ⚡ Quick Setup

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd pixora
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp env.example .env
# Edit .env with your OpenAI API key
```

### 4. Test the System
```bash
python test_pixora.py
```

### 5. Start the Application
```bash
python run_pixora.py
```

The application will open at `http://localhost:8000` in your browser!

## 🎯 What You Can Do Right Now

✅ **Prompt Enhancement** - AI automatically improves your image descriptions  
✅ **Session Management** - Tracks your conversations and preferences  
✅ **Workflow Management** - Orchestrates the entire image generation process  
🔄 **Coming Soon** - Actual image generation (currently in development)  

## 🧪 Testing the System

Run the test script to verify everything is working:
```bash
python test_pixora.py
```

You should see:
```
🚀 Starting Pixora Component Tests...

🧪 Testing Pixora Coordinator...
✅ Coordinator initialized successfully
✅ Test user request created
🔄 Processing test request...
✅ Request processed successfully!
   Status: completed
   Workflow ID: workflow_20241201_123456
   Enhanced Prompt: [Your enhanced prompt here]

🧪 Testing Workflow Manager...
✅ Workflow manager initialized successfully
✅ Test workflow created: [workflow-id]
✅ Workflow state retrieved: pending
✅ Step status updated successfully

🧪 Testing Session Manager...
✅ Session manager initialized successfully
✅ Test session created: [session-id]
✅ Session retrieved: [session-id]
✅ Conversation turn added successfully
✅ User preferences retrieved: 0 items

📊 Test Results: 3/3 tests passed
🎉 All tests passed! Pixora is ready to run.
```

## 🎨 Using the Application

1. **Open your browser** to `http://localhost:8000`
2. **Type a description** like "a leather backpack with neon lighting"
3. **Watch the AI enhance** your prompt automatically
4. **See the results** (enhanced prompts for now, images coming soon!)

## 🆘 Troubleshooting

### Common Issues

**Import Error: No module named 'pixora'**
- Make sure you're in the project root directory
- Check that the virtual environment is activated

**Chainlit not found**
- Install with: `pip install chainlit`

**OpenAI API errors**
- Check your `.env` file has the correct `OPENAI_API_KEY`
- Verify your API key is valid and has credits

**Port already in use**
- Change the port in `run_pixora.py` or stop other services using port 8000

### Getting Help

- Check the logs for detailed error messages
- Run `python test_pixora.py` to isolate issues
- Ensure all dependencies are installed correctly

## 🚀 Next Steps

Once you have the basic system running:

1. **Explore the UI** - Try different prompts and see how the AI enhances them
2. **Check the logs** - Monitor the system's behavior
3. **Customize settings** - Modify configuration in `.env`
4. **Wait for updates** - Image generation is coming soon!

## 📚 Learn More

- **Full Documentation**: See `README.md` for complete details
- **Architecture**: Understand the system design in the README
- **Development**: Check the code structure in the `pixora/` directory

---

**Happy creating! 🎨✨**

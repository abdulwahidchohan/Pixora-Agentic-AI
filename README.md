# Pixora — Agentic AI for Image Generation

> **Transform ideas into high-quality images using AI agents**

Pixora is a production-ready, modular architecture for AI-powered image generation. It uses specialized agents coordinated through OpenAI Agent SDK to enhance prompts, generate images, categorize outputs, and manage local storage with a beautiful Chainlit UI.

## 🚀 Features

- **Multi-Agent Architecture**: Specialized agents for prompt enhancement, guardrails, image generation, categorization, and file management
- **Smart Prompt Enhancement**: AI-powered prompt improvement using user preferences and memory
- **Local Storage Management**: Organized desktop folders with metadata preservation
- **Beautiful UI**: Modern Chainlit interface for seamless user experience
- **Extensible Design**: Easy to swap between ImageFX (prototype) and Vertex AI Imagen (production)
- **Memory & Personalization**: Learn from user preferences and interaction history

## 🏗️ Architecture

```
User (Chainlit UI)
   │
   ├─> Coordinator (Agent SDK) orchestrates workflow
   │    ├─> Prompt Enhancer Agent (improves prompts)
   │    ├─> Guardrail Agent (safety & moderation)
   │    ├─> ImageFX Agent (generates images)
   │    ├─> Categorizer Agent (classifies outputs)
   │    ├─> File Manager Agent (saves locally)
   │    └─> Memory Agent (stores preferences)
   │
   └─> Returns images + metadata to user
```

## 🛠️ System Components

1. **Chainlit UI** - Chat-style interface for user interaction
2. **Coordinator** - Orchestrates agent-to-agent communication
3. **Prompt Enhancer** - Improves prompt detail and style
4. **Guardrail Agent** - Moderation and safety checks
5. **ImageFX Agent** - Handles image generation API calls
6. **Categorizer Agent** - Classifies and organizes images
7. **File Manager** - Local storage with metadata preservation
8. **Memory Agent** - Vector store for user preferences
9. **Session Manager** - Groups interactions into sessions
10. **Auth Handler** - Secure token management

## 📁 Project Structure

```
pixora/
├── agents/                 # Specialized AI agents
├── chainlit_app/          # Chainlit UI components
├── coordinator/           # Agent orchestration
├── utils/                 # Shared utilities
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key
- ImageFX access (for prototype) or Vertex AI credentials (for production)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd pixora
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application**
   ```bash
   chainlit run chainlit_app/app.py
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# ImageFX Configuration (Prototype)
IMAGEFX_AUTH_TOKEN=your_imagefx_token

# Vertex AI Configuration (Production)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
VERTEX_AI_PROJECT_ID=your_project_id

# Application Settings
LOG_LEVEL=INFO
MEMORY_DB_PATH=./data/memory
```

### Image Provider Selection

**Prototype (ImageFX)**: Set `USE_IMAGEFX=true` in `.env`
**Production (Vertex AI)**: Set `USE_VERTEX_AI=true` in `.env`

## 📊 Usage Examples

### Basic Image Generation

1. Open the Chainlit UI
2. Type: "Generate a leather backpack with neon lighting"
3. The system will:
   - Enhance your prompt automatically
   - Generate 4 high-quality images
   - Categorize and save them to `~/Desktop/Pixora/Products/`
   - Store metadata for future reference

### Advanced Features

- **Style Transfer**: "Make it more cinematic with shallow depth of field"
- **Variations**: "Generate variations with different lighting"
- **Reference Images**: Upload an image for style reference

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pixora

# Run specific test file
pytest tests/test_prompt_enhancer.py
```

## 🚀 Deployment

### Local Development
```bash
chainlit run chainlit_app/app.py --dev
```

### Production
```bash
# Using systemd
sudo systemctl enable pixora
sudo systemctl start pixora

# Using Docker
docker build -t pixora .
docker run -p 8000:8000 pixora
```

## 🔒 Security & Privacy

- **Token Encryption**: All API keys encrypted at rest
- **Local Storage**: Images saved locally on user's desktop
- **User Consent**: Clear consent for data usage and storage
- **Rate Limiting**: Prevents abuse and ensures fair usage

## 📈 Monitoring & Observability

- **Structured Logging**: JSON-formatted logs for easy parsing
- **Error Tracking**: Comprehensive error reporting and alerting
- **Usage Metrics**: Track generation costs and user patterns
- **Health Checks**: Monitor agent health and API status

## 🛣️ Roadmap

- [x] Core architecture design
- [x] Basic agent implementations
- [x] Chainlit UI integration
- [ ] ImageFX integration (prototype)
- [ ] Vertex AI integration (production)
- [ ] Advanced memory and personalization
- [ ] Multi-user support and authentication
- [ ] Cloud deployment and scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/pixora/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/pixora/discussions)
- **Documentation**: [Wiki](https://github.com/your-org/pixora/wiki)

## 🙏 Acknowledgments

- OpenAI for the Agent SDK
- Chainlit for the beautiful UI framework
- Google for Vertex AI Imagen
- The open-source AI community

---

**Built with ❤️ for the future of AI-powered creativity**

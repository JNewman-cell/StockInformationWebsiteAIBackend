# StockInformationWebsiteAIBackend

A FastAPI-based backend service with LangGraph AI agent for intelligent stock information analysis.

## 🚀 Features

- **FastAPI Framework**: Modern, fast (high-performance) web framework for building APIs
- **LangGraph AI Agent**: Sophisticated AI agent using LangGraph for multi-step reasoning
- **OpenAI Integration**: Leverages GPT models for natural language understanding
- **Async Support**: Fully asynchronous for high performance
- **RESTful API**: Clean and well-documented API endpoints
- **CORS Support**: Configured for cross-origin requests
- **Environment Configuration**: Flexible configuration via environment variables

## 📋 Prerequisites

- Python 3.9 or higher
- OpenAI API key
- pip package manager

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JNewman-cell/StockInformationWebsiteAIBackend.git
   cd StockInformationWebsiteAIBackend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## ⚙️ Configuration

Edit the `.env` file with your settings:

```env
OPENAI_API_KEY=your_openai_api_key_here
APP_NAME=StockInformationWebsiteAIBackend
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Database Configuration (Optional - for authenticated API endpoints)
# Update with your Neon PostgreSQL credentials if using database features
DATABASE_URL=postgresql://username:password@your-neon-host.neon.tech/your_db?sslmode=require

# JWT Configuration (Optional - for authenticated endpoints)
JWT_SECRET=your_jwt_secret_here
JWT_ALGORITHM=HS256
JWT_ISSUER=https://neon.tech

AGENT_MODEL=gpt-4-turbo-preview
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=2000
```

### Database Setup (Optional)

If you want to use authenticated API endpoints and database features:

1. **Get your Neon database credentials** from https://console.neon.tech
2. **Update `DATABASE_URL`** in your `.env` file with your actual credentials:
   ```env
   DATABASE_URL=postgresql://username:password@ep-xxxxx.us-west-2.aws.neon.tech/dbname?sslmode=require
   ```
3. The application will automatically create the necessary tables on startup

## 🚀 Running the Application

### Development Mode

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Endpoints

#### Health Check
```http
GET /
GET /health
```

Returns the health status of the application.

**Response:**
```json
{
  "status": "healthy",
  "app_name": "StockInformationWebsiteAIBackend",
  "version": "1.0.0"
}
```

#### Query AI Agent
```http
POST /query
```

Send a query to the LangGraph AI agent for stock analysis.

**Request Body:**
```json
{
  "query": "What is the current trend for AAPL stock?",
  "context": {
    "timeframe": "1 week"
  }
}
```

**Response:**
```json
{
  "response": "Based on the analysis...",
  "metadata": {
    "query": "What is the current trend for AAPL stock?",
    "context": {"timeframe": "1 week"}
  }
}
```

#### Agent Info
```http
GET /agent/info
```

Get information about the AI agent configuration.

**Response:**
```json
{
  "model": "gpt-4-turbo-preview",
  "temperature": 0.7,
  "max_tokens": 2000,
  "status": "active"
}
```

## 🏗️ Project Structure

```
StockInformationWebsiteAIBackend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment configuration
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── app/
    ├── __init__.py       # App package initialization
    ├── config.py         # Configuration management
    └── agent.py          # LangGraph AI agent implementation
```

## 🤖 LangGraph Agent Architecture

The AI agent uses a state graph with three main nodes:

1. **Understand Query**: Analyzes the user's intent
2. **Process Query**: Processes the query with additional context
3. **Generate Response**: Creates a final, actionable response

```
[Start] → [Understand Query] → [Process Query] → [Generate Response] → [End]
```

## 🔧 Dependencies

### Core Dependencies
- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **pydantic**: Data validation
- **pydantic-settings**: Settings management

### LangGraph & AI
- **langgraph**: Graph-based agent framework
- **langchain**: LLM application framework
- **langchain-core**: Core LangChain functionality
- **langchain-openai**: OpenAI integration
- **openai**: OpenAI API client

### Utilities
- **python-dotenv**: Environment variable management
- **httpx**: HTTP client
- **aiohttp**: Async HTTP client
- **tiktoken**: Token counting

## 🧪 Testing

You can test the API using curl or the interactive Swagger UI:

### Using Swagger UI (Recommended)
1. Start the application: `python main.py`
2. Open http://localhost:8000/docs in your browser
3. Try out endpoints directly from the web interface

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Query the agent (public endpoint)
curl -X POST http://localhost:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"What is the current trend for AAPL stock?\", \"context\": {\"timeframe\": \"1 week\"}}"

# Get agent info
curl http://localhost:8000/agent/info
```

**Note for Windows `cmd.exe`**: Replace `\` with `^` for line continuation in the curl command above.

### Authenticated Endpoints (with Database)

If you've configured a database, you can test authenticated endpoints:

```bash
# Analyze stock price action (requires JWT token)
curl -X POST http://localhost:8000/api/v1/analyze/price-action ^
  -H "Content-Type: application/json" ^
  -H "x-stack-access-token: your_jwt_token_here" ^
  -d "{\"ticker\": \"AAPL\", \"additional_context\": \"Last 30 days\"}"

# Get user stats (requires JWT token)
curl http://localhost:8000/api/v1/users/me/stats ^
  -H "x-stack-access-token: your_jwt_token_here"
```

## 🔒 Security Considerations

- Never commit your `.env` file with real API keys
- Use environment variables for sensitive configuration
- Configure CORS appropriately for production
- Consider rate limiting for production deployments
- Keep dependencies updated

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the MIT License.

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- LangChain and LangGraph for AI capabilities
- OpenAI for language models
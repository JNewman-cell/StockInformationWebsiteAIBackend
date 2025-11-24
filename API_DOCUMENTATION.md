# API Documentation

## Overview

This document provides detailed information about the StockInformationWebsiteAIBackend API endpoints, request/response formats, and usage examples.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, consider implementing:
- API key authentication
- JWT tokens
- OAuth 2.0

## Endpoints

### 1. Root / Health Check

**Endpoint:** `GET /`

**Description:** Returns basic health status and application information.

**Response:**
```json
{
  "status": "healthy",
  "app_name": "StockInformationWebsiteAIBackend",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK`: Service is healthy

---

### 2. Health Check

**Endpoint:** `GET /health`

**Description:** Detailed health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "app_name": "StockInformationWebsiteAIBackend",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK`: Service is healthy

---

### 3. Query AI Agent

**Endpoint:** `POST /query`

**Description:** Send a query to the LangGraph AI agent for stock information analysis.

**Request Body:**
```json
{
  "query": "string",
  "context": {
    "key": "value"
  }
}
```

**Parameters:**
- `query` (required): The user's question about stocks
- `context` (optional): Additional context as key-value pairs

**Example Request:**
```json
{
  "query": "What is the current trend for AAPL stock?",
  "context": {
    "timeframe": "1 week",
    "indicators": ["RSI", "MACD"]
  }
}
```

**Response:**
```json
{
  "response": "Based on the analysis, AAPL stock shows...",
  "metadata": {
    "query": "What is the current trend for AAPL stock?",
    "context": {
      "timeframe": "1 week",
      "indicators": ["RSI", "MACD"]
    },
    "understanding": "...",
    "processing": "...",
    "final_response": true
  }
}
```

**Status Codes:**
- `200 OK`: Query processed successfully
- `422 Unprocessable Entity`: Invalid request format
- `500 Internal Server Error`: Error processing query
- `503 Service Unavailable`: Agent not initialized

---

### 4. Agent Information

**Endpoint:** `GET /agent/info`

**Description:** Get information about the AI agent configuration and status.

**Response:**
```json
{
  "model": "gpt-4-turbo-preview",
  "temperature": 0.7,
  "max_tokens": 2000,
  "status": "active"
}
```

**Status Codes:**
- `200 OK`: Information retrieved successfully

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: Service temporarily unavailable

---

## Example Usage

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Query the agent
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current trend for AAPL stock?",
    "context": {"timeframe": "1 week"}
  }'

# Get agent information
curl http://localhost:8000/agent/info
```

### Using Python requests

```python
import requests

base_url = "http://localhost:8000"

# Health check
response = requests.get(f"{base_url}/health")
print(response.json())

# Query the agent
query_data = {
    "query": "What is the current trend for AAPL stock?",
    "context": {"timeframe": "1 week"}
}
response = requests.post(f"{base_url}/query", json=query_data)
print(response.json())

# Get agent information
response = requests.get(f"{base_url}/agent/info")
print(response.json())
```

### Using JavaScript fetch

```javascript
const baseUrl = 'http://localhost:8000';

// Health check
fetch(`${baseUrl}/health`)
  .then(response => response.json())
  .then(data => console.log(data));

// Query the agent
fetch(`${baseUrl}/query`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'What is the current trend for AAPL stock?',
    context: { timeframe: '1 week' }
  })
})
  .then(response => response.json())
  .then(data => console.log(data));

// Get agent information
fetch(`${baseUrl}/agent/info`)
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## Rate Limiting

Currently, there are no rate limits. For production, consider implementing:
- Request rate limiting per IP
- Token bucket algorithm
- User-based quotas

---

## Best Practices

1. **Error Handling**: Always handle potential error responses
2. **Timeouts**: Set appropriate timeout values for requests
3. **Retries**: Implement exponential backoff for retries
4. **Validation**: Validate data before sending requests
5. **Context**: Provide relevant context for better AI responses

---

## Interactive Documentation

For interactive API documentation, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

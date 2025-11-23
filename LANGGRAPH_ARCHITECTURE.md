# LangGraph Agent Architecture Documentation

## Overview

The Stock Information AI Agent is built using LangGraph, which provides a framework for creating stateful, graph-based AI agents. This document explains the architecture, workflow, and implementation details.

## What is LangGraph?

LangGraph is a library for building stateful, multi-actor applications with Large Language Models (LLMs). It extends LangChain with the ability to create cyclical graphs and maintain state across multiple steps.

### Key Concepts

1. **State Graph**: A directed graph where nodes represent processing steps
2. **State**: Shared data structure passed between nodes
3. **Nodes**: Processing functions that transform state
4. **Edges**: Connections between nodes defining the workflow
5. **Compilation**: Converting the graph definition into an executable workflow

## Agent Architecture

### State Definition

The agent uses a typed state dictionary:

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    context: Optional[Dict[str, Any]]
    response: str
    metadata: Dict[str, Any]
```

**State Components:**
- `messages`: Conversation history (accumulated across nodes)
- `query`: User's original question
- `context`: Additional contextual information
- `response`: Final response to the user
- `metadata`: Processing metadata for debugging/tracking

### Graph Structure

```
┌─────────────────┐
│   Entry Point   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Understand Query│ ← Analyzes user intent
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Process Query   │ ← Processes with context
└────────┬────────┘
         │
         v
┌─────────────────┐
│Generate Response│ ← Creates final response
└────────┬────────┘
         │
         v
┌─────────────────┐
│      END        │
└─────────────────┘
```

## Node Implementations

### 1. Understand Query Node

**Purpose**: Analyze the user's query to understand their intent.

**Process**:
1. Creates a system message defining the agent's role
2. Adds the user's query as a human message
3. Sends to LLM for intent analysis
4. Stores understanding in metadata

**Input State**:
- `query`: User's question
- `messages`: Empty initially

**Output State**:
- `messages`: Updated with system, human, and AI messages
- `metadata.understanding`: LLM's understanding of the query

### 2. Process Query Node

**Purpose**: Process the query with additional context and perform detailed analysis.

**Process**:
1. Extracts context information if provided
2. Formulates a detailed analysis request
3. Sends to LLM for processing
4. Stores processing results in metadata

**Input State**:
- `query`: User's question
- `context`: Optional additional context
- `messages`: Previous conversation history

**Output State**:
- `messages`: Updated with processing conversation
- `metadata.processing`: LLM's detailed analysis

### 3. Generate Response Node

**Purpose**: Create a final, actionable response for the user.

**Process**:
1. Requests a summary of the analysis
2. Generates user-friendly response
3. Stores final response in state

**Input State**:
- `messages`: Complete conversation history
- All previous analysis

**Output State**:
- `response`: Final response to user
- `messages`: Complete conversation with final response
- `metadata.final_response`: Flag indicating completion

## Workflow Execution

### Synchronous Flow

```python
initial_state = {
    "messages": [],
    "query": "What is the current trend for AAPL stock?",
    "context": {"timeframe": "1 week"},
    "response": "",
    "metadata": {}
}

# Execute graph
final_state = await graph.ainvoke(initial_state)
```

### Asynchronous Processing

The agent uses async/await throughout:
- `ainvoke()`: Async graph execution
- `llm.ainvoke()`: Async LLM calls
- Enables concurrent processing of multiple requests

## Integration with FastAPI

### Initialization

```python
@app.on_event("startup")
async def startup_event():
    global stock_agent
    settings = get_settings()
    stock_agent = StockAgent(settings)
```

### Request Processing

```python
@app.post("/query")
async def query_agent(request: QueryRequest):
    response = await stock_agent.process_query(
        query=request.query,
        context=request.context
    )
    return QueryResponse(**response)
```

## Configuration

### LLM Settings

```python
llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.7,
    max_tokens=2000,
    openai_api_key=settings.openai_api_key
)
```

**Parameters**:
- `model`: OpenAI model to use
- `temperature`: Randomness (0-1, higher = more creative)
- `max_tokens`: Maximum response length
- `openai_api_key`: Authentication key

## Advanced Features

### State Persistence

LangGraph supports state persistence through checkpointing:
- Save intermediate states
- Resume from specific points
- Enable debugging and replay

### Conditional Edges

Add conditional routing based on state:

```python
workflow.add_conditional_edges(
    "understand_query",
    lambda state: "process" if state["confidence"] > 0.8 else "clarify"
)
```

### Tool Integration

Add external tools for data fetching:

```python
from langchain.tools import Tool

tools = [
    Tool(
        name="stock_price",
        func=get_stock_price,
        description="Get current stock price"
    )
]
```

## Error Handling

### Agent-Level Errors

```python
try:
    response = await stock_agent.process_query(query, context)
except Exception as e:
    logger.error(f"Agent error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### LLM API Errors

- Network timeouts
- Rate limiting
- Invalid API keys
- Model availability

## Performance Optimization

### Caching

```python
@lru_cache()
def get_settings():
    return Settings()
```

### Async Processing

- Use `ainvoke()` for async execution
- Enable concurrent request handling
- Reduce blocking operations

### Token Management

- Monitor token usage
- Implement token limits
- Optimize prompt length

## Monitoring and Debugging

### Metadata Tracking

Each processing step stores metadata:
- Understanding phase results
- Processing phase results
- Final response confirmation

### Graph Visualization

```python
def get_graph_structure():
    return {
        "nodes": ["understand_query", "process_query", "generate_response"],
        "edges": [...],
        "entry_point": "understand_query"
    }
```

## Best Practices

1. **State Management**: Keep state minimal and focused
2. **Node Responsibilities**: Each node should have a single purpose
3. **Error Recovery**: Implement error handling at each node
4. **Testing**: Test each node independently
5. **Logging**: Log state transitions for debugging
6. **Performance**: Monitor LLM call latency and costs

## Future Enhancements

### Potential Improvements

1. **Multi-agent Systems**: Add specialized agents for different tasks
2. **Tool Integration**: Add real-time stock data fetching
3. **Memory**: Implement conversation memory for context
4. **Streaming**: Stream responses for better UX
5. **Validation**: Add response validation nodes
6. **Human-in-the-Loop**: Enable human approval steps

### Example: Adding Real-time Data

```python
workflow.add_node("fetch_stock_data", fetch_real_time_data)
workflow.add_edge("understand_query", "fetch_stock_data")
workflow.add_edge("fetch_stock_data", "process_query")
```

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Summary

The LangGraph agent architecture provides:
- **Modularity**: Clear separation of concerns
- **Flexibility**: Easy to modify and extend
- **Observability**: Complete state tracking
- **Scalability**: Async processing for high throughput
- **Maintainability**: Well-structured codebase

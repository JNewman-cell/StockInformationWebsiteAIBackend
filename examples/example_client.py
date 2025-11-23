"""
Example client for interacting with the Stock Information AI Backend API

This script demonstrates how to use the API endpoints.
"""

import requests
import json
import sys


class StockAIClient:
    """Client for the Stock Information AI Backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url
        
    def health_check(self):
        """Check the health of the API"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def get_agent_info(self):
        """Get information about the AI agent"""
        response = requests.get(f"{self.base_url}/agent/info")
        return response.json()
    
    def query(self, query: str, context: dict = None):
        """
        Query the AI agent.
        
        Args:
            query: The question to ask
            context: Optional additional context
            
        Returns:
            The agent's response
        """
        data = {"query": query}
        if context:
            data["context"] = context
            
        response = requests.post(
            f"{self.base_url}/query",
            json=data
        )
        return response.json()


def main():
    """Main function to demonstrate API usage"""
    
    # Initialize client
    client = StockAIClient()
    
    print("=" * 60)
    print("Stock Information AI Backend - Example Client")
    print("=" * 60)
    print()
    
    # Health check
    print("1. Health Check")
    print("-" * 60)
    try:
        health = client.health_check()
        print(f"Status: {health['status']}")
        print(f"App: {health['app_name']} v{health['version']}")
        print("✅ API is healthy")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the server is running: python main.py")
        sys.exit(1)
    print()
    
    # Agent info
    print("2. Agent Information")
    print("-" * 60)
    try:
        info = client.get_agent_info()
        print(f"Model: {info['model']}")
        print(f"Temperature: {info['temperature']}")
        print(f"Max Tokens: {info['max_tokens']}")
        print(f"Status: {info['status']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Query the agent
    print("3. Query the Agent")
    print("-" * 60)
    print("Note: This requires a valid OpenAI API key in your .env file")
    print()
    
    # Example queries
    example_queries = [
        {
            "query": "What is the current trend for AAPL stock?",
            "context": {"timeframe": "1 week"}
        },
        {
            "query": "Compare the performance of TSLA and NIO",
            "context": {"metrics": ["price", "volume"]}
        },
        {
            "query": "What are the best tech stocks to watch?",
            "context": None
        }
    ]
    
    for i, example in enumerate(example_queries, 1):
        print(f"Example {i}:")
        print(f"  Query: {example['query']}")
        if example['context']:
            print(f"  Context: {json.dumps(example['context'])}")
        print()
    
    # Interactive mode
    print("4. Interactive Mode")
    print("-" * 60)
    print("You can now ask questions (or press Ctrl+C to exit)")
    print()
    
    try:
        while True:
            query_text = input("Your question: ").strip()
            if not query_text:
                continue
                
            print("\nQuerying agent...")
            try:
                result = client.query(query_text)
                print("\n📝 Response:")
                print(result['response'])
                print()
            except requests.exceptions.HTTPError as e:
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code == 503:
                        print("❌ Agent not properly initialized. Check your OpenAI API key.")
                    else:
                        print(f"❌ HTTP Error {e.response.status_code}: {e}")
                else:
                    print(f"❌ HTTP Error: {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
            print()
            
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
        sys.exit(0)


if __name__ == "__main__":
    main()

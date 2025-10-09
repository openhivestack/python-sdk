# OpenHive (Python SDK)

The official core library for building agents on the H.I.V.E. Protocol in Python.
This package provides the essential tools to bootstrap a protocol-compliant agent, handle secure messaging, and manage agent capabilities, with a focus on developer experience and flexibility.

## Features

- **High-Level Agent Class**: A simple, powerful `Agent` class to get started in minutes.
- **Flexible Deployment**: A decoupled `AgentServer` (using FastAPI) allows you to run the agent as a standalone server or integrate its logic into existing frameworks.
- **Service Discovery**: Built-in support for an `AgentRegistry` for discovering and communicating with other agents.
- **Simplified Agent Communication**: A high-level `send_task` method for easy and secure agent-to-agent communication.
- **Protocol Compliance**: Built-in, protocol-compliant message creation, validation, and cryptographic handling (Ed25519).
- **Configuration-Driven**: Easily configure your agent using a `.hive.yml` or JSON file.

## Installation

```bash
pip install openhive
```

## Quick Start

Here's how to create a complete, server-based agent in just a few steps.

### 1. Configure Your Agent

Create a `.hive.yml` file in your project root:

```yaml
id: "hive:agentid:hello-world-agent-py"
name: "HelloWorldAgentPy"
description: "A simple Python agent that provides greetings."
version: "0.1.0"
endpoint: "http://localhost:11200"

capabilities:
  - id: "hello-world-python"
    description: "Returns a greeting for a given name."
    input:
      name: "string"
    output:
      response: "string"
```

### 2. Create Your Agent File

Create a `main.py` file:

```python
import asyncio
from openhive import Agent, Config

async def main():
    # 1. Load agent configuration from .hive.yml
    config = Config.from_yaml('.hive.yml')

    # 2. Create a new agent instance
    agent = Agent(config)

    # 3. Define and register a handler for the 'hello-world-python' capability
    #    You can use the decorator style for cleaner code.
    @agent.capability("hello-world-python")
    async def hello_world(params: dict):
        name = params.get("name")
        if not name:
            raise ValueError("The 'name' parameter is required.")
        return {"response": f"Hello, {name}!"}

    # 4. Register the agent in the network (optional, for discovery)
    await agent.register()

    print(f"Agent {agent.identity.id()} registered with capabilities.")

    # 5. Create and start the HTTP server
    server = agent.create_server()
    # server.start() is blocking, so you might run it in a separate process
    # or use an ASGI server like uvicorn directly for more control.
    print(f"Server starting at {agent.get_endpoint()}")
    # For this example, we won't block with server.start()
    # In a real application, you would run the server.

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Run Your Agent

You can now run your `main.py` file. Your agent will start an HTTP server on the specified endpoint and be ready to accept `task_request` messages.

## Registering Capabilities

You can register capabilities in two ways:

### 1. Using the Decorator (Recommended)

```python
@agent.capability("my-capability")
async def my_handler(params: dict):
    # ... handler logic ...
    return {"result": "done"}
```

### 2. Using a Direct Function Call

This is useful for registering handlers dynamically.

```python
async def another_handler(params: dict):
    # ... handler logic ...
    return {"result": "done"}

agent.capability("another-capability", another_handler)
```

## Communicating with Other Agents

The SDK makes it simple to communicate with other agents using the `send_task` method, which handles discovery, message creation, signing, and response verification.

```python
import asyncio
from openhive import Agent, Config, InMemoryRegistry
from openhive.types import AgentInfo

async def communicate():
    # --- Agent 1 Setup ---
    config1 = Config.from_yaml('agent1.yml')
    agent1 = Agent(config1)

    @agent1.capability("echo")
    async def echo(params: dict):
        return {"echo": params}


    # --- Agent 2 Setup ---
    config2 = Config.from_yaml('agent2.yml')
    agent2 = Agent(config2)


    # --- Communication ---
    # Agents can share a registry for discovery
    registry = InMemoryRegistry()

    agent1_info = AgentInfo(**agent1.config.info(), publicKey=agent1.identity.get_public_key_b64())
    await registry.add(agent1_info)
    agent2_info = AgentInfo(**agent2.config.info(), publicKey=agent2.identity.get_public_key_b64())
    await registry.add(agent2_info)

    agent1.registry = registry
    agent2.registry = registry # Inject registry

    # Agent 2 sends a task to Agent 1
    result = await agent2.send_task(
        to_agent_id=agent1.identity.id(),
        capability="echo",
        params={"message": "Hello from Agent 2"}
    )

    print("Response from Agent 1:", result)

if __name__ == "__main__":
    # You would need agent1.yml and agent2.yml files for this example.
    # asyncio.run(communicate())
    pass
```

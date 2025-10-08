# OpenHive (Python SDK)

The official core library for building agents on the H.I.V.E. Protocol in Python.
This package provides the essential tools to bootstrap a protocol-compliant agent, handle secure messaging, and manage agent capabilities, with a focus on developer experience and flexibility.

## Features

- **High-Level Agent Class**: A simple, powerful `Agent` class to get started in minutes.
- **Flexible Deployment**: A decoupled `AgentServer` (using FastAPI) allows you to run the agent as a standalone server or integrate its logic into existing frameworks.
- **Simplified Capability Management**: An intuitive decorator for registering handlers for your agent's skills.
- **Protocol Compliance**: Built-in, protocol-compliant message creation, validation, and cryptographic handling (Ed25519).
- **Configuration-Driven**: Easily configure your agent using a `.hive.yml` file.

## Installation

```bash
pip install openhive
```

## Quick Start

Here's how to create a complete, server-based agent in just a few steps.

### 1. Configure Your Agent

Create a `.hive.yml` file in your project root:

```yaml
id: 'hive:agentid:hello-world-agent-py'
name: 'HelloWorldAgentPy'
description: 'A simple Python agent that provides greetings.'
version: '0.1.0'
port: 11200

capabilities:
  - id: 'hello-world-python'
    description: 'Returns a greeting for a given name.'
    input:
      name: 'string'
    output:
      response: 'string'
```

### 2. Create Your Agent File

Create a `main.py` file:

```python
from openhive import Agent, Config

# 1. Load agent configuration from .hive.yml
config = Config()

# 2. Create a new agent instance
agent = Agent(config)

# 3. Register a handler for the 'hello-world-python' capability
@agent.capability("hello-world-python")
async def hello_world(params: dict):
    name = params.get("name")
    if not name:
        raise ValueError("The 'name' parameter is required.")

    # Return the result directly
    return {"response": f"Hello, {name}!"}

# 4. Create and start the HTTP server
if __name__ == "__main__":
    server = agent.create_server()
    server.start()
    # Agent is now running and ready for tasks.
```

### 3. Run Your Agent

You can now run your `main.py` file. Your agent will start an HTTP server on port `11200` and be ready to accept `task_request` messages.

## Advanced Usage

### Integrating with Existing Frameworks (e.g., FastAPI)

The `Agent` class is decoupled from the HTTP server, allowing you to integrate it into your own application.

```python
from fastapi import FastAPI
from openhive import Agent, Config

# Agent setup is the same as above
config = Config()
agent = Agent(config)
# ... register capabilities ...

app = FastAPI()

@app.post("/tasks")
async def handle_tasks(message: dict):
    # You are responsible for peer public key management
    sender_public_key = get_public_key_for_agent(message.get("from"))

    response_data = await agent.handle_task_request(message, sender_public_key)

    # You are responsible for creating and signing the response message
    response_message = create_and_sign_response_message(response_data)

    # Return the signed message
    return response_message
```

### Communicating with Other Agents

Configure peers to enable agent-to-agent communication. The public and private keys are raw bytes.

```python
# Add a peer agent's public key (as raw bytes)
agent.add_peer("hive:agentid:some-peer-id", b'peer-public-key-bytes')

# Get the agent's identity to create messages
identity = agent.get_identity()

# Create a task request message to send to the peer
task_request = identity.createTaskRequest(
  "hive:agentid:some-peer-id",
  "some-capability",
  {"parameter": "value"}
)

# Now you can send this `task_request` dictionary to the peer's /tasks endpoint.
```

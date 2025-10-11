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

Create a `.hive.yml` file in your project root. This file is the single source of truth for your agent's identity and configuration.

The configuration loader supports environment variable substitution using Jinja2 syntax. It automatically loads variables from a `.env` file in your project root.

```yaml
id: "hive:agentid:hello-world-agent-py"
name: "HelloWorldAgentPy"
description: "A simple Python agent that provides greetings."
version: "0.1.0"
endpoint: "http://localhost:11200"

# Agent's cryptographic keys.
# It's highly recommended to load the private key from an environment variable.
keys:
  publicKey: "base64_encoded_public_key"
  privateKey: "{{ env.HIVE_AGENT_PRIVATE_KEY }}"

capabilities:
  - id: "hello-world-python"
    description: "Returns a greeting for a given name."
    input:
      name: "string"
    output:
      response: "string"
```

Place your `HIVE_AGENT_PRIVATE_KEY` in a `.env` file:

```
HIVE_AGENT_PRIVATE_KEY=your_base64_encoded_private_key
```

### 2. Create Your Agent File

Create a `main.py` file:

```python
import asyncio
from openhive import Agent, AgentConfig

async def main():
    # 1. Load agent configuration from .hive.yml
    agent_config = AgentConfig.from_yaml('.hive.yml')

    # 2. Create a new agent instance
    agent = Agent(agent_config)

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

## Agent as a Registry

The `AgentServer` now includes a full set of RESTful endpoints that expose the agent's internal registry, allowing any agent to serve as a discovery hub for a cluster of other agents. This enables agents to dynamically register, deregister, and discover each other over the network.

### Registry API Endpoints

- `POST /registry/add`: Registers an agent. The request body should be an `AgentInfo` object.
- `GET /registry`: Returns a list of all registered agents.
- `GET /registry/{agent_id}`: Retrieves the details of a single agent by its ID.
- `DELETE /registry/{agent_id}`: Removes an agent from the registry.

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

The SDK makes it simple to communicate with other agents using the `send_task` method. For agents to communicate, they must first discover each other. The following example demonstrates a realistic scenario with three agents forming a cluster: one agent acts as a central registry, while the other two register with it and then communicate.

This example assumes you have three separate terminal sessions and the necessary `.hive.yml` and `.env` files for each agent.

### 1. The Registry Agent

This agent's only job is to run and serve as the discovery server for the cluster.

**`registry_agent.py`**

```python
import uvicorn
from openhive import Agent

# Create a .hive.yml for this agent listening on port 11200
# It needs an ID, keys, etc., but no capabilities are required.

if __name__ == "__main__":
    registry_agent = Agent()
    server = registry_agent.create_server()
    print(f"Registry agent is running at {registry_agent.endpoint()}")
    uvicorn.run(server.app, host="0.0.0.0", port=11200)
```

Run this agent in your first terminal: `python registry_agent.py`

### 2. The Responder Agent

This agent provides a `greet` capability and registers itself with the Registry Agent upon startup.

**`responder_agent.py`**

```python
import asyncio
import httpx
import uvicorn
from openhive import Agent

# Create a .hive.yml for this agent listening on port 11201
# with a capability called 'greet'.

REGISTRY_ENDPOINT = "http://localhost:11200"

responder_agent = Agent()

@responder_agent.capability("greet")
async def greet(params: dict):
    return {"message": f"Hello, {params.get('name')}!"}

async def startup():
    await responder_agent.register(REGISTRY_ENDPOINT)
    print("Responder agent registered successfully.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup())

    server = responder_agent.create_server()
    print(f"Responder agent is running at {responder_agent.endpoint()}")
    uvicorn.run(server.app, host="0.0.0.0", port=11201)
```

Run this agent in your second terminal: `python responder_agent.py`

### 3. The Requester Agent

This agent sends a task to the Responder Agent after discovering it via the Registry Agent.

**`requester_agent.py`**

```python
import asyncio
from openhive import Agent

# Create a .hive.yml for this agent listening on port 11202

REGISTRY_ENDPOINT = "http://localhost:11200"

async def main():
    requester_agent = Agent()

    # Register itself with the registry agent
    await requester_agent.register(REGISTRY_ENDPOINT)

    # 1. Search for agents with the 'greet' capability
    print("Searching for agents with 'greet' capability...")
    search_results = await requester_agent.search(
        "capability:greet", REGISTRY_ENDPOINT
    )

    if not search_results:
        print("No agents found with the 'greet' capability.")
        return

    responder_info = search_results[0]
    print(f"Found responder agent: {responder_info.id}")

    # 2. Add the discovered agent to its local registry
    await requester_agent.registry.add(responder_info)

    # 3. Now, send the task
    print("Requester sending 'greet' task to responder...")
    result = await requester_agent.send_task(
        to_agent_id=responder_info.id,
        capability="greet",
        params={"name": "World"}
    )

    print("Requester received response:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

Run this in a third terminal: `python requester_agent.py`. You should see the successful task exchange!

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) to get started.

## ⚖️ Licensing

This project is made available under a Dual License model.

### 1. Open Source License (AGPLv3)

The code in this repository is primarily licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.

The AGPLv3 is a strong copyleft license. This means you are free to use, modify, and distribute this software, but if you run a modified version of the software as a public network service (Software as a Service, or SaaS), you must offer the source code of your modified version to your users.

**See the [LICENSE.md](LICENSE.md) file for full details.**

### 2. Commercial License (Proprietary)

If you are an organization that needs to use this software in a proprietary, closed-source product, or if you cannot comply with the AGPLv3's copyleft requirements, you must purchase a **Commercial License**.

For licensing inquiries, please contact us at: **[commercial@openhive.sh]**

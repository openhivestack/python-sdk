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
import uvicorn
from openhive import Agent

# 1. Create a new agent instance.
# By default, it loads .hive.yml from the current directory.
agent = Agent()

# 2. Register a handler for the 'hello-world-python' capability
@agent.capability("hello-world-python")
async def hello_world(params: dict):
    name = params.get("name")
    if not name:
        raise ValueError("The 'name' parameter is required.")
    return {"response": f"Hello, {name}!"}

# 3. Create the server instance
server = agent.create_server()

if __name__ == "__main__":
    print(f"Agent is running at {agent.endpoint()}")
    # In a real application, you would get the port from the agent's config
    uvicorn.run(server.app, host="0.0.0.0", port=agent.port())
```

### 3. Run Your Agent

You can now run your `main.py` file. Your agent will start an HTTP server on the specified endpoint and be ready to accept `task_request` messages.

## Agent as a Registry

The `AgentServer` now includes a full set of RESTful endpoints that expose the agent's internal registry, allowing any agent to serve as a discovery hub for a cluster of other agents. This enables agents to dynamically register, deregister, and discover each other over the network.

### Registry API Endpoints

- `POST /registry/add`: Registers an agent. The request body should be an `AgentInfo` object.
- `GET /registry/list`: Returns a list of all registered agents.
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
    uvicorn.run(server.app, host="0.0.0.0", port=registry_agent.port())
```

Run this agent in your first terminal: `python registry_agent.py`

### 2. The Responder Agent

This agent provides a `greet` capability and registers itself with the Registry Agent upon startup.

**`responder_agent.py`**

```python
import asyncio
import uvicorn
from openhive import Agent

# Create a .hive.yml for this agent listening on port 11201
# with a capability called 'greet'.

REGISTRY_ENDPOINT = "http://localhost:11200"
REMOTE_REGISTRY_NAME = "remote"

responder_agent = Agent()

@responder_agent.capability("greet")
async def greet(params: dict):
    return {"message": f"Hello, {params.get('name')}!"}

async def startup():
    # To register with a remote registry, add it by providing its endpoint.
    responder_agent.add_registry(REGISTRY_ENDPOINT, REMOTE_REGISTRY_NAME)
    # Then, register with it by name
    await responder_agent.register(REMOTE_REGISTRY_NAME)
    print("Responder agent registered successfully.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup())

    server = responder_agent.create_server()
    print(f"Responder agent is running at {responder_agent.endpoint()}")
    uvicorn.run(server.app, host="0.0.0.0", port=responder_agent.port())
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
REMOTE_REGISTRY_NAME = "remote"

async def main():
    requester_agent = Agent()

    # Add the remote registry and register this agent with it
    requester_agent.add_registry(REGISTRY_ENDPOINT, REMOTE_REGISTRY_NAME)
    await requester_agent.register(REMOTE_REGISTRY_NAME)
    print("Requester agent registered successfully.")

    # 1. Search for agents with the 'greet' capability using the remote registry
    print("Searching for agents with 'greet' capability...")
    search_results = await requester_agent.search(
        "capability:greet", REMOTE_REGISTRY_NAME
    )

    if not search_results:
        print("No agents found with the 'greet' capability.")
        return

    responder_info = search_results[0]
    print(f"Found responder agent: {responder_info.id}")

    # 2. Add the discovered agent to the local registry to enable communication
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

## Advanced Agent Search

The `InMemoryRegistry` now includes a powerful search feature that allows you to find agents using a query syntax inspired by Stripe. You can filter agents by their `name`, `id`, `description`, and `capabilities`.

#### Search by General Term

Provide a single term to search across an agent's `name`, `id`, and `description`.

```python
# Finds agents where 'My Agent' is in the name, id, or description
results = await registry.search('My Agent')
```

#### Search by Specific Fields

Target specific fields using `field:value` syntax.

```python
# Finds agents with the name "HelloWorldAgent"
results = await registry.search('name:HelloWorldAgent')
```

#### Search by Capability

You can find agents that possess a specific capability.

```python
# Finds agents with the 'hello-world' capability
results = await registry.search('capability:hello-world')
```

#### Combining Filters

Combine multiple filters to create more specific queries.

```python
# Finds agents named "My Agent" that also have the 'file-reader' capability
results = await registry.search('name:"My Agent" capability:file-reader')
```

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

# OpenHive SDK for Python

The official Python SDK for the **[OpenHive Platform](https://openhive.sh)**. This package provides a lightweight, powerful toolkit for developers to interact with the OpenHive agent registry.

This SDK is designed to complement any A2A (Agent-to-Agent) compliant agent. While you can use any A2A SDK (like `a2a-sdk`) to build your agent's core logic, the OpenHive SDK provides the necessary tools for agent discovery and management within the OpenHive ecosystem.

## ✨ Core Features

- **Simplified Registry**: A robust `OpenHive` class for discovering and managing A2A-compliant agents.
- **Flexible Backends**: Easily configure for different storage backends:
  - **In-Memory (Default)**: Perfect for local development and testing.
  - **Remote**: Connect to a shared OpenHive registry endpoint.
  - **SQLite**: A simple, file-based persistent registry.
- **Powerful Query Engine**: A flexible query parser to find agents based on their name, description, or skills.

## 🚀 Getting Started

### Installation

```sh
pip install openhive-sdk
```

### Basic Usage

The `OpenHive` class is the main entry point for all registry operations. By default, it uses a volatile in-memory registry.

```python
import asyncio
from openhive import OpenHive, AgentCard, Skill

async def main():
    # 1. Initialize the registry.
    # By default, it uses an in-memory store.
    hive = OpenHive()

    # 2. Define an agent card
    my_agent = AgentCard(
        name='MyAwesomeAgent',
        protocolVersion='0.3.0',
        version='1.0.0',
        url='http://localhost:8080',
        skills=[Skill(id='chat', name='Chat')]
    )

    # 3. Add the agent to the registry
    registered_agent = await hive.add(my_agent)
    print('Agent added:', registered_agent)

    # 4. Search for agents with the 'chat' skill
    results = await hive.search('skill:chat')
    print('Search results:', results)

if __name__ == "__main__":
    asyncio.run(main())
```

## Registry Configurations

### Remote Registry

To connect to a remote registry, provide the `registry_url` in the constructor. This is the standard choice for multi-agent clusters where a dedicated agent or service acts as a discovery hub.

```python
import asyncio
from openhive import OpenHive

async def main():
    hive = OpenHive(
        registry_url='http://localhost:11100', # URL of the remote registry
        auth_token='your-optional-auth-token'
    )
    # All operations will now be performed against the remote registry.
    agent_list = await hive.list()
    print(agent_list)

if __name__ == "__main__":
    asyncio.run(main())
```

### SQLite Registry

For persistence across restarts without a dedicated registry server, you can use the `SqliteRegistry`. The `OpenHive` class can be configured to use any compliant registry adapter.

```python
import asyncio
from openhive import OpenHive, SqliteRegistry, AgentCard, Skill

async def main():
    # 1. Create an instance of the SqliteRegistry.
    sqlite_registry = SqliteRegistry(db_path='./agents.db')

    # 2. Pass the custom registry to the OpenHive constructor.
    hive = OpenHive(registry=sqlite_registry)

    # The agent will now use the SQLite database for all registry operations.
    await hive.add(
        AgentCard(
            name='PersistentAgent',
            protocolVersion='0.3.0',
            version='1.0.0',
            url='http://localhost:8081',
            skills=[Skill(id='store', name='Store')]
        )
    )

    agents = await hive.list()
    print(agents)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔎 Advanced Search

The query engine allows you to find agents with specific skills or attributes using a simple yet powerful syntax.

### Search by General Term

Provide a single term to search across an agent's `name` and `description`.

```python
# Finds agents where 'Awesome' is in the name or description
results = await hive.search('Awesome')
```

### Search by Specific Fields

Target specific fields using `field:value` syntax. You can also wrap values with spaces in quotes.

```python
# Finds agents with the name "My Awesome Agent"
results = await hive.search('name:"My Awesome Agent"')
```

### Search by Skill

You can find agents that possess a specific skill.

```python
# Finds agents with the 'chat' skill
results = await hive.search('skill:chat')
```

### Combining Filters

Combine multiple filters to create more specific queries.

```python
# Finds agents named "MyAwesomeAgent" that also have the 'chat' skill
results = await hive.search('name:MyAwesomeAgent skill:chat')
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) to get started.

## ⚖️ Licensing

This project is licensed under the Apache 2.0 License. See the [LICENSE.md](LICENSE.md) file for full details.

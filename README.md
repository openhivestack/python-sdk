# OpenHive SDK for Python

The official Python SDK for the **[OpenHive Platform](https://openhive.sh)**. This package provides a lightweight, powerful toolkit for developers to interact with the OpenHive agent registry.

This SDK is designed to complement any A2A (Agent-to-Agent) compliant agent. While you can use any A2A SDK (like `a2a-sdk`) to build your agent's core logic, the OpenHive SDK provides the necessary tools for agent discovery and management within the OpenHive ecosystem.

## ✨ Core Features

- **Agent Registry**: A robust `AgentRegistry` class for discovering and managing A2A-compliant agents.
- **Adapter Pattern**: Easily switch between different storage backends for your registry:
    - `InMemoryRegistry`: Perfect for local development and testing.
    - `RemoteRegistry`: Connect to a shared OpenHive registry endpoint.
    - `SqliteRegistry`: A simple, file-based persistent registry using Python's built-in `sqlite3`.
- **Powerful Query Engine**: A flexible query parser to find agents based on their name, description, or skills.

## 🚀 Getting Started

1. **Installation:**

   ```sh
   pip install openhive-sdk
   ```

2. **Basic Usage (In-Memory Registry):**

   ```python
   import asyncio
   from openhive import AgentRegistry, InMemoryRegistry, AgentCard, Skill

   async def main():
       # 1. Initialize the registry with an adapter
       registry = AgentRegistry(InMemoryRegistry())

       # 2. Define an agent
       my_agent = AgentCard(
           name='MyAwesomeAgent',
           protocolVersion='0.3.0',
           version='1.0.0',
           url='http://localhost:8080',
           skills=[Skill(id='chat', name='Chat')]
       )

       # 3. Add the agent to the registry
       await registry.add(my_agent)

       # 4. Search for agents
       results = await registry.search('chat')
       print(results)

   if __name__ == "__main__":
       asyncio.run(main())
   ```

## 🔎 Advanced Search

The query engine allows you to find agents with specific skills or attributes.

```python
# Find agents with the 'chat' skill
chat_agents = await registry.search('skill:chat')

# Find agents with "My" in their name or description
my_agents = await registry.search('My')
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) to get started.

## ⚖️ Licensing

This project is licensed under the Apache 2.0 License. See the [LICENSE.md](LICENSE.md) file for full details.

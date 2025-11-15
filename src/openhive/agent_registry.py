from abc import ABC, abstractmethod
from typing import List, Optional

from .types import AgentRegistryEntry
from .query_parser import QueryParser
from .log import get_logger

log = get_logger(__name__)


class AgentRegistryAdapter(ABC):
    @abstractmethod
    async def add(self, agent: AgentRegistryEntry) -> AgentRegistryEntry:
        pass

    @abstractmethod
    async def get(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        pass

    @abstractmethod
    async def remove(self, agent_id: str) -> None:
        pass

    @abstractmethod
    async def list(self) -> List[AgentRegistryEntry]:
        pass

    @abstractmethod
    async def search(self, query: str) -> List[AgentRegistryEntry]:
        pass

    @abstractmethod
    async def update(self, agent_id: str, agent: AgentRegistryEntry) -> AgentRegistryEntry:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass


class AgentRegistry:
    def __init__(self, adapter: AgentRegistryAdapter):
        self._adapter = adapter

    async def add(self, agent: AgentRegistryEntry) -> AgentRegistryEntry:
        if not agent.name or not agent.url:
            raise ValueError("Agent name and URL are required.")
        return await self._adapter.add(agent)

    async def get(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        return await self._adapter.get(agent_id)

    async def remove(self, agent_id: str) -> None:
        await self._adapter.remove(agent_id)

    async def list(self) -> List[AgentRegistryEntry]:
        return await self._adapter.list()

    async def search(self, query: str) -> List[AgentRegistryEntry]:
        return await self._adapter.search(query)
    
    async def update(self, agent_id: str, agent: AgentRegistryEntry) -> AgentRegistryEntry:
        return await self._adapter.update(agent_id, agent)

    async def clear(self) -> None:
        await self._adapter.clear()

    async def close(self) -> None:
        await self._adapter.close()

    @property
    def adapter(self) -> AgentRegistryAdapter:
        return self._adapter

class InMemoryRegistry(AgentRegistryAdapter):
    def __init__(self):
        self._agents: dict[str, AgentRegistryEntry] = {}
        log.info("In-memory registry initialized")

    async def add(self, agent: AgentRegistryEntry) -> AgentRegistryEntry:
        agent_id = agent.name
        log.info(f"Adding agent {agent_id} to in-memory registry")
        if agent_id in self._agents:
            raise ValueError(f"Agent with name {agent_id} already exists.")
        self._agents[agent_id] = agent
        return agent

    async def get(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        log.info(f"Getting agent {agent_id} from in-memory registry")
        return self._agents.get(agent_id)

    async def remove(self, agent_id: str) -> None:
        log.info(f"Removing agent {agent_id} from in-memory registry")
        if agent_id in self._agents:
            del self._agents[agent_id]

    async def list(self) -> List[AgentRegistryEntry]:
        log.info("Listing all agents in in-memory registry")
        return list(self._agents.values())

    async def update(self, agent_id: str, agent_update: AgentRegistryEntry) -> AgentRegistryEntry:
        log.info(f"Updating agent {agent_id} in in-memory registry")
        if agent_id not in self._agents:
            raise ValueError(f"Agent with name {agent_id} not found.")
        self._agents[agent_id] = agent_update
        return agent_update

    async def search(self, query: str) -> List[AgentRegistryEntry]:
        log.info(f"Searching for '{query}' in in-memory registry")
        agents = list(self._agents.values())

        if not query or not query.strip():
            return agents

        parsed_query = QueryParser.parse(query)

        if not parsed_query.field_filters and not parsed_query.general_filters:
            return agents

        # Apply field filters
        for f in parsed_query.field_filters:
            if f.operator == 'has_skill':
                agents = [
                    agent for agent in agents
                    if any(
                        s.id.lower() == f.value.lower() or s.name.lower() == f.value.lower()
                        for s in agent.skills
                    )
                ]
            else:
                agents = [
                    agent for agent in agents
                    if hasattr(agent, f.field) and f.value.lower() in str(getattr(agent, f.field)).lower()
                ]

        # Apply general text search filters
        for f in parsed_query.general_filters:
            agents = [
                agent for agent in agents
                if any(
                    hasattr(agent, field) and f.term.lower() in str(getattr(agent, field)).lower()
                    for field in f.fields
                )
            ]
        
        log.info(f"Search for '{query}' returned {len(agents)} results")
        return agents

    async def clear(self) -> None:
        log.info("Clearing all agents from in-memory registry")
        self._agents.clear()

    async def close(self) -> None:
        log.info("Closing in-memory registry")
        self._agents.clear()

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
        parsed_query = QueryParser.parse(query)
        agents = list(self._agents.values())

        if not query or not query.strip():
            log.info("Empty query, returning all agents")
            return agents

        def matches(agent: AgentRegistryEntry) -> bool:
            general_match = (
                not parsed_query.general_filters or
                all(
                    any(
                        filter.term.lower() in getattr(agent, field, '' if getattr(agent, field, None) is not None else None).lower()
                        for field in filter.fields
                        if isinstance(getattr(agent, field, None), str)
                    )
                    for filter in parsed_query.general_filters
                )
            )

            field_match = (
                not parsed_query.field_filters or
                all(
                    (
                        filter.value.lower() in getattr(agent, filter.field, '' if getattr(agent, filter.field, None) is not None else None).lower()
                        if filter.operator == 'includes' and isinstance(getattr(agent, filter.field, None), str)
                        else any(
                            s.id.lower() == filter.value.lower() or s.name.lower() == filter.value.lower()
                            for s in agent.skills
                        )
                    )
                    for filter in parsed_query.field_filters
                )
            )

            return general_match and field_match

        results = [agent for agent in agents if matches(agent)]
        log.info(f"Search for '{query}' returned {len(results)} results")
        return results

    async def clear(self) -> None:
        log.info("Clearing all agents from in-memory registry")
        self._agents.clear()

    async def close(self) -> None:
        log.info("Closing in-memory registry")
        self._agents.clear()

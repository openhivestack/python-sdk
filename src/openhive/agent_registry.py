from abc import ABC, abstractmethod
from typing import List, Optional
import uuid

from .types import AgentCard
from .query_parser import QueryParser
from .log import get_logger

log = get_logger(__name__)


class AgentRegistry(ABC):
    @abstractmethod
    async def add(self, agent: AgentCard, *args, **kwargs) -> AgentCard:
        pass

    @abstractmethod
    async def get(self, agent_name: str, *args, **kwargs) -> Optional[AgentCard]:
        pass

    @abstractmethod
    async def delete(self, agent_name: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    async def list(self, *args, **kwargs) -> List[AgentCard]:
        pass

    @abstractmethod
    async def search(self, query: str, *args, **kwargs) -> List[AgentCard]:
        pass

    @abstractmethod
    async def update(self, agent_name: str, agent: AgentCard, *args, **kwargs) -> AgentCard:
        pass

    @abstractmethod
    async def clear(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    async def close(self, *args, **kwargs) -> None:
        pass


class InMemoryRegistry(AgentRegistry):
    def __init__(self, query_parser: Optional[QueryParser] = None):
        self._agents: dict[str, AgentCard] = {}
        self._query_parser = query_parser or QueryParser()
        log.info("In-memory registry initialized")

    async def add(self, agent: AgentCard, *args, **kwargs) -> AgentCard:
        # Ensure name is unique
        if agent.name in self._agents:
            raise ValueError(f"Agent with name {agent.name} already exists.")

        log.info(f"Adding agent {agent.name} to in-memory registry")
        self._agents[agent.name] = agent
        return agent

    async def get(self, agent_name: str, *args, **kwargs) -> Optional[AgentCard]:
        log.info(f"Getting agent {agent_name} from in-memory registry")
        return self._agents.get(agent_name)

    async def delete(self, agent_name: str, *args, **kwargs) -> None:
        log.info(f"Removing agent {agent_name} from in-memory registry")
        if agent_name in self._agents:
            del self._agents[agent_name]

    async def list(self, *args, **kwargs) -> List[AgentCard]:
        log.info("Listing all agents in in-memory registry")
        return list(self._agents.values())

    async def update(self, agent_name: str, agent_update: AgentCard, *args, **kwargs) -> AgentCard:
        log.info(f"Updating agent {agent_name} in in-memory registry")
        if agent_name not in self._agents:
            raise ValueError(f"Agent with name {agent_name} not found.")
        self._agents[agent_name] = agent_update
        return agent_update

    async def search(self, query: str, *args, **kwargs) -> List[AgentCard]:
        log.info(f"Searching for '{query}' in in-memory registry")
        agents = list(self._agents.values())

        if not query or not query.strip():
            return agents

        parsed_query = self._query_parser.parse(query)

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

    async def clear(self, *args, **kwargs) -> None:
        log.info("Clearing all agents from in-memory registry")
        self._agents.clear()

    async def close(self, *args, **kwargs) -> None:
        log.info("Closing in-memory registry")
        self._agents.clear()

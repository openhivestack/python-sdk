from abc import ABC, abstractmethod
from typing import List, Optional

from .types import AgentInfo
from .query_parser import QueryParser
from .log import get_logger

log = get_logger(__name__)


class AgentRegistry(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def endpoint(self) -> str:
        pass

    @abstractmethod
    async def add(self, agent_info: AgentInfo):
        pass

    @abstractmethod
    async def get(self, agent_id: str) -> Optional[AgentInfo]:
        pass

    @abstractmethod
    async def remove(self, agent_id: str):
        pass

    @abstractmethod
    async def list(self) -> List[AgentInfo]:
        pass

    @abstractmethod
    async def search(self, query: str) -> List[AgentInfo]:
        pass
    
    @abstractmethod
    async def update(self, agent_info: AgentInfo):
        pass


class InMemoryRegistry(AgentRegistry):
    def __init__(self, name: str, endpoint: str):
        self._name = name
        self._endpoint = endpoint
        self._agents: dict[str, AgentInfo] = {}
        log.info(f"In-memory registry '{name}' initialized")

    @property
    def name(self) -> str:
        return self._name

    @property
    def endpoint(self) -> str:
        return self._endpoint
    
    async def add(self, agent_info: AgentInfo):
        log.info(f"Adding agent {agent_info.id} to registry '{self.name}'")
        self._agents[agent_info.id] = agent_info

    async def get(self, agent_id: str) -> Optional[AgentInfo]:
        log.info(f"Getting agent {agent_id} from registry '{self.name}'")
        agent = self._agents.get(agent_id)
        if not agent:
            log.warning(f"Agent {agent_id} not found in registry '{self.name}'")
        return agent

    async def remove(self, agent_id: str):
        log.info(f"Removing agent {agent_id} from registry '{self.name}'")
        if agent_id in self._agents:
            del self._agents[agent_id]

    async def list(self) -> List[AgentInfo]:
        log.info(f"Listing all agents in registry '{self.name}'")
        return list(self._agents.values())

    async def update(self, agent_info: AgentInfo):
        log.info(f"Updating agent {agent_info.id} in registry '{self.name}'")
        if agent_info.id in self._agents:
            self._agents[agent_info.id] = agent_info

    async def search(self, query: str) -> List[AgentInfo]:
        log.info(f"Searching for '{query}' in registry '{self.name}'")
        parsed_query = QueryParser.parse(query)
        agents = list(self._agents.values())

        if not query or not query.strip():
            log.info("Empty query, returning all agents")
            return agents

        def matches(agent: AgentInfo) -> bool:
            general_match = (
                not parsed_query.general_filters or
                all(
                    any(
                        filter.term.lower() in getattr(agent, field, '').lower()
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
                        filter.value.lower() in getattr(agent, filter.field, '').lower()
                        if filter.operator == 'includes' and isinstance(getattr(agent, filter.field, None), str)
                        else any(
                            cap.id.lower() == filter.value.lower()
                            for cap in agent.capabilities
                        )
                    )
                    for filter in parsed_query.field_filters
                )
            )

            return general_match and field_match

        results = [agent for agent in agents if matches(agent)]
        log.info(f"Search for '{query}' returned {len(results)} results")
        return results

from abc import ABC, abstractmethod
from typing import List, Optional
from .types import AgentInfo
from .query_parser import QueryParser


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

    @property
    def name(self) -> str:
        return self._name

    @property
    def endpoint(self) -> str:
        return self._endpoint
    
    async def add(self, agent_info: AgentInfo):
        self._agents[agent_info.id] = agent_info

    async def get(self, agent_id: str) -> Optional[AgentInfo]:
        return self._agents.get(agent_id)

    async def remove(self, agent_id: str):
        if agent_id in self._agents:
            del self._agents[agent_id]

    async def list(self) -> List[AgentInfo]:
        return list(self._agents.values())

    async def update(self, agent_info: AgentInfo):
        if agent_info.id in self._agents:
            self._agents[agent_info.id] = agent_info

    async def search(self, query: str) -> List[AgentInfo]:
        parsed_query = QueryParser.parse(query)
        agents = list(self._agents.values())

        if not query or not query.strip():
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

        return [agent for agent in agents if matches(agent)]

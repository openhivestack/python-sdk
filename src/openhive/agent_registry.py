from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

from .types import AgentCard
from .query_parser import QueryParser
from .log import get_logger

log = get_logger(__name__)

T = TypeVar('T')


class AgentRegistry(ABC, Generic[T]):
    @abstractmethod
    async def add(self, agent: AgentCard, *args, **kwargs) -> T:
        pass

    @abstractmethod
    async def get(self, agent_name: str, *args, **kwargs) -> Optional[T]:
        pass

    @abstractmethod
    async def delete(self, agent_name: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    async def list(self, *args, **kwargs) -> List[T]:
        pass

    @abstractmethod
    async def search(self, query: str, *args, **kwargs) -> List[T]:
        pass

    @abstractmethod
    async def update(self, agent_name: str, agent: AgentCard, *args, **kwargs) -> T:
        pass

    @abstractmethod
    async def clear(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    async def close(self, *args, **kwargs) -> None:
        pass

    # Optional extended methods
    async def complete_upload(self, agent: dict, *args, **kwargs):
        raise NotImplementedError("This registry does not support complete_upload")

    async def deploy_agent(self, agent_name: str, *args, **kwargs):
        raise NotImplementedError("This registry does not support deploy_agent")

    async def get_agent_download(self, agent_name: str, *args, version_or_tag: str = 'latest', **kwargs):
        raise NotImplementedError("This registry does not support get_agent_download")

    async def get_current_user(self, *args, **kwargs):
        raise NotImplementedError("This registry does not support get_current_user")

    async def request_upload_url(self, agent: dict, force: bool, *args, **kwargs):
        raise NotImplementedError("This registry does not support request_upload_url")

    async def revoke_api_key(self, token: str, *args, **kwargs):
        raise NotImplementedError("This registry does not support revoke_api_key")


class InMemoryRegistry(AgentRegistry[AgentCard]):
    def __init__(self, query_parser: Optional[QueryParser] = None):
        self._agents: dict[str, AgentCard] = {}
        self._query_parser = query_parser or QueryParser()
        log.info("In-memory registry initialized")

    async def add(self, agent: AgentCard, *args, **kwargs) -> AgentCard:
        # Ensure name is unique
        if agent.name in self._agents:
            raise ValueError(f"Agent with name {agent.name} already exists.")

        log.info("Adding agent %s to in-memory registry", agent.name)
        self._agents[agent.name] = agent
        return agent

    async def get(self, agent_name: str, *args, **kwargs) -> Optional[AgentCard]:
        log.info("Getting agent %s from in-memory registry", agent_name)
        return self._agents.get(agent_name)

    async def delete(self, agent_name: str, *args, **kwargs) -> None:
        log.info("Removing agent %s from in-memory registry", agent_name)
        if agent_name in self._agents:
            del self._agents[agent_name]

    async def list(self, *args, **kwargs) -> List[AgentCard]:
        log.info("Listing all agents in in-memory registry")
        return list(self._agents.values())

    async def update(self, agent_name: str, agent: AgentCard, *args, **kwargs) -> AgentCard:
        log.info("Updating agent %s in in-memory registry", agent_name)
        if agent_name not in self._agents:
            raise ValueError(f"Agent with name {agent_name} not found.")
        self._agents[agent_name] = agent
        return agent

    async def search(self, query: str, *args, **kwargs) -> List[AgentCard]:
        log.info("Searching for '%s' in in-memory registry", query)
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

        log.info("Search for '%s' returned %d results", query, len(agents))
        return agents

    async def clear(self, *args, **kwargs) -> None:
        log.info("Clearing all agents from in-memory registry")
        self._agents.clear()

    async def close(self, *args, **kwargs) -> None:
        log.info("Closing in-memory registry")
        self._agents.clear()

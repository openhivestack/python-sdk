from typing import List, Optional

from .agent_registry import AgentRegistry, InMemoryRegistry
from .remote_registry import RemoteRegistry
from .types import AgentCard
from .query_parser import QueryParser


class OpenHive:
    def __init__(
        self,
        registry_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        query_parser: Optional[QueryParser] = None,
        registry: Optional[AgentRegistry] = None,
    ):
        if registry:
            self._registry = registry
        elif registry_url:
            self._registry = RemoteRegistry(endpoint=registry_url, token=auth_token)
        else:
            self._registry = InMemoryRegistry(query_parser=query_parser)

    async def add(self, agent: AgentCard) -> AgentCard:
        return await self._registry.add(agent)

    async def get(self, agent_name: str) -> Optional[AgentCard]:
        return await self._registry.get(agent_name)

    async def list(self) -> List[AgentCard]:
        return await self._registry.list()

    async def update(self, agent_name: str, agent: AgentCard) -> AgentCard:
        return await self._registry.update(agent_name, agent)

    async def delete(self, agent_name: str) -> None:
        await self._registry.delete(agent_name)

    async def search(self, query: str) -> List[AgentCard]:
        return await self._registry.search(query)

    async def close(self) -> None:
        await self._registry.close()

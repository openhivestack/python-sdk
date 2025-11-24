from typing import List, Optional

from .agent_registry import AgentRegistry, InMemoryRegistry
from .remote_registry import RemoteRegistry
from .types import AgentCard
from .query_parser import QueryParser


class OpenHive:
    def __init__(
        self,
        registry_url: Optional[str] = None,
        headers: Optional[dict] = None,
        query_parser: Optional[QueryParser] = None,
        registry: Optional[AgentRegistry] = None,
    ):
        if registry:
            self._registry = registry
        elif registry_url:
            self._registry = RemoteRegistry(endpoint=registry_url, options={'headers': headers} if headers else None)
        else:
            self._registry = InMemoryRegistry(query_parser=query_parser)

    async def add(self, agent: AgentCard, *args, **kwargs) -> AgentCard:
        return await self._registry.add(agent, *args, **kwargs)

    async def get(self, agent_name: str, *args, **kwargs) -> Optional[AgentCard]:
        return await self._registry.get(agent_name, *args, **kwargs)

    async def list(self, *args, **kwargs) -> List[AgentCard]:
        return await self._registry.list(*args, **kwargs)

    async def update(self, agent_name: str, agent: AgentCard, *args, **kwargs) -> AgentCard:
        return await self._registry.update(agent_name, agent, *args, **kwargs)

    async def delete(self, agent_name: str, *args, **kwargs) -> None:
        await self._registry.delete(agent_name, *args, **kwargs)

    async def search(self, query: str, *args, **kwargs) -> List[AgentCard]:
        return await self._registry.search(query, *args, **kwargs)

    async def close(self, *args, **kwargs) -> None:
        await self._registry.close(*args, **kwargs)

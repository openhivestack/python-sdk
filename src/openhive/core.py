from typing import List, Optional, TypeVar, Generic

from .agent_registry import AgentRegistry, InMemoryRegistry
from .remote_registry import RemoteRegistry
from .types import AgentCard
from .query_parser import QueryParser

T = TypeVar('T')


class OpenHive(Generic[T]):
    def __init__(
        self,
        registry_url: Optional[str] = None,
        headers: Optional[dict] = None,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        query_parser: Optional[QueryParser] = None,
        registry: Optional[AgentRegistry[T]] = None,
    ):
        if registry:
            self._registry = registry
        elif registry_url:
            options = {'headers': headers} if headers else {}
            if api_key:
                options['api_key'] = api_key
            if access_token:
                options['access_token'] = access_token

            self._registry = RemoteRegistry(
                endpoint=registry_url, options=options
            )  # type: ignore
        else:
            self._registry = InMemoryRegistry(query_parser=query_parser)  # type: ignore

    async def add(self, agent: AgentCard, *args, **kwargs) -> T:
        return await self._registry.add(agent, *args, **kwargs)

    async def get(self, agent_name: str, *args, **kwargs) -> Optional[T]:
        return await self._registry.get(agent_name, *args, **kwargs)

    async def list(self, *args, page: Optional[int] = None, limit: Optional[int] = None, **kwargs) -> List[T]:
        kwargs['page'] = page
        kwargs['limit'] = limit
        return await self._registry.list(*args, **kwargs)

    async def update(self, agent_name: str, agent: AgentCard, *args, **kwargs) -> T:
        return await self._registry.update(agent_name, agent, *args, **kwargs)

    async def delete(self, agent_name: str, *args, **kwargs) -> None:
        await self._registry.delete(agent_name, *args, **kwargs)

    async def search(
        self, query: str, *args, page: Optional[int] = None, limit: Optional[int] = None, **kwargs
    ) -> List[T]:
        kwargs['page'] = page
        kwargs['limit'] = limit
        return await self._registry.search(query, *args, **kwargs)

    async def close(self, *args, **kwargs) -> None:
        await self._registry.close(*args, **kwargs)

    # Extended Platform Methods
    async def complete_upload(self, agent: dict, *args, **kwargs):
        if hasattr(self._registry, 'complete_upload'):
            return await self._registry.complete_upload(agent, *args, **kwargs)
        raise NotImplementedError('Registry does not support complete_upload')

    async def deploy_agent(self, agent_name: str, *args, **kwargs):
        if hasattr(self._registry, 'deploy_agent'):
            return await self._registry.deploy_agent(agent_name, *args, **kwargs)
        raise NotImplementedError('Registry does not support deploy_agent')

    async def get_agent_download(self, agent_name: str, version_or_tag: str = 'latest', *args, **kwargs):
        if hasattr(self._registry, 'get_agent_download'):
            return await self._registry.get_agent_download(agent_name, version_or_tag, *args, **kwargs)
        raise NotImplementedError('Registry does not support get_agent_download')

    async def get_current_user(self, *args, **kwargs):
        if hasattr(self._registry, 'get_current_user'):
            return await self._registry.get_current_user(*args, **kwargs)
        raise NotImplementedError('Registry does not support get_current_user')

    async def request_upload_url(self, agent: dict, force: bool, *args, **kwargs):
        if hasattr(self._registry, 'request_upload_url'):
            return await self._registry.request_upload_url(agent, force, *args, **kwargs)
        raise NotImplementedError('Registry does not support request_upload_url')

    async def revoke_api_key(self, token: str, *args, **kwargs):
        if hasattr(self._registry, 'revoke_api_key'):
            return await self._registry.revoke_api_key(token, *args, **kwargs)
        raise NotImplementedError('Registry does not support revoke_api_key')

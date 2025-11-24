import httpx
from typing import List, Optional

from .agent_registry import AgentRegistry
from .types import AgentCard
from .log import get_logger

log = get_logger(__name__)


class RemoteRegistry(AgentRegistry[AgentCard]):
    def __init__(self, endpoint: str, options: Optional[dict] = None):
        self._endpoint = endpoint
        self._headers_config = options.get('headers', {}) if options else {}
        log.info("Remote registry adapter initialized for endpoint: %s", endpoint)

    @property
    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        headers.update(self._headers_config)
        return headers

    async def add(self, agent: AgentCard, *args, **kwargs) -> AgentCard:
        log.info("Adding agent %s to remote registry", agent.name)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._endpoint}/agent",
                content=agent.json(by_alias=True),
                headers=self._headers,
            )
            response.raise_for_status()
            return AgentCard(**response.json())

    async def get(self, agent_name: str, *args, **kwargs) -> Optional[AgentCard]:
        log.info("Getting agent %s from remote registry", agent_name)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._endpoint}/agent/{agent_name}", headers=self._headers
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return AgentCard(**response.json())

    async def delete(self, agent_name: str, *args, **kwargs) -> None:
        log.info("Removing agent %s from remote registry", agent_name)
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self._endpoint}/agent/{agent_name}", headers=self._headers
            )
            response.raise_for_status()

    async def list(self, *args, **kwargs) -> List[AgentCard]:
        log.info("Listing agents from remote registry")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._endpoint}/agent", headers=self._headers)
            response.raise_for_status()
            return [AgentCard(**info) for info in response.json()]

    async def search(self, query: str, *args, **kwargs) -> List[AgentCard]:
        log.info("Searching for '%s' in remote registry", query)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._endpoint}/agent",
                params={'q': query},
                headers=self._headers,
            )
            response.raise_for_status()
            return [AgentCard(**info) for info in response.json()]

    async def update(self, agent_name: str, agent: AgentCard, *args, **kwargs) -> AgentCard:
        log.info("Updating agent %s in remote registry", agent_name)
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self._endpoint}/agent/{agent_name}",
                content=agent.json(by_alias=True),
                headers=self._headers,
            )
            response.raise_for_status()
            return AgentCard(**response.json())

    async def clear(self, *args, **kwargs) -> None:
        log.warning("Clear operation is not supported on a remote registry.")
        raise NotImplementedError("Clear operation is not supported on a remote registry.")

    async def close(self, *args, **kwargs) -> None:
        log.info("No-op for remote registry close")

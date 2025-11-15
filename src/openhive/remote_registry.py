import httpx
from typing import List, Optional

from .agent_registry import AgentRegistryAdapter
from .types import AgentRegistryEntry
from .log import get_logger

log = get_logger(__name__)


class RemoteRegistry(AgentRegistryAdapter):
    def __init__(self, endpoint: str, token: Optional[str] = None):
        self._endpoint = endpoint
        self._token = token
        log.info(f"Remote registry adapter initialized for endpoint: {endpoint}")

    @property
    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def add(self, agent: AgentRegistryEntry) -> AgentRegistryEntry:
        agent_id = agent.name
        log.info(f"Adding agent {agent_id} to remote registry")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._endpoint}/agents",
                content=agent.json(by_alias=True),
                headers=self._headers,
            )
            response.raise_for_status()
            return AgentRegistryEntry(**response.json())

    async def get(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        log.info(f"Getting agent {agent_id} from remote registry")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._endpoint}/agents/{agent_id}", headers=self._headers
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return AgentRegistryEntry(**response.json())

    async def remove(self, agent_id: str) -> None:
        log.info(f"Removing agent {agent_id} from remote registry")
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self._endpoint}/agents/{agent_id}", headers=self._headers
            )
            response.raise_for_status()

    async def list(self) -> List[AgentRegistryEntry]:
        log.info(f"Listing agents from remote registry")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._endpoint}/agents", headers=self._headers)
            response.raise_for_status()
            return [AgentRegistryEntry(**info) for info in response.json()]

    async def search(self, query: str) -> List[AgentRegistryEntry]:
        log.info(f"Searching for '{query}' in remote registry")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._endpoint}/agents",
                params={'q': query},
                headers=self._headers,
            )
            response.raise_for_status()
            return [AgentRegistryEntry(**info) for info in response.json()]

    async def update(self, agent_id: str, agent: AgentRegistryEntry) -> AgentRegistryEntry:
        log.info(f"Updating agent {agent_id} in remote registry")
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self._endpoint}/agents/{agent_id}",
                content=agent.json(by_alias=True),
                headers=self._headers,
            )
            response.raise_for_status()
            return AgentRegistryEntry(**response.json())

    async def clear(self) -> None:
        log.warning("Clear operation is not supported on a remote registry.")
        raise NotImplementedError("Clear operation is not supported on a remote registry.")

    async def close(self) -> None:
        log.info("No-op for remote registry close")
        pass

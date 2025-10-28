import httpx
from typing import List, Optional

from .agent_registry import AgentRegistry
from .types import AgentInfo
from .agent_error import AgentError, PROCESSING_FAILED, AGENT_NOT_FOUND
from .log import get_logger

log = get_logger(__name__)


class RemoteRegistry(AgentRegistry):
    def __init__(self, name: str, endpoint: str, token: Optional[str] = None):
        self._name = name
        self._endpoint = endpoint
        self._token = token
        log.info(f"Remote registry '{name}' initialized for endpoint: {endpoint}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @property
    def _headers(self) -> dict:
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}

    async def add(self, agent_info: AgentInfo):
        log.info(f"Adding agent {agent_info.id} to remote registry '{self.name}'")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.endpoint}/registry/agents/add",
                    json=agent_info.dict(by_alias=True),
                    headers=self._headers,
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            log.error(
                f"Failed to add agent to remote registry '{self.name}': {e}",
                exc_info=True,
            )
            raise AgentError(
                PROCESSING_FAILED, f"Failed to add agent to remote registry: {e}"
            )

    async def get(self, agent_id: str) -> Optional[AgentInfo]:
        log.info(f"Getting agent {agent_id} from remote registry '{self.name}'")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.endpoint}/registry/agents/{agent_id}",
                    headers=self._headers,
                )
                if response.status_code == 404:
                    log.warning(
                        f"Agent {agent_id} not found in remote registry '{self.name}'"
                    )
                    return None
                response.raise_for_status()
                return AgentInfo(**response.json())
        except httpx.HTTPError as e:
            log.error(
                f"Failed to get agent from remote registry '{self.name}': {e}",
                exc_info=True,
            )
            raise AgentError(
                AGENT_NOT_FOUND, f"Failed to get agent from remote registry: {e}"
            )

    async def remove(self, agent_id: str):
        log.info(f"Removing agent {agent_id} from remote registry '{self.name}'")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.endpoint}/registry/agents/{agent_id}",
                    headers=self._headers,
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            log.error(
                f"Failed to remove agent from remote registry '{self.name}': {e}",
                exc_info=True,
            )
            raise AgentError(
                PROCESSING_FAILED, f"Failed to remove agent from remote registry: {e}"
            )

    async def list(self) -> List[AgentInfo]:
        log.info(f"Listing agents from remote registry '{self.name}'")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.endpoint}/registry/agents/list", headers=self._headers
                )
                response.raise_for_status()
                return [AgentInfo(**info) for info in response.json()]
        except httpx.HTTPError as e:
            log.error(
                f"Failed to list agents from remote registry '{self.name}': {e}",
                exc_info=True,
            )
            raise AgentError(
                PROCESSING_FAILED, f"Failed to list agents from remote registry: {e}"
            )

    async def search(self, query: str) -> List[AgentInfo]:
        log.info(f"Searching for '{query}' in remote registry '{self.name}'")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.endpoint}/registry/agents/search",
                    params={'q': query},
                    headers=self._headers,
                )
                response.raise_for_status()
                return [AgentInfo(**info) for info in response.json()]
        except httpx.HTTPError as e:
            log.error(
                f"Failed to search agents in remote registry '{self.name}': {e}",
                exc_info=True,
            )
            raise AgentError(
                PROCESSING_FAILED,
                f"Failed to search agents in remote registry: {e}",
            )

    async def update(self, agent_info: AgentInfo):
        log.info(f"Updating agent {agent_info.id} in remote registry '{self.name}'")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.endpoint}/registry/agents/{agent_info.id}",
                    json=agent_info.dict(by_alias=True),
                    headers=self._headers,
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            log.error(
                f"Failed to update agent in remote registry '{self.name}': {e}",
                exc_info=True,
            )
            raise AgentError(
                PROCESSING_FAILED, f"Failed to update agent in remote registry: {e}"
            )

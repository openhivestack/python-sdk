import httpx
from typing import List, Optional
from .agent_registry import AgentRegistry
from .types import AgentInfo
from .agent_error import AgentError, PROCESSING_FAILED, AGENT_NOT_FOUND


class RemoteRegistry(AgentRegistry):
    def __init__(self, name: str, endpoint: str):
        self._name = name
        self._endpoint = endpoint

    @property
    def name(self) -> str:
        return self._name

    @property
    def endpoint(self) -> str:
        return self._endpoint

    async def add(self, agent_info: AgentInfo):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.endpoint}/registry/add",
                    json=agent_info.dict(by_alias=True)
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise AgentError(PROCESSING_FAILED, f"Failed to add agent to remote registry: {e}")

    async def get(self, agent_id: str) -> Optional[AgentInfo]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.endpoint}/registry/{agent_id}")
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return AgentInfo(**response.json())
        except httpx.HTTPError as e:
            raise AgentError(AGENT_NOT_FOUND, f"Failed to get agent from remote registry: {e}")

    async def remove(self, agent_id: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{self.endpoint}/registry/remove/{agent_id}")
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise AgentError(PROCESSING_FAILED, f"Failed to remove agent from remote registry: {e}")

    async def list(self) -> List[AgentInfo]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.endpoint}/registry/list")
                response.raise_for_status()
                return [AgentInfo(**info) for info in response.json()]
        except httpx.HTTPError as e:
            raise AgentError(PROCESSING_FAILED, f"Failed to list agents from remote registry: {e}")

    async def search(self, query: str) -> List[AgentInfo]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.endpoint}/registry/search", params={'q': query})
                response.raise_for_status()
                return [AgentInfo(**info) for info in response.json()]
        except httpx.HTTPError as e:
            raise AgentError(PROCESSING_FAILED, f"Failed to search agents in remote registry: {e}")

    async def update(self, agent_info: AgentInfo):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.endpoint}/registry/{agent_info.id}",
                    json=agent_info.dict(by_alias=True)
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise AgentError(PROCESSING_FAILED, f"Failed to update agent in remote registry: {e}")

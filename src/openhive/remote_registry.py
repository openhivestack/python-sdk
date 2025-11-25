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
        if options:
            if options.get('api_key'):
                self._headers_config['x-api-key'] = options['api_key']
            if options.get('access_token'):
                self._headers_config['Authorization'] = f"Bearer {options['access_token']}"
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
        params = {}
        if 'page' in kwargs:
            params['page'] = kwargs['page']
        if 'limit' in kwargs:
            params['limit'] = kwargs['limit']

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._endpoint}/agent",
                params=params,
                headers=self._headers
            )
            response.raise_for_status()
            return [AgentCard(**info) for info in response.json()]

    async def search(self, query: str, *args, **kwargs) -> List[AgentCard]:
        log.info("Searching for '%s' in remote registry", query)
        params = {'q': query}
        if 'page' in kwargs:
            params['page'] = kwargs['page']
        if 'limit' in kwargs:
            params['limit'] = kwargs['limit']

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._endpoint}/agent",
                params=params,
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

    async def complete_upload(self, agent: dict, *args, **kwargs):
        log.info("Completing upload for agent %s", agent.get('name'))
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._endpoint}/agent/publish-complete",
                json={'agent': agent},
                headers=self._headers
            )
            response.raise_for_status()
            return response.json()

    async def deploy_agent(self, agent_name: str, *args, **kwargs):
        log.info("Triggering deployment for agent %s", agent_name)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._endpoint}/agent/{agent_name}/deploy",
                json={},
                headers=self._headers
            )
            
            try:
                data = response.json()
            except Exception as exc:
                raise ValueError(f"Server returned invalid JSON: {response.text}") from exc
                
            if response.status_code >= 400:
                raise Exception(data.get('message') or data.get('error') or response.reason_phrase)

            return data

    async def get_agent_download(self, agent_name: str, *args, version_or_tag: str = 'latest', **kwargs):
        log.info("Getting download URL for agent %s version %s", agent_name, version_or_tag)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._endpoint}/agent/{agent_name}/download-url",
                params={'versionOrTag': version_or_tag},
                headers=self._headers
            )

            if response.status_code >= 400:
                data = response.json()
                raise Exception(data.get('message') or response.reason_phrase)

            data = response.json()
            if not data.get('url'):
                raise Exception('No response data received from platform')
            return data

    async def get_current_user(self, *args, **kwargs):
        log.info("Getting current user info")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._endpoint}/users/me",
                headers=self._headers
            )
            
            if response.status_code >= 400:
                data = response.json()
                raise Exception(data.get('message') or response.reason_phrase)
            
            data = response.json()
            if not data.get('user'):
                raise Exception('Invalid token or user not found')
            return data.get('user')

    async def request_upload_url(self, agent: dict, force: bool, *args, **kwargs):
        log.info("Requesting upload URL for agent %s", agent.get('name'))
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._endpoint}/agent/{agent.get('name')}/upload-url",
                json={'agent': agent, 'force': force},
                headers=self._headers
            )
            
            if response.status_code >= 400:
                data = response.json()
                raise Exception(data.get('message') or response.reason_phrase)
            
            data = response.json()
            if not data.get('url'):
                raise Exception('No response data received from platform')
            return data

    async def revoke_api_key(self, token: str, *args, **kwargs):
        log.info("Revoking API key")
        headers = self._headers.copy()
        if token:
            headers['Authorization'] = f"Bearer {token}"
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._endpoint}/auth/sign-out",
                headers=headers
            )
            if response.status_code >= 400:
                data = response.json()
                raise Exception(data.get('message') or response.reason_phrase)

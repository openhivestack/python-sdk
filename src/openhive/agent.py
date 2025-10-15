from typing import Dict, Any, Callable, Awaitable, List, Optional, Union
import httpx
import os
from pydantic import ValidationError

from .log import get_logger
from .agent_config import AgentConfig
from .agent_identity import AgentIdentity
from .types import AgentMessageType, TaskRequestData, TaskResultData, TaskErrorData, AgentInfo
from .agent_error import (
    AgentError, INVALID_SIGNATURE, INVALID_MESSAGE_FORMAT, INVALID_PARAMETERS,
    CAPABILITY_NOT_FOUND, PROCESSING_FAILED, AGENT_NOT_FOUND, CONFIG_ERROR
)
from .agent_registry import AgentRegistry, InMemoryRegistry
from .remote_registry import RemoteRegistry

CapabilityHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]

log = get_logger(__name__)


class Agent:
    def __init__(self, config: Optional[Union[AgentConfig, str]] = None, registry: AgentRegistry = None):
        if config is None:
            config = os.path.join(os.getcwd(), '.hive.yml')
        
        log.info("Initializing agent...")
        self.config = AgentConfig(config)
        self.identity = AgentIdentity.create(self.config)
        self._capability_handlers: Dict[str, CapabilityHandler] = {}
        self.registries: Dict[str, AgentRegistry] = {}
        
        log.info("Setting up internal registry.")
        self.registries['internal'] = InMemoryRegistry('internal', self.config.endpoint)
        
        if registry:
            log.info(f"Using provided registry: {registry.name}")
            self.registries[registry.name] = registry
            self.active_registry = registry
        else:
            log.info("Defaulting to internal registry.")
            self.active_registry = self.registries['internal']
        
        log.info(f"Agent initialized with ID: {self.identity.id()}")

    @property
    def registry(self) -> AgentRegistry:
        return self.active_registry

    def use_registry(self, name: str) -> "Agent":
        if name not in self.registries:
            raise ValueError(f"Registry with name '{name}' not found.")
        self.active_registry = self.registries[name]
        log.info(f"Switched to registry: {name}")
        return self

    def add_registry(
        self, registry_or_endpoint: Union[AgentRegistry, str], name: Optional[str] = None
    ) -> "Agent":
        if isinstance(registry_or_endpoint, str):
            endpoint = registry_or_endpoint
            registry_name = name or endpoint
            new_registry = RemoteRegistry(registry_name, endpoint)
            self.registries[new_registry.name] = new_registry
            log.info(f"Added remote registry '{new_registry.name}' for endpoint: {endpoint}")
        else:
            self.registries[registry_or_endpoint.name] = registry_or_endpoint
            log.info(f"Added registry: {registry_or_endpoint.name}")
        return self

    def remove_registry(self, name: str) -> "Agent":
        if name in self.registries:
            del self.registries[name]
            log.info(f"Removed registry: {name}")
        return self

    def get_registry(self, name: str) -> AgentRegistry:
        return self.registries[name]

    def list_registries(self) -> List[AgentRegistry]:
        return list(self.registries.values())

    def capability(self, capability_id: str, handler=None):
        if not self.config.has_capability(capability_id):
            raise ValueError(
                f"Capability '{capability_id}' not defined in agent configuration."
            )
        
        log.info(f"Registering handler for capability: {capability_id}")

        def decorator(func: CapabilityHandler):
            self._capability_handlers[capability_id] = func
            return func

        if handler:
            return decorator(handler)
        return decorator

    async def process(
        self,
        message: dict,
        sender_public_key: str,
    ) -> dict:
        task_id = message.get("data", {}).get("task_id", "unknown")
        log.info(f"Processing message for task: {task_id}")

        if not self.identity.verify_message(message, sender_public_key):
            log.warning(f"Signature verification failed for task: {task_id}")
            return self._create_error_response(
                task_id,
                INVALID_SIGNATURE,
                "Signature verification failed.",
            )

        log.info(f"Signature verified for task: {task_id}")

        if message.get("type") != AgentMessageType.TASK_REQUEST.value:
            log.warning(f"Invalid message type for task: {task_id}")
            return self._create_error_response(
                task_id,
                INVALID_MESSAGE_FORMAT,
                "Invalid message type.",
            )

        try:
            task_data = TaskRequestData(**message.get("data", {}))
        except ValidationError as e:
            log.error(f"Invalid task data for task {task_id}: {e}")
            return self._create_error_response(
                task_id,
                INVALID_PARAMETERS,
                f"Invalid task data: {e}",
            )

        handler = self._capability_handlers.get(task_data.capability)
        if not handler:
            log.error(f"Capability '{task_data.capability}' not found for task: {task_id}")
            return self._create_error_response(
                task_id,
                CAPABILITY_NOT_FOUND,
                f"Capability '{task_data.capability}' not found.",
            )

        try:
            log.info(f"Executing handler for capability '{task_data.capability}' on task: {task_id}")
            result = await handler(task_data.params)
            log.info(f"Capability '{task_data.capability}' executed successfully for task: {task_id}")
            return TaskResultData(task_id=task_id, result=result).dict()
        except Exception as e:
            log.error(f"Error executing capability '{task_data.capability}' for task {task_id}: {e}", exc_info=True)
            return self._create_error_response(
                task_id,
                PROCESSING_FAILED,
                str(e),
            )

    def _create_error_response(
        self, task_id: str, error_code: str, message: str,
    ) -> dict:
        log.error(f"Creating error response for task {task_id}: {error_code} - {message}")
        return TaskErrorData(
            task_id=task_id,
            error=error_code,
            message=message,
            retry=False
        ).dict()

    async def register(self, registry: Optional[Union[str, AgentRegistry]] = None):
        if registry is None:
            registry_obj = self.active_registry
        elif isinstance(registry, str):
            registry_obj = self.get_registry(registry)
        else:
            registry_obj = registry

        if not registry_obj:
            raise AgentError(CONFIG_ERROR, "Registry not found.")
        
        log.info(f"Registering agent with registry: {registry_obj.name}")

        info = self.config.info()
        info.pop("keys", None)
        agent_info = AgentInfo(
            **info,
            keys={"publicKey": self.identity.get_public_key()},
        )

        try:
            await registry_obj.add(agent_info)
            log.info(f"Successfully registered with registry: {registry_obj.name}")
        except Exception as e:
            log.error(f"Failed to register with registry '{registry_obj.name}': {e}", exc_info=True)
            raise AgentError(
                PROCESSING_FAILED,
                f"Failed to register with registry '{registry_obj.name}': {e}"
            ) from e

    async def search(self, query: str, registry: Optional[Union[str, AgentRegistry]] = None) -> List[AgentInfo]:
        if registry is None:
            registry_obj = self.active_registry
        elif isinstance(registry, str):
            registry_obj = self.get_registry(registry)
        else:
            registry_obj = registry

        if not registry_obj:
            raise AgentError(CONFIG_ERROR, "Registry not found.")
        
        log.info(f"Searching for '{query}' in registry: {registry_obj.name}")

        try:
            results = await registry_obj.search(query)
            log.info(f"Found {len(results)} results for query '{query}' in registry '{registry_obj.name}'")
            return results
        except Exception as e:
            log.error(f"Failed to search in registry '{registry_obj.name}': {e}", exc_info=True)
            raise AgentError(
                PROCESSING_FAILED,
                f"Failed to search for agents with query '{query}' from registry '{registry_obj.name}': {e}"
            ) from e

    async def public_key(self, agent_id: str) -> str | None:
        log.info(f"Fetching public key for agent: {agent_id}")
        agent_info = await self.active_registry.get(agent_id)
        if agent_info:
            log.info(f"Public key found for agent: {agent_id}")
            return agent_info.keys.public_key
        log.warning(f"Public key not found for agent: {agent_id}")
        return None

    def endpoint(self) -> str:
        return self.config.endpoint

    def port(self) -> int:
        return self.config.port

    def host(self) -> str:
        return self.config.host

    async def send_task(
        self, to_agent_id: str, capability: str, params: dict, task_id: str = None
    ) -> dict:
        log.info(f"Sending task '{capability}' to agent: {to_agent_id}")
        target_agent = await self.active_registry.get(to_agent_id)
        if not target_agent:
            log.error(f"Agent {to_agent_id} not found in registry.")
            raise AgentError(AGENT_NOT_FOUND, f"Agent {to_agent_id} not found in registry.")

        if not target_agent.endpoint:
            log.error(f"Endpoint for agent {to_agent_id} not configured.")
            raise AgentError(CONFIG_ERROR, f"Endpoint for agent {to_agent_id} not configured.")

        task_request = self.identity.createTaskRequest(
            to_agent_id,
            capability,
            params,
            task_id,
        )

        log.info(f"Sending task request to: {target_agent.endpoint}/tasks")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{target_agent.endpoint}/tasks",
                json=task_request,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()
            response_data = response.json()
            log.info(f"Received response for task")

            if not self.identity.verify_message(response_data, target_agent.keys.public_key):
                log.error("Response signature verification failed.")
                raise AgentError(INVALID_SIGNATURE, "Response signature verification failed.")

            log.info("Response signature verified.")
            return response_data['data']

    def create_server(self):
        from .agent_server import AgentServer
        return AgentServer(self)

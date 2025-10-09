from typing import Dict, Any, Callable, Awaitable, Optional
from .agent_config import AgentConfig
from .agent_identity import AgentIdentity
from .types import AgentMessageType, TaskRequestData, TaskResultData, TaskErrorData, AgentInfo
from . import hive_error
from .agent_registry import AgentRegistry, InMemoryRegistry
import httpx
import base64

CapabilityHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


class Agent:
    def __init__(
        self,
        config: AgentConfig,
        private_key: bytes = None,
        public_key: bytes = None,
        registry: AgentRegistry = None,
    ):
        self.config = config
        self.registry = registry or InMemoryRegistry()

        if private_key and public_key:
            self.identity = AgentIdentity(config, private_key, public_key)
        else:
            self.identity = AgentIdentity.create(config)

        self._capability_handlers: Dict[str, CapabilityHandler] = {}

    def capability(self, capability_id: str, handler: Optional[CapabilityHandler] = None):
        def decorator(func: CapabilityHandler):
            if not self.config.has_capability(capability_id):
                raise ValueError(f"Capability '{capability_id}' is not defined.")
            self._capability_handlers[capability_id] = func
            return func

        if handler:
            return decorator(handler)
        return decorator

    async def handle_task_request(
        self,
        message: dict,
        sender_public_key: bytes,
    ) -> dict:
        task_id = message.get("data", {}).get("task_id", "unknown")

        if not self.identity.verify_message(message, sender_public_key):
            return self._create_error_response(
                task_id,
                hive_error.INVALID_SIGNATURE,
                "Signature verification failed.",
            )

        if message.get("type") != AgentMessageType.TASK_REQUEST.value:
            return self._create_error_response(
                task_id,
                hive_error.INVALID_MESSAGE_FORMAT,
                "Invalid message type.",
            )

        try:
            task_data = TaskRequestData(**message.get("data", {}))
        except Exception as e:
            return self._create_error_response(
                task_id,
                hive_error.INVALID_PARAMETERS,
                f"Invalid task data: {e}",
            )

        handler = self._capability_handlers.get(task_data.capability)
        if not handler:
            return self._create_error_response(
                task_id,
                hive_error.CAPABILITY_NOT_FOUND,
                f"Capability '{task_data.capability}' not found.",
            )

        try:
            result = await handler(task_data.params)
            return TaskResultData(task_id=task_id, result=result).dict()
        except Exception as e:
            return self._create_error_response(
                task_id,
                hive_error.PROCESSING_FAILED,
                str(e),
            )

    def _create_error_response(
        self, task_id: str, error_code: str, message: str,
    ) -> dict:
        return TaskErrorData(
            task_id=task_id,
            error=error_code,
            message=message,
            retry=False
        ).dict()

    async def register(self):
        agent_info_dict = self.config.info()
        agent_info_dict['publicKey'] = base64.b64encode(self.identity.public_key).decode('utf-8')
        agent_info = AgentInfo(**agent_info_dict)
        await self.registry.add(agent_info)

    async def get_public_key(self, agent_id: str) -> bytes | None:
        agent_info = await self.registry.get(agent_id)
        if agent_info:
            return base64.b64decode(agent_info.public_key)
        return None

    def get_identity(self) -> AgentIdentity:
        return self.identity

    def get_endpoint(self) -> str:
        return self.config.endpoint

    async def send_task(
        self, to_agent_id: str, capability: str, params: dict, task_id: str = None
    ) -> dict:
        target_agent = await self.registry.get(to_agent_id)
        if not target_agent:
            raise ValueError(f"Agent {to_agent_id} not found in registry.")

        if not target_agent.endpoint:
            raise ValueError(f"Endpoint for agent {to_agent_id} not configured.")

        task_request = self.identity.createTaskRequest(
            to_agent_id, capability, params, task_id=task_id
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{target_agent.endpoint}/tasks",
                json=task_request,
            )
            response.raise_for_status()
            response_message = response.json()

        target_public_key = base64.b64decode(target_agent.public_key)
        if not self.identity.verify_message(response_message, target_public_key):
            raise ValueError("Response signature verification failed.")

        return response_message['data']

    def create_server(self):
        from .agent_server import AgentServer
        return AgentServer(self)

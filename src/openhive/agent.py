from typing import Dict, Any, Callable, Awaitable, List
import base64
import httpx
from .agent_config import AgentConfig
from .agent_identity import AgentIdentity
from .types import AgentMessageType, TaskRequestData, TaskResultData, TaskErrorData, AgentInfo
from .agent_error import AgentError, INVALID_SIGNATURE, INVALID_MESSAGE_FORMAT, INVALID_PARAMETERS
from .agent_error import CAPABILITY_NOT_FOUND, PROCESSING_FAILED
from .agent_registry import AgentRegistry, InMemoryRegistry

CapabilityHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


class Agent:
    def __init__(self, config: AgentConfig | str, registry: AgentRegistry = None):
        self.config = AgentConfig(config)
        self.identity = AgentIdentity.create(self.config)
        self._capability_handlers = {}
        self.registry: AgentRegistry = registry if registry else InMemoryRegistry()

    def capability(self, capability_id: str, handler=None):
        if not self.config.has_capability(capability_id):
            raise ValueError(
                f"Capability '{capability_id}' not defined in agent configuration."
            )
        
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

        if not self.identity.verify_message(
            message, base64.b64decode(sender_public_key)
        ):
            return self._create_error_response(
                task_id,
                INVALID_SIGNATURE,
                "Signature verification failed.",
            )

        if message.get("type") != AgentMessageType.TASK_REQUEST.value:
            return self._create_error_response(
                task_id,
                INVALID_MESSAGE_FORMAT,
                "Invalid message type.",
            )

        try:
            task_data = TaskRequestData(**message.get("data", {}))
        except Exception as e:
            return self._create_error_response(
                task_id,
                INVALID_PARAMETERS,
                f"Invalid task data: {e}",
            )

        handler = self._capability_handlers.get(task_data.capability)
        if not handler:
            return self._create_error_response(
                task_id,
                CAPABILITY_NOT_FOUND,
                f"Capability '{task_data.capability}' not found.",
            )

        try:
            result = await handler(task_data.params)
            return TaskResultData(task_id=task_id, result=result).dict()
        except Exception as e:
            return self._create_error_response(
                task_id,
                PROCESSING_FAILED,
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

    async def register(self, registry_endpoint: str = None):
        agent_info = AgentInfo(
            **self.config.info(),
            publicKey=self.identity.get_public_key_b64(),
        )
        await self.registry.add(agent_info)

        if registry_endpoint:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{registry_endpoint}/registry/add",
                        json=agent_info.dict(by_alias=True),
                    )
            except Exception as e:
                raise AgentError(
                    f"Failed to register with remote registry at {registry_endpoint}: {e}"
                )

    async def search(self, query: str, registry_endpoint: str) -> List[AgentInfo]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{registry_endpoint}/registry/search", params={"q": query}
                )
                response.raise_for_status()
                results_dict = response.json()
                return [AgentInfo(**info) for info in results_dict]
        except Exception as e:
            raise AgentError(
                f"Failed to search for agents with query '{query}' from registry at {registry_endpoint}: {e}"
            )

    async def public_key(self, agent_id: str) -> str | None:
        agent_info = await self.registry.get(agent_id)
        if agent_info:
            return agent_info.public_key
        return None

    def endpoint(self) -> str:
        return self.config.endpoint

    async def send_task(
        self, to_agent_id: str, capability: str, params: dict, task_id: str = None
    ) -> dict:
        target_agent = await self.registry.get(to_agent_id)
        if not target_agent:
            raise Exception(f"Agent {to_agent_id} not found in registry.")

        if not target_agent.endpoint:
            raise Exception(f"Endpoint for agent {to_agent_id} not configured.")

        task_request = self.identity.createTaskRequest(
            to_agent_id,
            capability,
            params,
            task_id,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{target_agent.endpoint}/tasks",
                json=task_request,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()
            response_data = response.json()

            if not self.identity.verify_message(
                response_data, base64.b64decode(target_agent.publicKey)
            ):
                raise Exception("Response signature verification failed.")

            return response_data['data']

    def create_server(self):
        from .agent_server import AgentServer
        return AgentServer(self)

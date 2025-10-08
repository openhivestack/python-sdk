from typing import Dict, Any, Callable, Awaitable
from .config import Config
from .agent_identity import AgentIdentity
from .types import HiveMessageType, TaskRequestData, TaskResultData, TaskErrorData
from . import hive_error

CapabilityHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


class Agent:
    def __init__(
        self,
        config: Config,
        private_key: bytes = None,
        public_key: bytes = None,
    ):
        self.config = config
        if private_key and public_key:
            self.identity = AgentIdentity(config, private_key, public_key)
        else:
            self.identity = AgentIdentity.create(config)
        
        self._capability_handlers: Dict[str, CapabilityHandler] = {}
        self._peers: Dict[str, bytes] = {}

    def capability(self, capability_id: str):
        def decorator(func: CapabilityHandler):
            if not self.config.has_capability(capability_id):
                raise ValueError(f"Capability '{capability_id}' is not defined.")
            self._capability_handlers[capability_id] = func
            return func
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

        if message.get("type") != HiveMessageType.TASK_REQUEST.value:
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
        
    def add_peer(self, agent_id: str, public_key: bytes):
        self._peers[agent_id] = public_key

    def get_peer_public_key(self, agent_id: str) -> bytes | None:
        return self._peers.get(agent_id)

    def get_identity(self) -> AgentIdentity:
        return self.identity
        
    def get_port(self) -> int:
        return self.config.port
        
    def create_server(self):
        from .agent_server import AgentServer
        return AgentServer(self)

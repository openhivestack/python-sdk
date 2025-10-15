import json
import uuid
import base64

from .agent_config import AgentConfig
from .agent_signature import AgentSignature
from .types import AgentMessageType
from .log import get_logger

log = get_logger(__name__)


class AgentIdentity:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.private_key = config.keys['privateKey']
        self.public_key = config.keys['publicKey']
        log.info(f"AgentIdentity initialized for agent: {self.id()}")

    @classmethod
    def create(cls, config: AgentConfig):
        log.info("Creating new AgentIdentity")
        return cls(config)

    def id(self) -> str:
        return self.config.id

    def _create_message(
        self,
        to_agent_id: str,
        msg_type: AgentMessageType,
        data: dict,
    ) -> dict:
        message_without_sig = {
            "from": self.id(),
            "to": to_agent_id,
            "type": msg_type.value,
            "data": data,
        }
        
        log.info(f"Signing message to {to_agent_id} of type {msg_type.value}")
        signature = AgentSignature.sign(message_without_sig, self.private_key)
        
        return {**message_without_sig, "sig": signature}

    def createTaskRequest(
        self,
        to_agent_id: str,
        capability: str,
        params: dict,
        task_id: str = None,
    ) -> dict:
        task_id = task_id or str(uuid.uuid4())
        log.info(f"Creating task request for capability '{capability}' with task ID: {task_id}")
        data = {
            "task_id": task_id,
            "capability": capability,
            "params": params,
        }
        return self._create_message(
            to_agent_id,
            AgentMessageType.TASK_REQUEST,
            data,
        )

    def createTaskResult(
        self,
        to_agent_id: str,
        task_id: str,
        result: dict,
    ) -> dict:
        log.info(f"Creating task result for task '{task_id}'")
        data = {
            "task_id": task_id,
            "status": "completed",
            "result": result,
        }
        return self._create_message(
            to_agent_id,
            AgentMessageType.TASK_RESULT,
            data,
        )

    def createTaskError(
        self,
        to_agent_id: str,
        task_id: str,
        error: dict,
        retry: bool,
    ) -> dict:
        log.info(f"Creating task error for task '{task_id}'")
        data = {
            "task_id": task_id,
            "error": error,
            "retry": retry,
        }
        return self._create_message(
            to_agent_id,
            AgentMessageType.TASK_ERROR,
            data,
        )

    def verify_message(
        self, message: dict, public_key: bytes,
    ) -> bool:
        log.info(f"Verifying message signature from '{message.get('from')}'")
        message_copy = message.copy()
        signature = message_copy.pop("sig")

        is_valid = AgentSignature.verify(
            message_copy,
            signature,
            public_key,
        )
        log.info(f"Signature from '{message.get('from')}' is {'valid' if is_valid else 'invalid'}")
        return is_valid

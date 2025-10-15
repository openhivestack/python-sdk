import json
import uuid
import base64
from .agent_config import AgentConfig
from .agent_signature import AgentSignature
from .types import AgentMessageType


class AgentIdentity:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.private_key = config.keys['privateKey']
        self.public_key = config.keys['publicKey']

    @classmethod
    def create(cls, config: AgentConfig):
        return cls(config)

    def id(self) -> str:
        return self.config.id

    def name(self) -> str:
        return self.config.name
        
    def get_public_key(self) -> str:
        return self.public_key

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
        
        signature = AgentSignature.sign(message_without_sig, self.private_key)
        
        return {**message_without_sig, "sig": signature}

    def createTaskRequest(
        self,
        to_agent_id: str,
        capability: str,
        params: dict,
        task_id: str = None,
    ) -> dict:
        data = {
            "task_id": task_id or str(uuid.uuid4()),
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
        error: str,
        message: str,
        retry: bool,
    ) -> dict:
        data = {
            "task_id": task_id,
            "error": error,
            "message": message,
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
        message_copy = message.copy()
        signature = message_copy.pop("sig")

        return AgentSignature.verify(
            message_copy,
            signature,
            public_key,
        )

import json
import uuid
from .config import Config
from .crypto import Crypto
from .types import HiveMessageType


class AgentIdentity:
    def __init__(self, config: Config, private_key: bytes, public_key: bytes):
        self.config = config
        self.private_key = private_key
        self.public_key = public_key

    @classmethod
    def create(cls, config: Config):
        keys = Crypto.generate_key_pair()
        return cls(config, keys["private_key"], keys["public_key"])

    def id(self) -> str:
        return self.config.id

    def name(self) -> str:
        return self.config.name

    def _create_message(
        self,
        to_agent_id: str,
        msg_type: HiveMessageType,
        data: dict,
    ) -> dict:
        message_without_sig = {
            "from": self.id(),
            "to": to_agent_id,
            "type": msg_type.value,
            "data": data,
        }
        
        # Pydantic models need to be converted to dicts for JSON serialization
        # but here `data` is already a dict.
        # We need a stable JSON representation for signing.
        message_json = json.dumps(
            message_without_sig,
            sort_keys=True, 
            separators=(',', ':')
        ).encode('utf-8')
        
        signature = Crypto.sign(message_json, self.private_key)
        
        return {**message_without_sig, "sig": signature}

    def createTaskRequest(
        self,
        to_agent_id: str,
        capability: str,
        params: dict,
    ) -> dict:
        data = {
            "task_id": str(uuid.uuid4()),
            "capability": capability,
            "params": params,
        }
        return self._create_message(
            to_agent_id,
            HiveMessageType.TASK_REQUEST,
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
            HiveMessageType.TASK_RESULT,
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
            HiveMessageType.TASK_ERROR,
            data,
        )

    def verify_message(
        self, message: dict, public_key: bytes,
    ) -> bool:
        message_copy = message.copy()
        signature = message_copy.pop("sig")

        message_json = (
            json.dumps(
                message_copy,
                sort_keys=True,
                separators=(',', ':'),
            ).encode('utf-8')
        )
        return Crypto.verify(
            message_json,
            signature,
            public_key,
        )

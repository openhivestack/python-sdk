from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class AgentCapability(BaseModel):
    id: str
    description: str = ""
    input: Dict[str, Any]
    output: Dict[str, Any]


class AgentConfigStruct(BaseModel):
    id: str
    name: str
    description: str
    version: str
    endpoint: str
    host: str
    port: int
    public_key: Optional[str] = Field(None, alias="publicKey")
    log_level: str = Field("info", alias="logLevel")
    capabilities: List[AgentCapability]
    keys: Dict[str, str]


class AgentKeys(BaseModel):
    public_key: str = Field(..., alias="publicKey")


class AgentInfo(BaseModel):
    id: str
    name: str
    description: str
    version: str
    endpoint: str
    capabilities: List[AgentCapability]
    keys: AgentKeys


class AgentMessageType(str, Enum):
    TASK_REQUEST = 'task_request'
    TASK_RESPONSE = 'task_response'
    TASK_UPDATE = 'task_update'
    TASK_RESULT = 'task_result'
    TASK_ERROR = 'task_error'
    CAPABILITY_QUERY = 'capability_query'
    CAPABILITY_RESPONSE = 'capability_response'
    HEARTBEAT = 'heartbeat'
    AGENT_IDENTITY = 'agent_identity'


class TaskRequestData(BaseModel):
    task_id: str
    capability: str
    params: Dict[str, Any]
    deadline: Optional[str] = None


class TaskResultData(BaseModel):
    task_id: str
    status: str = 'completed'
    result: Dict[str, Any]


class TaskErrorData(BaseModel):
    task_id: str
    error: str
    message: str
    retry: bool


class AgentMessage(BaseModel):
    from_id: str = Field(..., alias='from')
    to: str
    type: AgentMessageType
    data: Dict[str, Any]
    sig: str

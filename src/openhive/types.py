from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class AgentCapability(BaseModel):
    id: str
    description: str = ""
    input: Dict[str, Any]
    output: Dict[str, Any]


class AgentConfig(BaseModel):
    id: str
    name: str
    description: str
    version: str
    port: int = 11100
    log_level: str = Field("info", alias="logLevel")
    capabilities: List[AgentCapability]


class HiveMessageType(str, Enum):
    TASK_REQUEST = 'task_request'
    TASK_RESPONSE = 'task_response'
    TASK_UPDATE = 'task_update'
    TASK_RESULT = 'task_result'
    TASK_ERROR = 'task_error'
    CAPABILITY_QUERY = 'capability_query'
    CAPABILITY_RESPONSE = 'capability_response'


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


class HiveMessage(BaseModel):
    from_agent: str = Field(..., alias='from')
    to: str
    type: HiveMessageType
    data: Dict[str, Any]
    sig: str

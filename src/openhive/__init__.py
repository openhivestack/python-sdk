"""
H.I.V.E. Protocol Core SDK for Python
"""
__version__ = "0.4.0"

from .agent import Agent
from .agent_config import AgentConfig, AgentConfigError
from .types import AgentCapability, AgentMessage, AgentMessageType, AgentConfigStruct
from .agent_signature import AgentSignature

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentConfigError",
    "AgentCapability",
    "AgentMessage",
    "AgentMessageType",
    "AgentConfigStruct",
    "AgentSignature",
]

INVALID_SIGNATURE = "invalid_signature"
CAPABILITY_NOT_FOUND = "capability_not_found"
INVALID_PARAMETERS = "invalid_parameters"
PROCESSING_FAILED = "processing_failed"
RESOURCE_UNAVAILABLE = "resource_unavailable"
RATE_LIMITED = "rate_limited"
INVALID_MESSAGE_FORMAT = "invalid_message_format"
AGENT_NOT_FOUND = "agent_not_found"
CONFIG_ERROR = "config_error"
TASK_ERROR = "task_error"


class AgentError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

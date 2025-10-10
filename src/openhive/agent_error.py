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
    def __init__(self, message: str, code: str = PROCESSING_FAILED, retry: bool = False):
        super().__init__(message)
        self.message = message
        self.code = code
        self.retry = retry
        self.http_status = 500

        if code == INVALID_SIGNATURE:
            self.http_status = 401
        elif code in [CAPABILITY_NOT_FOUND, AGENT_NOT_FOUND]:
            self.http_status = 404
        elif code in [INVALID_PARAMETERS, INVALID_MESSAGE_FORMAT, CONFIG_ERROR]:
            self.http_status = 400
        elif code == RATE_LIMITED:
            self.http_status = 429
        elif code == RESOURCE_UNAVAILABLE:
            self.http_status = 503

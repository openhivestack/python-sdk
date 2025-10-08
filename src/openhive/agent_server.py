from fastapi import FastAPI, HTTPException
from uvicorn import run
from .agent import Agent


class AgentServer:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.app = FastAPI()
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/status")
        async def get_status():
            identity = self.agent.get_identity()
            return {
                "agentId": identity.id(),
                "status": "ok",
                "version": identity.config.version,
            }

        @self.app.get("/capabilities")
        async def get_capabilities():
            identity = self.agent.get_identity()
            return {
                "agentId": identity.id(),
                "capabilities": [
                    cap.dict() for cap in identity.config.capabilities
                ],
            }

        @self.app.post("/tasks")
        async def post_tasks(message: dict):
            sender_id = message.get("from")
            if not sender_id:
                raise HTTPException(
                    status_code=400,
                    detail="'from' field is missing in message"
                )
                
            sender_public_key = self.agent.get_peer_public_key(sender_id)
            if not sender_public_key:
                raise HTTPException(
                    status_code=401,
                    detail="Sender public key not found. Peer not configured.",
                )
            
            response_data = await self.agent.handle_task_request(
                message,
                sender_public_key,
            )

            identity = self.agent.get_identity()

            if "error" in response_data:
                response_message = identity.createTaskError(
                    sender_id,
                    response_data['task_id'],
                    response_data['error'],
                    response_data['message'],
                    response_data['retry']
                )
                return response_message
            else:
                response_message = identity.createTaskResult(
                    sender_id,
                    response_data['task_id'],
                    response_data['result']
                )
                return response_message

    def start(self, port: int = None):
        listen_port = port or self.agent.get_port()
        run(self.app, host="0.0.0.0", port=listen_port)

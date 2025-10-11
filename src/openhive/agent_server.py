from fastapi import FastAPI, HTTPException
from uvicorn import run
from yarl import URL
from .agent import Agent
from .types import AgentInfo


class AgentServer:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.app = FastAPI()
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/status")
        async def get_status():
            identity = self.agent.identity()
            return {
                "agentId": identity.id(),
                "status": "ok",
                "version": identity.config.version,
            }

        @self.app.get("/capabilities")
        async def get_capabilities():
            identity = self.agent.identity()
            return {
                "agentId": identity.id(),
                "capabilities": [
                    cap.dict() for cap in identity.config.capabilities
                ],
            }

        @self.app.post("/registry/add", status_code=201)
        async def add_agent_to_registry(agent_info: AgentInfo):
            try:
                await self.agent.registry.add(agent_info)
                return agent_info
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/registry/list")
        async def list_agents_in_registry():
            try:
                agents = await self.agent.registry.list()
                return agents
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/registry/search")
        async def search_agents_in_registry(q: str):
            try:
                results = await self.agent.registry.search(q)
                return results
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/registry/{agent_id}")
        async def get_agent_from_registry(agent_id: str):
            try:
                agent = await self.agent.registry.get(agent_id)
                if agent:
                    return agent
                else:
                    raise HTTPException(status_code=404, detail="Agent not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.put("/registry/{agent_id}", status_code=200)
        async def update_agent_in_registry(agent_id: str, agent_info: AgentInfo):
            if agent_id != agent_info.id:
                raise HTTPException(status_code=400, detail="Agent ID mismatch")
            try:
                await self.agent.registry.update(agent_info)
                return agent_info
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/registry/{agent_id}", status_code=204)
        async def remove_agent_from_registry(agent_id: str):
            try:
                await self.agent.registry.remove(agent_id)
                return
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/tasks")
        async def post_tasks(message: dict):
            sender_id = message.get("from")
            if not sender_id:
                raise HTTPException(
                    status_code=400,
                    detail="'from' field is missing in message"
                )

            sender_public_key = await self.agent.public_key(sender_id)
            if not sender_public_key:
                raise HTTPException(
                    status_code=401,
                    detail="Sender public key not found. Peer not configured.",
                )

            response_data = await self.agent.process(
                message,
                sender_public_key,
            )

            identity = self.agent.identity()

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
        listen_port = port or int(URL(self.agent.endpoint()).port)
        run(self.app, host="0.0.0.0", port=listen_port)

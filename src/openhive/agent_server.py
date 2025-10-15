from fastapi import FastAPI, HTTPException
from uvicorn import run
from yarl import URL

from .agent import Agent
from .types import AgentInfo
from .log import get_logger

log = get_logger(__name__)


class AgentServer:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.app = FastAPI()
        log.info("Setting up agent server routes...")
        self._setup_routes()
        log.info("Routes configured.")

    def _setup_routes(self):
        @self.app.get("/status")
        async def get_status():
            log.info("Received request for /status")
            identity = self.agent.identity
            return {
                "agentId": identity.id(),
                "status": "ok",
                "version": identity.config.version,
            }

        @self.app.get("/capabilities")
        async def get_capabilities():
            log.info("Received request for /capabilities")
            identity = self.agent.identity
            return {
                "agentId": identity.id(),
                "capabilities": [
                    cap.dict() for cap in identity.config.capabilities
                ],
            }

        @self.app.post("/registry/agents/add", status_code=201)
        async def add_agent_to_registry(agent_info: AgentInfo):
            log.info(f"Received request to add agent {agent_info.id} to registry")
            try:
                await self.agent.registry.add(agent_info)
                log.info(f"Agent {agent_info.id} added to registry")
                return agent_info
            except Exception as e:
                log.error(f"Error adding agent to registry: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/registry/agents/list")
        async def list_agents_in_registry():
            log.info("Received request for /registry/agents/list")
            try:
                agents = await self.agent.registry.list()
                log.info(f"Returning {len(agents)} agents from registry")
                return agents
            except Exception as e:
                log.error(f"Error listing agents from registry: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/registry/agents/search")
        async def search_agents_in_registry(q: str):
            log.info(f"Received request for /registry/agents/search with query: {q}")
            try:
                results = await self.agent.registry.search(q)
                log.info(f"Found {len(results)} agents for query: {q}")
                return results
            except Exception as e:
                log.error(f"Error searching agents in registry: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/registry/agents/{agent_id}")
        async def get_agent_from_registry(agent_id: str):
            log.info(f"Received request for /registry/agents/{agent_id}")
            try:
                agent = await self.agent.registry.get(agent_id)
                if agent:
                    log.info(f"Agent {agent_id} found in registry")
                    return agent
                else:
                    log.warning(f"Agent {agent_id} not found in registry")
                    raise HTTPException(status_code=404, detail="Agent not found")
            except Exception as e:
                log.error(f"Error getting agent from registry: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.put("/registry/agents/{agent_id}", status_code=200)
        async def update_agent_in_registry(agent_id: str, agent_info: AgentInfo):
            log.info(f"Received request to update agent {agent_id} in registry")
            if agent_id != agent_info.id:
                raise HTTPException(status_code=400, detail="Agent ID mismatch")
            try:
                await self.agent.registry.update(agent_info)
                log.info(f"Agent {agent_id} updated in registry")
                return agent_info
            except Exception as e:
                log.error(f"Error updating agent in registry: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/registry/agents/{agent_id}", status_code=204)
        async def remove_agent_from_registry(agent_id: str):
            log.info(f"Received request to delete agent {agent_id} from registry")
            try:
                await self.agent.registry.remove(agent_id)
                log.info(f"Agent {agent_id} removed from registry")
                return
            except Exception as e:
                log.error(f"Error removing agent from registry: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/tasks")
        async def post_tasks(message: dict):
            sender_id = message.get("from")
            log.info(f"Received task request from {sender_id}")
            if not sender_id:
                raise HTTPException(
                    status_code=400,
                    detail="'from' field is missing in message"
                )

            sender_public_key = await self.agent.public_key(sender_id)
            if not sender_public_key:
                log.error(f"Sender public key not found for agent: {sender_id}")
                raise HTTPException(
                    status_code=401,
                    detail="Sender public key not found. Peer not configured.",
                )

            response_data = await self.agent.process(
                message,
                sender_public_key,
            )
            log.info("Task processed successfully. Sending result.")

            identity = self.agent.identity

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
        log.info(f"Starting agent server on port: {listen_port}")
        run(self.app, host="0.0.0.0", port=listen_port)

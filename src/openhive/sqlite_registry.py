import sqlite3
import json
from typing import List, Optional

from .agent_registry import AgentRegistry, QueryParser
from .types import AgentInfo, AgentKeys, AgentCapability
from .log import get_logger

log = get_logger(__name__)


class SqliteRegistry(AgentRegistry):
    def __init__(self, name: str, endpoint: str):
        self._name = name
        self._endpoint = endpoint
        self._conn = sqlite3.connect(endpoint)
        self._conn.row_factory = sqlite3.Row
        self._create_table()
        log.info(f"SQLite registry '{name}' initialized at {endpoint}")

    def _create_table(self):
        cursor = self._conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                version TEXT,
                endpoint TEXT,
                capabilities TEXT,
                public_key TEXT
            )
        ''')
        self._conn.commit()

    @property
    def name(self) -> str:
        return self._name

    @property
    def endpoint(self) -> str:
        return self._endpoint

    async def add(self, agent_info: AgentInfo):
        log.info(f"Adding agent {agent_info.id} to registry '{self.name}'")
        cursor = self._conn.cursor()
        cursor.execute(
            'INSERT INTO agents (id, name, description, version, endpoint, capabilities, public_key) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                agent_info.id,
                agent_info.name,
                agent_info.description,
                agent_info.version,
                agent_info.endpoint,
                json.dumps([cap.dict() for cap in agent_info.capabilities]),
                agent_info.keys.public_key,
            ),
        )
        self._conn.commit()

    async def get(self, agent_id: str) -> Optional[AgentInfo]:
        log.info(f"Getting agent {agent_id} from registry '{self.name}'")
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
        row = cursor.fetchone()
        if not row:
            log.warning(f"Agent {agent_id} not found in registry '{self.name}'")
            return None
        return self._row_to_agent_info(row)

    async def remove(self, agent_id: str):
        log.info(f"Removing agent {agent_id} from registry '{self.name}'")
        cursor = self._conn.cursor()
        cursor.execute('DELETE FROM agents WHERE id = ?', (agent_id,))
        self._conn.commit()

    async def list(self) -> List[AgentInfo]:
        log.info(f"Listing all agents in registry '{self.name}'")
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM agents')
        rows = cursor.fetchall()
        return [self._row_to_agent_info(row) for row in rows]

    async def update(self, agent_info: AgentInfo):
        log.info(f"Updating agent {agent_info.id} in registry '{self.name}'")
        cursor = self._conn.cursor()
        cursor.execute(
            '''
            UPDATE agents
            SET name = ?, description = ?, version = ?, endpoint = ?, capabilities = ?, public_key = ?
            WHERE id = ?
            ''',
            (
                agent_info.name,
                agent_info.description,
                agent_info.version,
                agent_info.endpoint,
                json.dumps([cap.dict() for cap in agent_info.capabilities]),
                agent_info.keys.public_key,
                agent_info.id,
            ),
        )
        self._conn.commit()
        
    async def search(self, query: str) -> List[AgentInfo]:
        log.info(f"Searching for '{query}' in registry '{self.name}'")
        # Naive in-memory search. For larger datasets, consider full-text search in SQLite.
        agents = await self.list()
        
        if not query or not query.strip():
            log.info("Empty query, returning all agents")
            return agents
            
        parsed_query = QueryParser.parse(query)

        def matches(agent: AgentInfo) -> bool:
            general_match = (
                not parsed_query.general_filters or
                all(
                    any(
                        filter.term.lower() in getattr(agent, field, '').lower()
                        for field in filter.fields
                        if isinstance(getattr(agent, field, None), str)
                    )
                    for filter in parsed_query.general_filters
                )
            )

            field_match = (
                not parsed_query.field_filters or
                all(
                    (
                        filter.value.lower() in getattr(agent, filter.field, '').lower()
                        if filter.operator == 'includes' and isinstance(getattr(agent, filter.field, None), str)
                        else any(
                            cap.id.lower() == filter.value.lower()
                            for cap in agent.capabilities
                        )
                    )
                    for filter in parsed_query.field_filters
                )
            )

            return general_match and field_match

        results = [agent for agent in agents if matches(agent)]
        log.info(f"Search for '{query}' returned {len(results)} results")
        return results

    def _row_to_agent_info(self, row: sqlite3.Row) -> AgentInfo:
        return AgentInfo(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            version=row['version'],
            endpoint=row['endpoint'],
            capabilities=[AgentCapability(**cap) for cap in json.loads(row['capabilities'])],
            keys=AgentKeys(publicKey=row['public_key']),
        )

import sqlite3
import json
import uuid
from typing import List, Optional

from .agent_registry import AgentRegistry
from .types import AgentCard, Skill
from .log import get_logger
from .query_parser import QueryParser


log = get_logger(__name__)


class SqliteRegistry(AgentRegistry):
    def __init__(self, db_path: str, query_parser: Optional[QueryParser] = None):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._query_parser = query_parser or QueryParser()
        self._create_table()
        log.info(f"SQLite registry initialized at {db_path}")

    def _create_table(self):
        cursor = self._conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                protocolVersion TEXT,
                version TEXT,
                url TEXT,
                skills TEXT
            )
        ''')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_name ON agents (name)')
        self._conn.commit()

    async def add(self, agent: AgentCard) -> AgentCard:
        if not agent.id:
            agent.id = str(uuid.uuid4())
        log.info(f"Adding agent {agent.name} ({agent.id}) to SQLite registry")
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO agents (id, name, description, protocolVersion, version, url, skills) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (
                    agent.id,
                    agent.name,
                    agent.description,
                    agent.protocol_version,
                    agent.version,
                    agent.url,
                    json.dumps([s.dict() for s in agent.skills]),
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"Agent with name {agent.name} already exists.")
        return agent

    async def get(self, agent_id: str) -> Optional[AgentCard]:
        log.info(f"Getting agent {agent_id} from SQLite registry")
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_agent(row)

    async def delete(self, agent_id: str) -> None:
        log.info(f"Removing agent {agent_id} from SQLite registry")
        cursor = self._conn.cursor()
        cursor.execute('DELETE FROM agents WHERE id = ?', (agent_id,))
        self._conn.commit()

    async def list(self) -> List[AgentCard]:
        log.info(f"Listing all agents from SQLite registry")
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM agents')
        rows = cursor.fetchall()
        return [self._row_to_agent(row) for row in rows]

    async def update(self, agent_id: str, agent: AgentCard) -> AgentCard:
        log.info(f"Updating agent {agent_id} in SQLite registry")
        cursor = self._conn.cursor()
        cursor.execute(
            '''
            UPDATE agents
            SET name = ?, description = ?, protocolVersion = ?, version = ?, url = ?, skills = ?
            WHERE id = ?
            ''',
            (
                agent.name,
                agent.description,
                agent.protocol_version,
                agent.version,
                agent.url,
                json.dumps([s.dict() for s in agent.skills]),
                agent_id,
            ),
        )
        self._conn.commit()
        return agent
        
    async def search(self, query: str) -> List[AgentCard]:
        log.info(f"Searching for '{query}' in SQLite registry")
        agents = await self.list()

        if not query or not query.strip():
            return agents

        parsed_query = self._query_parser.parse(query)

        if not parsed_query.field_filters and not parsed_query.general_filters:
            return agents

        # Apply field filters
        for f in parsed_query.field_filters:
            if f.operator == 'has_skill':
                agents = [
                    agent for agent in agents
                    if any(
                        s.id.lower() == f.value.lower() or s.name.lower() == f.value.lower()
                        for s in agent.skills
                    )
                ]
            else:
                agents = [
                    agent for agent in agents
                    if hasattr(agent, f.field) and f.value.lower() in str(getattr(agent, f.field)).lower()
                ]

        # Apply general text search filters
        for f in parsed_query.general_filters:
            agents = [
                agent for agent in agents
                if any(
                    hasattr(agent, field) and f.term.lower() in str(getattr(agent, field)).lower()
                    for field in f.fields
                )
            ]
            
        return agents

    async def clear(self) -> None:
        log.info("Clearing all agents from SQLite registry")
        cursor = self._conn.cursor()
        cursor.execute('DELETE FROM agents')
        self._conn.commit()

    async def close(self) -> None:
        log.info("Closing SQLite registry connection")
        self._conn.close()

    def _row_to_agent(self, row: sqlite3.Row) -> AgentCard:
        return AgentCard(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            protocolVersion=row['protocolVersion'],
            version=row['version'],
            url=row['url'],
            skills=[Skill(**s) for s in json.loads(row['skills'])],
        )

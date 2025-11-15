import sqlite3
import json
from typing import List, Optional

from .agent_registry import AgentRegistryAdapter
from .types import AgentRegistryEntry, Skill
from .log import get_logger

log = get_logger(__name__)


class SqliteRegistry(AgentRegistryAdapter):
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_table()
        log.info(f"SQLite registry initialized at {db_path}")

    def _create_table(self):
        cursor = self._conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                name TEXT PRIMARY KEY,
                description TEXT,
                protocolVersion TEXT,
                version TEXT,
                url TEXT,
                skills TEXT
            )
        ''')
        self._conn.commit()

    async def add(self, agent: AgentRegistryEntry) -> AgentRegistryEntry:
        agent_id = agent.name
        log.info(f"Adding agent {agent_id} to SQLite registry")
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO agents (name, description, protocolVersion, version, url, skills) VALUES (?, ?, ?, ?, ?, ?)',
                (
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
            raise ValueError(f"Agent with name {agent_id} already exists.")
        return agent

    async def get(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        log.info(f"Getting agent {agent_id} from SQLite registry")
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM agents WHERE name = ?', (agent_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_agent(row)

    async def remove(self, agent_id: str) -> None:
        log.info(f"Removing agent {agent_id} from SQLite registry")
        cursor = self._conn.cursor()
        cursor.execute('DELETE FROM agents WHERE name = ?', (agent_id,))
        self._conn.commit()

    async def list(self) -> List[AgentRegistryEntry]:
        log.info(f"Listing all agents from SQLite registry")
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM agents')
        rows = cursor.fetchall()
        return [self._row_to_agent(row) for row in rows]

    async def update(self, agent_id: str, agent: AgentRegistryEntry) -> AgentRegistryEntry:
        log.info(f"Updating agent {agent_id} in SQLite registry")
        cursor = self._conn.cursor()
        cursor.execute(
            '''
            UPDATE agents
            SET description = ?, protocolVersion = ?, version = ?, url = ?, skills = ?
            WHERE name = ?
            ''',
            (
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
        
    async def search(self, query: str) -> List[AgentRegistryEntry]:
        log.info(f"Searching for '{query}' in SQLite registry")
        # For production, consider SQLite's FTS5 extension for better performance
        agents = await self.list()
        
        if not query or not query.strip():
            return agents
            
        lower_case_query = query.lower()

        def matches(agent: AgentRegistryEntry) -> bool:
            name_match = agent.name.lower().find(lower_case_query) != -1
            description_match = agent.description and agent.description.lower().find(lower_case_query) != -1
            skill_match = any(
                s.id.lower().find(lower_case_query) != -1 or
                s.name.lower().find(lower_case_query) != -1 or
                (s.description and s.description.lower().find(lower_case_query) != -1)
                for s in agent.skills
            )
            return name_match or description_match or skill_match

        return [agent for agent in agents if matches(agent)]

    async def clear(self) -> None:
        log.info("Clearing all agents from SQLite registry")
        cursor = self._conn.cursor()
        cursor.execute('DELETE FROM agents')
        self._conn.commit()

    async def close(self) -> None:
        log.info("Closing SQLite registry connection")
        self._conn.close()

    def _row_to_agent(self, row: sqlite3.Row) -> AgentRegistryEntry:
        return AgentRegistryEntry(
            name=row['name'],
            description=row['description'],
            protocolVersion=row['protocolVersion'],
            version=row['version'],
            url=row['url'],
            skills=[Skill(**s) for s in json.loads(row['skills'])],
        )

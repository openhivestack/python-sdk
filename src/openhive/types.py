from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Skill(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    input: Optional[Dict[str, Any]] = {}
    output: Optional[Dict[str, Any]] = {}


class AgentCard(BaseModel):
    id: Optional[str] = None  # Optional on creation, will be assigned by the registry
    name: str
    description: Optional[str] = None
    protocol_version: str = Field(..., alias='protocolVersion')
    version: str
    url: str
    skills: List[Skill]
    capabilities: Optional[Dict[str, bool]] = None

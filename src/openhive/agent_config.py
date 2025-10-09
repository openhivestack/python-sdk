import json
from yaml import safe_load
from .types import AgentConfigStruct


class AgentConfigError(Exception):
    pass


class AgentConfig:
    def __init__(self, config_data: dict):
        self._config = AgentConfigStruct(**config_data)

    @classmethod
    def from_json(cls, file_path: str) -> 'AgentConfig':
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        return cls(config_data)

    @classmethod
    def from_yaml(cls, file_path: str) -> 'AgentConfig':
        with open(file_path, 'r') as f:
            config_data = safe_load(f)
        return cls(config_data)

    @property
    def id(self) -> str:
        return self._config.id

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def description(self) -> str:
        return self._config.description

    @property
    def version(self) -> str:
        return self._config.version

    @property
    def endpoint(self) -> str:
        return self._config.endpoint

    @property
    def capabilities(self):
        return self._config.capabilities

    def has_capability(self, capability_id: str) -> bool:
        return any(cap.id == capability_id for cap in self._config.capabilities)

    def to_dict(self):
        return self._config.dict(by_alias=True)

    def info(self):
        return self._config.dict(
            by_alias=True,
            exclude={'log_level', 'public_key'}
        )

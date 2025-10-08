import os
import yaml
from pydantic import ValidationError
from .types import AgentConfig


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, file_path: str = None):
        if file_path is None:
            file_path = os.path.join(os.getcwd(), '.hive.yml')
        
        if not os.path.exists(file_path):
            raise ConfigError(f"Configuration file not found at: {file_path}")

        try:
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            self._config = AgentConfig(**config_data)

        except yaml.YAMLError as e:
            raise ConfigError(f"Error parsing YAML file: {e}")
        except ValidationError as e:
            raise ConfigError(f"Configuration validation error: {e}")
        except Exception as e:
            raise ConfigError(f"An unexpected error occurred while loading config: {e}")

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
    def port(self) -> int:
        return self._config.port

    @property
    def capabilities(self):
        return self._config.capabilities

    def has_capability(self, capability_id: str) -> bool:
        return any(cap.id == capability_id for cap in self.capabilities)

    def get_full_config(self) -> AgentConfig:
        return self._config

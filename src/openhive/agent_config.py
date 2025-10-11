import yaml
import os
import base64
from typing import Dict, Any
from dotenv import load_dotenv
from jinja2 import Template
from .types import AgentConfigStruct
from .agent_error import AgentError


def _pad_base64(data):
    """Pad base64 data if necessary."""
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return data


class AgentConfig:
    def __init__(self, config_data: dict | str):
        if isinstance(config_data, str):
            config_data = self.load(config_data)
        
        try:
            self._config = AgentConfigStruct(**config_data)
        except Exception as e:
            raise AgentError(f"Configuration validation failed: {e}")

    def load(self, file_path: str) -> Dict[str, Any]:
        try:
            load_dotenv()

            with open(file_path, 'r') as f:
                content = f.read()

            template = Template(content)
            rendered_content = template.render(env=os.environ)
            
            config_dict = yaml.safe_load(rendered_content)
            
            if 'keys' not in config_dict or 'publicKey' not in config_dict['keys'] or 'privateKey' not in config_dict['keys']:
                raise ValueError("Missing required fields: keys.publicKey or keys.privateKey")

            padded_public_key = _pad_base64(config_dict['keys']['publicKey'])
            config_dict['keys']['publicKey'] = base64.b64decode(
                padded_public_key.encode('utf-8')
            ).decode('utf-8')
            
            padded_private_key = _pad_base64(config_dict['keys']['privateKey'])
            config_dict['keys']['privateKey'] = base64.b64decode(
                padded_private_key.encode('utf-8')
            ).decode('utf-8')
            
            return config_dict

        except (IOError, yaml.YAMLError) as e:
            raise AgentError(f"Failed to load or parse YAML configuration: {e}")
        except (ValueError, base64.binascii.Error) as e:
            raise AgentError(f"Key validation or decoding failed: {e}")

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
        
    @property
    def keys(self) -> Dict[str, str]:
        return self._config.keys

    def has_capability(self, capability_id: str) -> bool:
        return any(cap.id == capability_id for cap in self._config.capabilities)

    def to_dict(self):
        return self._config.model_dump(by_alias=True)

    def info(self):
        return self._config.model_dump(
            by_alias=True,
            exclude={'log_level', 'keys'}
        )

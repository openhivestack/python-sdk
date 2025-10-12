import yaml
import os
from urllib.parse import urlparse
import base64
from typing import Dict, Any
from dotenv import load_dotenv
from jinja2 import Template
from .types import AgentConfigStruct
from .agent_error import AgentError


class AgentConfig:
    def __init__(self, config_data: dict | str):
        if isinstance(config_data, str):
            config_data = self.load(config_data)
        try:
            self._config = AgentConfigStruct(**config_data)
        except Exception as e:
            raise AgentError(f"Configuration validation failed: {e}") from e

    def load(self, file_path: str) -> Dict[str, Any]:
        try:
            load_dotenv()

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            template = Template(content)
            rendered_content = template.render(env=os.environ)
            config_dict = yaml.safe_load(rendered_content)

            if (
                'keys' not in config_dict
                or 'publicKey' not in config_dict['keys']
                or 'privateKey' not in config_dict['keys']
            ):
                raise ValueError(
                    "Missing required fields: keys.publicKey or keys.privateKey"
                )

            config_dict['keys']['publicKey'] = base64.b64decode(
                config_dict['keys']['publicKey']
            ).decode('utf-8')
            config_dict['keys']['privateKey'] = base64.b64decode(
                config_dict['keys']['privateKey']
            ).decode('utf-8')

            endpoint = config_dict.get('endpoint')
            if not endpoint:
                raise ValueError("Missing required field: endpoint")

            parsed_endpoint = urlparse(endpoint)
            config_dict['host'] = config_dict.get('host') or parsed_endpoint.netloc
            config_dict['port'] = config_dict.get('port') or parsed_endpoint.port
            return config_dict

        except (IOError, yaml.YAMLError) as e:
            raise AgentError(
                f"Failed to load or parse YAML configuration: {e}"
            ) from e
        except (ValueError, base64.binascii.Error) as e:
            raise AgentError(f"Key validation or decoding failed: {e}") from e

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
    def host(self) -> str:
        return self._config.host

    @property
    def port(self) -> int:
        return self._config.port

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

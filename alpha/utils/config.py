"""
Alpha - Configuration Management

Load and manage configuration from YAML files and environment variables.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ModelConfig:
    """Individual model configuration."""
    max_tokens: int = 4096
    temperature: float = 0.7
    difficulty_range: List[str] = None


@dataclass
class LLMProviderConfig:
    """LLM provider configuration."""
    api_key: str
    model: str = None
    base_url: str = None
    max_tokens: int = 4096
    temperature: float = 0.7
    default_model: str = None
    auto_select_model: bool = False
    models: Dict[str, ModelConfig] = None


@dataclass
class LLMConfig:
    """LLM configuration."""
    default_provider: str
    providers: Dict[str, LLMProviderConfig]


@dataclass
class MemoryConfig:
    """Memory configuration."""
    database: str
    vector_db: str = None


@dataclass
class ToolsConfig:
    """Tools configuration."""
    enabled: List[str]
    sandbox: bool = True


@dataclass
class InterfaceConfig:
    """Interface configuration."""
    cli_enabled: bool = True
    api_enabled: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000


@dataclass
class Config:
    """Main configuration."""
    name: str
    version: str
    llm: LLMConfig
    memory: MemoryConfig
    tools: ToolsConfig
    interface: InterfaceConfig


def load_config(config_path: str = "config.yaml") -> Config:
    """
    Load configuration from YAML file.

    Environment variables can be used in the format: ${VAR_NAME}

    Args:
        config_path: Path to config file

    Returns:
        Config object
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, 'r') as f:
        raw_config = yaml.safe_load(f)

    # Replace environment variables
    raw_config = _replace_env_vars(raw_config)

    # Parse configuration
    alpha_config = raw_config.get('alpha', {})
    llm_config = raw_config.get('llm', {})
    memory_config = raw_config.get('memory', {})
    tools_config = raw_config.get('tools', {})
    interface_config = raw_config.get('interface', {})

    # Build LLM providers
    providers = {}
    for name, provider_data in llm_config.get('providers', {}).items():
        # Parse model configurations if present
        models_config = None
        if 'models' in provider_data:
            models_config = {}
            for model_name, model_data in provider_data['models'].items():
                models_config[model_name] = ModelConfig(
                    max_tokens=model_data.get('max_tokens', 4096),
                    temperature=model_data.get('temperature', 0.7),
                    difficulty_range=model_data.get('difficulty_range', [])
                )

            # Remove 'models' from provider_data before creating LLMProviderConfig
            provider_data_copy = provider_data.copy()
            provider_data_copy.pop('models')
            provider_data_copy['models'] = models_config
            providers[name] = LLMProviderConfig(**provider_data_copy)
        else:
            providers[name] = LLMProviderConfig(**provider_data)

    return Config(
        name=alpha_config.get('name', 'Alpha'),
        version=alpha_config.get('version', '0.1.0'),
        llm=LLMConfig(
            default_provider=llm_config.get('default_provider', 'openai'),
            providers=providers
        ),
        memory=MemoryConfig(**memory_config),
        tools=ToolsConfig(**tools_config),
        interface=InterfaceConfig(
            cli_enabled=interface_config.get('cli', {}).get('enabled', True),
            api_enabled=interface_config.get('api', {}).get('enabled', False),
            api_host=interface_config.get('api', {}).get('host', '0.0.0.0'),
            api_port=interface_config.get('api', {}).get('port', 8000)
        )
    )


def _replace_env_vars(config: dict) -> dict:
    """
    Replace ${VAR} with environment variables.
    Supports fallback syntax: ${VAR1:-${VAR2}} or ${VAR1:-default}
    """
    if isinstance(config, dict):
        return {k: _replace_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_replace_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
        # Extract variable expression
        expr = config[2:-1]

        # Handle fallback syntax: VAR1:-VAR2 or VAR1:-default
        if ':-' in expr:
            primary_var, fallback = expr.split(':-', 1)
            # Try primary variable first
            value = os.environ.get(primary_var)
            if value:
                return value
            # If fallback is also a variable reference
            if fallback.startswith('${') and fallback.endswith('}'):
                return _replace_env_vars(fallback)
            else:
                # Try fallback as environment variable
                fallback_value = os.environ.get(fallback)
                return fallback_value if fallback_value else fallback
        else:
            # Simple variable reference
            value = os.environ.get(expr)
            # Return value if found, otherwise return empty string for optional vars
            return value if value else ""
    else:
        return config

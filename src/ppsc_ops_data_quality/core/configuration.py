"""Read YAML mappings without accepting duplicate configuration keys."""

from pathlib import Path

import yaml


class ConfigurationLoader(yaml.SafeLoader):
    """Safe YAML with explicit, unique mapping keys (including merged keys)."""


def construct_mapping(loader: ConfigurationLoader, node: yaml.MappingNode) -> dict:
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if key in mapping:
            raise ValueError(f"Duplicate YAML configuration key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=True)
    return mapping


ConfigurationLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
)


def load_yaml(path: Path) -> dict:
    """Load one mapping, preserving YAML date/datetime values and quoted IDs."""
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=ConfigurationLoader)
    if not isinstance(value, dict):
        raise ValueError("Configuration must be a YAML mapping")
    return value

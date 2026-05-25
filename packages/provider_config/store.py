from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from packages.provider_config.catalog import default_provider_document, provider_options_payload

SECRET_MASK = "***"
CLEAR_SECRET_SENTINEL = "__CLEAR__"


def _provider_sections() -> dict:
    return default_provider_document()["providers"]


def _options_sections() -> dict:
    return provider_options_payload()["providers"]


def _known_secret_fields() -> set[str]:
    secrets: set[str] = set()
    for section in _options_sections().values():
        for provider in section["providers"].values():
            for field in provider["fields"]:
                if field.get("secret"):
                    secrets.add(field["name"])
    return secrets


def _known_json_fields() -> set[str]:
    json_fields: set[str] = set()
    for section in _options_sections().values():
        for provider in section["providers"].values():
            for field in provider["fields"]:
                if field.get("kind") == "json":
                    json_fields.add(field["name"])
    return json_fields


def _merge_payload(payload: Any, previous: dict | None = None) -> dict:
    merged = default_provider_document()
    merged_sections = merged["providers"]
    previous_sections = (previous or default_provider_document()).get("providers", {})
    incoming_sections = payload.get("providers") if isinstance(payload, dict) else None
    if not isinstance(incoming_sections, dict):
        return merged

    secret_fields = _known_secret_fields()
    json_fields = _known_json_fields()
    for section_name, section_default in merged_sections.items():
        incoming_section = incoming_sections.get(section_name)
        if not isinstance(incoming_section, dict):
            continue

        selected = incoming_section.get("selected")
        if isinstance(selected, str) and (selected == "" or selected in section_default["providers"]):
            merged_sections[section_name]["selected"] = selected

        incoming_providers = incoming_section.get("providers")
        if not isinstance(incoming_providers, dict):
            continue

        for provider_name, provider_default in section_default["providers"].items():
            incoming_provider = incoming_providers.get(provider_name)
            if not isinstance(incoming_provider, dict):
                continue

            previous_provider = (
                previous_sections.get(section_name, {})
                .get("providers", {})
                .get(provider_name, {})
            )
            for field_name in provider_default:
                if field_name not in incoming_provider:
                    continue
                value = incoming_provider.get(field_name)
                if field_name in json_fields:
                    if value == "":
                        merged_sections[section_name]["providers"][provider_name][field_name] = ""
                        continue
                    if isinstance(value, (dict, list)):
                        merged_sections[section_name]["providers"][provider_name][field_name] = value
                        continue
                    if isinstance(value, str):
                        try:
                            merged_sections[section_name]["providers"][provider_name][field_name] = json.loads(value)
                        except json.JSONDecodeError:
                            merged_sections[section_name]["providers"][provider_name][field_name] = value
                    continue
                if not isinstance(value, str):
                    continue
                if field_name in secret_fields:
                    if value == CLEAR_SECRET_SENTINEL:
                        merged_sections[section_name]["providers"][provider_name][field_name] = ""
                        continue
                    if value in {"", SECRET_MASK}:
                        previous_value = previous_provider.get(field_name)
                        if isinstance(previous_value, str) and previous_value:
                            value = previous_value
                merged_sections[section_name]["providers"][provider_name][field_name] = value
    return merged


def load_provider_config(root_dir: Path) -> dict:
    config_path = Path(root_dir) / "config" / "providers.yaml"
    if not config_path.exists():
        return default_provider_document()

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return _merge_payload(data)


def save_provider_config(root_dir: Path, payload: dict) -> None:
    root = Path(root_dir)
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "providers.yaml"
    existing = load_provider_config(root)
    normalized = validate_provider_payload(payload, previous=existing)
    temp_path = config_path.with_suffix(".yaml.tmp")
    temp_path.unlink(missing_ok=True)
    temp_path.write_text(
        yaml.safe_dump(normalized, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    temp_path.replace(config_path)


def mask_provider_config(payload: dict) -> dict:
    masked = deepcopy(payload)
    secret_fields = _known_secret_fields()
    for section in masked.get("providers", {}).values():
        for provider in section.get("providers", {}).values():
            for field_name in secret_fields:
                value = provider.get(field_name)
                if isinstance(value, str) and value:
                    provider[field_name] = SECRET_MASK
    return masked


def validate_provider_payload(payload: dict, previous: dict | None = None) -> dict:
    return _merge_payload(payload, previous=previous)

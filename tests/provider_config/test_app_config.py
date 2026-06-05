from __future__ import annotations

import json
import tempfile
from pathlib import Path

from packages.provider_config.app_config import AppConfigManager


def test_get_tts_model_default() -> None:
    """AppConfigManager 应返回默认 TTS 模型"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AppConfigManager(config_dir=tmpdir)
        config = manager.get_tts_config()
        assert config["model"] == "mimo-v2.5-tts"


def test_get_tts_voice_default() -> None:
    """AppConfigManager 应返回默认 TTS 音色"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AppConfigManager(config_dir=tmpdir)
        config = manager.get_tts_config()
        assert config["voice"] == "Mia"


def test_set_tts_model() -> None:
    """AppConfigManager 应能保存 TTS 模型"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AppConfigManager(config_dir=tmpdir)
        manager.set_tts("model", "custom-model")
        config = manager.get_tts_config()
        assert config["model"] == "custom-model"


def test_set_tts_voice() -> None:
    """AppConfigManager 应能保存 TTS 音色"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AppConfigManager(config_dir=tmpdir)
        manager.set_tts("voice", "CustomVoice")
        config = manager.get_tts_config()
        assert config["voice"] == "CustomVoice"


def test_persistence() -> None:
    """AppConfigManager 应能持久化配置到文件"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager1 = AppConfigManager(config_dir=tmpdir)
        manager1.set_tts("model", "persisted-model")

        manager2 = AppConfigManager(config_dir=tmpdir)
        config = manager2.get_tts_config()
        assert config["model"] == "persisted-model"


def test_get_nested_tts_config() -> None:
    """AppConfigManager 应能获取嵌套的 TTS 配置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AppConfigManager(config_dir=tmpdir)
        config = manager.get_tts_config()
        assert "director" in config
        assert "character" in config["director"]

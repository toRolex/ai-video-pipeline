from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULTS: dict[str, Any] = {
    "llm": {
        "provider": "deepseek",
        "model": "deepseek-v4-pro",
        "thinking": "disabled",
    },
    "tts": {
        "provider": "mimo",
        "model": "mimo-v2.5-tts",
        "voice": "Mia",
        "fallback_voice": "Dean",
        "randomize_voice": True,
        "random_voices": ["Mia", "Dean"],
        "style_prompt": "自然 清晰 适合短视频带货口播",
        "voice_design_prompt": "",
        "style_control_mode": "simple",
        "director": {
            "character": "",
            "scene": "",
            "guidance": "",
        },
        "audio_tags": {
            "enabled": False,
            "tags": "",
        },
        "audio_format": "mp3",
        "sample_rate": None,
        "bitrate": None,
        "channel": None,
        "enable_request_logging": False,
        "enable_performance_metrics": True,
        "log_audio_duration": True,
    },
    "vision": {
        "provider": "openai",
        "model": "mimo-v2.5",
    },
    "media": {
        "ffmpeg_path": "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
        "ffprobe_path": "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe",
        "subtitle_mode": "script_timed",
        "max_retry": 3,
        "retry_delay_seconds": 60,
    },
}


class AppConfigManager:
    """统一配置管理器，读写 config/app_config.json"""

    def __init__(self, config_dir: str | Path = "config") -> None:
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / "app_config.json"

    def _load(self) -> dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self, config: dict[str, Any]) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _merge_defaults(self, config: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for key, default_value in DEFAULTS.items():
            if key in config:
                if isinstance(default_value, dict) and isinstance(config[key], dict):
                    result[key] = {**default_value, **config[key]}
                else:
                    result[key] = config[key]
            else:
                result[key] = default_value
        return result

    def get_tts_config(self) -> dict[str, Any]:
        config = self._load()
        tts = config.get("tts", {})
        defaults = DEFAULTS["tts"]
        return {**defaults, **tts}

    def set_tts(self, key: str, value: Any) -> None:
        config = self._load()
        if "tts" not in config:
            config["tts"] = {}
        config["tts"][key] = value
        self._save(config)

    def get_tts_value(self, key: str, default: Any = None) -> Any:
        config = self.get_tts_config()
        return config.get(key, default)

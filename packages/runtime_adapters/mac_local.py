from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from packages.runtime_adapters.base import BaseRuntimeAdapter


class MacLocalRuntimeAdapter(BaseRuntimeAdapter):
    """Runtime adapter for macOS development environment.

    Locates ffmpeg by probing, in order:
      1. ``FFMPEG_PATH`` environment variable
      2. ``brew --prefix ffmpeg`` output
      3. ``tools/bin/ffmpeg`` relative to CWD
      4. ``shutil.which("ffmpeg")`` (system PATH)
    """

    profile_name = "mac-local"

    def ensure_tools(self) -> None:
        return None

    def ffmpeg_path(self) -> Path:
        # 1. Explicit env var
        env = os.environ.get("FFMPEG_PATH")
        if env is not None:
            path = Path(env)
            if path.exists():
                return path

        # 2. Homebrew
        try:
            brew_prefix = subprocess.check_output(
                ["brew", "--prefix", "ffmpeg"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            path = Path(brew_prefix) / "bin" / "ffmpeg"
            if path.exists():
                return path
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # 3. tools/bin
        local = Path("tools/bin/ffmpeg")
        if local.exists():
            return local

        # 4. System PATH
        which = shutil.which("ffmpeg")
        if which:
            return Path(which)

        raise FileNotFoundError(
            "ffmpeg not found. Install via 'brew install ffmpeg' "
            "or set FFMPEG_PATH env var"
        )

    def attempt_root(self, workspace_root: Path, attempt_id: str) -> Path:
        root = workspace_root / "attempts" / attempt_id
        root.mkdir(parents=True, exist_ok=True)
        return root

    def build_fake_outputs(self, attempt_root: Path) -> list[Path]:
        output_root = attempt_root / "output"
        output_root.mkdir(parents=True, exist_ok=True)
        files = {
            "script.json": b"{}\n",
            "audio.mp3": b"stub-audio",
            "subtitles.srt": b"1\n00:00:00,000 --> 00:00:01,000\nstub\n",
            "final.mp4": b"stub-video",
        }
        paths: list[Path] = []
        for name, content in files.items():
            path = output_root / name
            path.write_bytes(content)
            paths.append(path)
        return paths

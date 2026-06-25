"""Tests for PhaseOrchestrator — script_generating migration (Slice 1)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from packages.domain_core.models import ArtifactPointer
from packages.pipeline_services.phase_orchestrator import (
    PhaseContext,
    PhaseOrchestrator,
    to_url_path,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_root(tmp_path: Path) -> Path:
    """Create a minimal root_dir layout (workspace/projects/...)."""
    return tmp_path


@pytest.fixture()
def project_dir(tmp_root: Path) -> Path:
    d = tmp_root / "workspace" / "projects" / "proj-001"
    d.mkdir(parents=True)
    return d


@pytest.fixture()
def ctx(project_dir: Path, tmp_root: Path) -> PhaseContext:
    return PhaseContext(
        job_id="job-001",
        project_dir=project_dir,
        root_dir=tmp_root,
        product="羊肚菌",
        options={},
    )


@pytest.fixture()
def orchestrator() -> PhaseOrchestrator:
    bridge = MagicMock()
    subtitle_svc = MagicMock()
    video_svc = MagicMock()
    tts_provider = MagicMock()
    schedule_store = MagicMock()
    return PhaseOrchestrator(
        script_bridge=bridge,
        subtitle_svc=subtitle_svc,
        video_svc=video_svc,
        tts_provider=tts_provider,
        schedule_store=schedule_store,
    )


# ---------------------------------------------------------------------------
# PhaseContext
# ---------------------------------------------------------------------------

class TestPhaseContext:
    def test_fields(self, ctx: PhaseContext, project_dir: Path, tmp_root: Path):
        assert ctx.job_id == "job-001"
        assert ctx.project_dir == project_dir
        assert ctx.root_dir == tmp_root
        assert ctx.product == "羊肚菌"
        assert ctx.options == {}

    def test_options_carries_manual_script(self, project_dir: Path, tmp_root: Path):
        ctx = PhaseContext(
            job_id="j1",
            project_dir=project_dir,
            root_dir=tmp_root,
            product="test",
            options={"manual_script": "手动文案"},
        )
        assert ctx.options["manual_script"] == "手动文案"


# ---------------------------------------------------------------------------
# to_url_path helper
# ---------------------------------------------------------------------------

class TestToUrlPath:
    def test_posix(self, tmp_path: Path):
        workspace = tmp_path / "workspace"
        file_path = workspace / "projects" / "p" / "runtime" / "jobs" / "j1" / "口播文案.txt"
        assert to_url_path(file_path, workspace) == "projects/p/runtime/jobs/j1/口播文案.txt"

    def test_slash_separated(self, tmp_path: Path):
        workspace = tmp_path / "workspace"
        file_path = workspace / "a" / "b" / "c.txt"
        assert to_url_path(file_path, workspace) == "a/b/c.txt"


# ---------------------------------------------------------------------------
# PhaseOrchestrator construction
# ---------------------------------------------------------------------------

class TestPhaseOrchestratorInit:
    def test_accepts_five_deps(self):
        orch = PhaseOrchestrator(
            script_bridge=MagicMock(),
            subtitle_svc=MagicMock(),
            video_svc=MagicMock(),
            tts_provider=MagicMock(),
            schedule_store=MagicMock(),
        )
        assert orch._script_bridge is not None
        assert orch._subtitle_svc is not None
        assert orch._video_svc is not None
        assert orch._tts_provider is not None
        assert orch._schedule_store is not None

    def test_has_handler_map(self):
        orch = PhaseOrchestrator(*[MagicMock()] * 5)
        assert isinstance(orch._handlers, dict)
        assert "script_generating" in orch._handlers


# ---------------------------------------------------------------------------
# run_phase dispatch
# ---------------------------------------------------------------------------

class TestRunPhase:
    def test_unknown_phase_raises(self, orchestrator: PhaseOrchestrator, ctx: PhaseContext):
        with pytest.raises(ValueError, match="Unknown phase"):
            orchestrator.run_phase("bogus_phase", ctx)

    def test_known_phase_returns_list(self, orchestrator: PhaseOrchestrator, ctx: PhaseContext):
        """run_phase with script_generating should return a list (even if empty)."""
        result = orchestrator.run_phase("script_generating", ctx)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# _run_script — manual_script path
# ---------------------------------------------------------------------------

class TestRunScriptManual:
    def test_manual_script_writes_files_and_returns_artifacts(
        self,
        orchestrator: PhaseOrchestrator,
        ctx: PhaseContext,
    ):
        ctx.options["manual_script"] = "这是手动输入的文案内容。"

        artifacts = orchestrator.run_phase("script_generating", ctx)

        assert len(artifacts) == 2
        kinds = {a.kind for a in artifacts}
        assert kinds == {"script"}
        for a in artifacts:
            assert isinstance(a, ArtifactPointer)
            assert a.url.startswith("/workspace/")
            assert a.size_bytes > 0

        # Verify the files were written
        job_dir = ctx.project_dir / "runtime" / "jobs" / ctx.job_id
        txt_path = job_dir / "口播文案.txt"
        json_path = job_dir / "口播文案.json"
        assert txt_path.exists()
        assert txt_path.read_text(encoding="utf-8") == "这是手动输入的文案内容。"
        assert json_path.exists()
        jdata = json.loads(json_path.read_text(encoding="utf-8"))
        assert jdata["text"] == "这是手动输入的文案内容。"
        assert jdata["source"] == "manual"


# ---------------------------------------------------------------------------
# _run_script — LLM generation path
# ---------------------------------------------------------------------------

class TestRunScriptLLM:
    def test_llm_generation_calls_bridge_and_returns_artifacts(
        self,
        orchestrator: PhaseOrchestrator,
        ctx: PhaseContext,
    ):
        job_dir = ctx.project_dir / "runtime" / "jobs" / ctx.job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        txt_path = job_dir / "口播文案.txt"
        json_path = job_dir / "口播文案.json"
        txt_path.write_text("LLM生成的文案", encoding="utf-8")
        json_path.write_text("{}", encoding="utf-8")

        orchestrator._script_bridge.generate.return_value = {
            "txt_path": str(txt_path),
            "json_path": str(json_path),
            "final_script": "LLM生成的文案",
        }

        artifacts = orchestrator.run_phase("script_generating", ctx)

        orchestrator._script_bridge.generate.assert_called_once_with(
            product="羊肚菌", output_dir=job_dir, mock=False,
        )
        assert len(artifacts) == 2
        assert all(isinstance(a, ArtifactPointer) for a in artifacts)


# ---------------------------------------------------------------------------
# _run_script — cover title auto-generation
# ---------------------------------------------------------------------------

class TestRunScriptCoverTitle:
    @patch("packages.pipeline_services.phase_orchestrator.AppConfigManager")
    @patch("packages.pipeline_services.phase_orchestrator.ScriptGenerator")
    def test_auto_generates_cover_title_when_missing(
        self,
        mock_sg_cls: MagicMock,
        mock_acm_cls: MagicMock,
        orchestrator: PhaseOrchestrator,
        ctx: PhaseContext,
    ):
        ctx.options["manual_script"] = "手动文案测试。"

        # Set up job JSON without cover_title
        job_json_dir = ctx.project_dir / "control" / "jobs"
        job_json_dir.mkdir(parents=True, exist_ok=True)
        job_json_path = job_json_dir / f"{ctx.job_id}.json"
        job_json_path.write_text(
            json.dumps({"job_id": ctx.job_id, "phase": "script_generating"}, ensure_ascii=False),
            encoding="utf-8",
        )

        # Mock ScriptGenerator
        mock_gen = MagicMock()
        mock_sg_cls.return_value = mock_gen
        mock_gen.generate_cover_title.return_value = {"text": "羊肚菌美味", "highlight_words": ["羊肚菌"]}

        orchestrator.run_phase("script_generating", ctx)

        mock_gen.generate_cover_title.assert_called_once()
        # Verify job JSON was updated with cover_title
        updated = json.loads(job_json_path.read_text(encoding="utf-8"))
        assert updated["cover_title"]["text"] == "羊肚菌美味"

    @patch("packages.pipeline_services.phase_orchestrator.AppConfigManager")
    @patch("packages.pipeline_services.phase_orchestrator.ScriptGenerator")
    def test_skips_cover_title_when_already_set(
        self,
        mock_sg_cls: MagicMock,
        mock_acm_cls: MagicMock,
        orchestrator: PhaseOrchestrator,
        ctx: PhaseContext,
    ):
        ctx.options["manual_script"] = "手动文案测试。"

        job_json_dir = ctx.project_dir / "control" / "jobs"
        job_json_dir.mkdir(parents=True, exist_ok=True)
        job_json_path = job_json_dir / f"{ctx.job_id}.json"
        job_json_path.write_text(
            json.dumps({
                "job_id": ctx.job_id,
                "phase": "script_generating",
                "cover_title": {"text": "已有标题"},
            }, ensure_ascii=False),
            encoding="utf-8",
        )

        orchestrator.run_phase("script_generating", ctx)

        mock_sg_cls.assert_not_called()

    @patch("packages.pipeline_services.phase_orchestrator.AppConfigManager")
    @patch("packages.pipeline_services.phase_orchestrator.ScriptGenerator")
    def test_cover_title_error_does_not_propagate(
        self,
        mock_sg_cls: MagicMock,
        mock_acm_cls: MagicMock,
        orchestrator: PhaseOrchestrator,
        ctx: PhaseContext,
        capsys: pytest.CaptureFixture,
    ):
        ctx.options["manual_script"] = "手动文案。"

        job_json_dir = ctx.project_dir / "control" / "jobs"
        job_json_dir.mkdir(parents=True, exist_ok=True)
        job_json_path = job_json_dir / f"{ctx.job_id}.json"
        job_json_path.write_text(
            json.dumps({"job_id": ctx.job_id}, ensure_ascii=False),
            encoding="utf-8",
        )

        mock_sg_cls.side_effect = RuntimeError("LLM down")

        # Should not raise
        artifacts = orchestrator.run_phase("script_generating", ctx)
        assert isinstance(artifacts, list)


# ---------------------------------------------------------------------------
# _job_dir helper
# ---------------------------------------------------------------------------

class TestJobDir:
    def test_returns_correct_path(self, orchestrator: PhaseOrchestrator, ctx: PhaseContext):
        expected = ctx.project_dir / "runtime" / "jobs" / ctx.job_id
        assert orchestrator._job_dir(ctx) == expected

    def test_creates_dir(self, orchestrator: PhaseOrchestrator, ctx: PhaseContext):
        d = orchestrator._job_dir(ctx)
        assert d.exists()

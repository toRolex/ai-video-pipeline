import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from apps.control_plane.routes.api_jobs import router as api_jobs_router
from apps.control_plane.routes.api_projects import router as api_projects_router
from apps.control_plane.routes.api_schedule import router as api_schedule_router
from apps.control_plane.routes.config import router as config_router
from apps.control_plane.routes.jobs import router as jobs_router
from apps.control_plane.routes.projects import router as projects_router
from apps.control_plane.routes.reviews import router as reviews_router
from apps.control_plane.routes.workers import router as workers_router
from apps.control_plane.services.dispatch import Dispatcher
from packages.domain_core.state import next_phase
from packages.file_store.repository import FileStoreRepository

REVIEW_PHASES = {"script_review", "asset_review", "final_review"}
AUTO_TICK_INTERVAL = 3  # seconds between auto-advances in dev mode


async def _auto_tick(root_dir: Path):
    """Dev-mode background loop: scans disk for non-review jobs and advances them."""
    while True:
        await asyncio.sleep(AUTO_TICK_INTERVAL)
        try:
            projects_root = root_dir / "workspace" / "projects"
            if not projects_root.exists():
                continue

            for project_dir in sorted(projects_root.iterdir()):
                if not project_dir.is_dir():
                    continue
                jobs_dir = project_dir / "control" / "jobs"
                if not jobs_dir.exists():
                    continue

                for f in sorted(jobs_dir.glob("*.json")):
                    try:
                        import json
                        data = json.loads(f.read_text(encoding="utf-8"))
                        job_id = data.get("job_id", "")
                        current = data.get("phase", "")

                        if not job_id or current in REVIEW_PHASES:
                            continue
                        if current in ("completed", "failed", "cancelled", "paused"):
                            continue

                        if current == "queued":
                            next_p = "script_generating"
                        else:
                            try:
                                next_p = next_phase(current)
                            except ValueError:
                                next_p = "completed"

                        if next_p in REVIEW_PHASES:
                            data["phase"] = next_p
                            data["review_status"] = "pending"
                        else:
                            data["phase"] = next_p

                        f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                        print(f"[AUTO-TICK] {job_id}: {current} -> {next_p}")

                        review_path = project_dir / "reviews" / "review_events.jsonl"
                        review_path.parent.mkdir(parents=True, exist_ok=True)
                        with review_path.open("a", encoding="utf-8") as h:
                            h.write(json.dumps({
                                "job_id": job_id,
                                "event": "auto_tick",
                                "from_phase": current,
                                "to_phase": next_p,
                            }, ensure_ascii=False) + "\n")
                    except Exception as e:
                        print(f"[AUTO-TICK ERROR] {f.name}: {e}")
        except Exception as e:
            print(f"[AUTO-TICK LOOP ERROR] {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    dev_mode = os.environ.get("DEV_AUTO_TICK", "1") == "1"
    if dev_mode:
        asyncio.create_task(_auto_tick(app.state.root_dir))
    yield


def create_app(root_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Ziyuantang Control Plane", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.dispatcher = Dispatcher()
    app.state.root_dir = root_dir or Path.cwd()
    app.include_router(api_projects_router)
    app.include_router(api_jobs_router)
    app.include_router(api_schedule_router)
    app.include_router(projects_router)
    app.include_router(config_router)
    app.include_router(workers_router)
    app.include_router(jobs_router)
    app.include_router(reviews_router)

    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app

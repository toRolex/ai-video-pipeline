from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["projects"])
templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent / "templates")
)

PROJECT_DIR_PATTERN = re.compile(r"^(\d{3})(.+)$")


def _scan_projects() -> list[dict[str, object]]:
    projects: list[dict[str, object]] = []
    cwd = Path.cwd()

    for entry in sorted(cwd.iterdir()):
        if not entry.is_dir():
            continue
        m = PROJECT_DIR_PATTERN.match(entry.name)
        if not m:
            continue
        number, name = m.group(1), m.group(2)
        info: dict[str, object] = {
            "number": number,
            "name": name,
            "dir": entry.name,
        }

        # 尝试读取 task_status.json 获取进度
        status_path = entry / "task_status.json"
        if status_path.is_file():
            try:
                data = json.loads(status_path.read_text(encoding="utf-8"))
                jobs = data.get("jobs", [])
                total = len(jobs)
                completed = sum(1 for j in jobs if j.get("state") == "completed")
                info["total_jobs"] = total
                info["completed_jobs"] = completed
                info["status"] = "completed" if total and completed == total else "running"
            except Exception:
                info["status"] = "unknown"
        else:
            info["status"] = "idle"

        projects.append(info)

    return projects


@router.get("/", response_class=HTMLResponse)
def project_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="projects.html",
        context={"projects": _scan_projects()},
    )

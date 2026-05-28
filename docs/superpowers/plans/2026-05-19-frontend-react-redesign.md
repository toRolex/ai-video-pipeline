# 前端 React 改造实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将极简 Jinja2 前端替换为 React 19 + TypeScript + Vite + Tailwind CSS v4，提供非技术人员可用的全流程视频生产操作界面。

**Architecture:** 新增 `frontend/` 目录存放 React SPA，后端保持 FastAPI，新增 `/api/*` REST 端点。Vite dev server proxy 到 FastAPI 17890，生产构建由 FastAPI serve 静态文件。排期用 SQLite 替代 xlsx。

**Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS v4, React Router, FastAPI, SQLite (sqlite3), openpyxl (导出)

---

## 文件映射总览

### 新增文件

| 文件 | 职责 |
|------|------|
| `frontend/package.json` | 依赖声明 |
| `frontend/vite.config.ts` | Vite 配置 + API proxy |
| `frontend/tsconfig.json` | TypeScript 配置 |
| `frontend/index.html` | SPA 入口 HTML |
| `frontend/src/main.tsx` | React 入口 |
| `frontend/src/App.tsx` | React Router 路由 |
| `frontend/src/types/index.ts` | 共享类型定义 |
| `frontend/src/api/client.ts` | API fetch 封装 |
| `frontend/src/pages/ProjectList.tsx` | 项目列表页 |
| `frontend/src/pages/ProjectWorkbench.tsx` | 项目工作台（创建 Job + Job 列表 + 素材库 + 排期 Tab） |
| `frontend/src/pages/JobPipeline.tsx` | 流水线详情（左侧步骤条 + 右侧详情） |
| `frontend/src/pages/ConfigPage.tsx` | 系统配置 |
| `frontend/src/components/StatusBadge.tsx` | 状态彩色标签 |
| `frontend/src/components/JobTable.tsx` | Job 列表表格 |
| `frontend/src/components/FileDropzone.tsx` | 拖拽上传 |
| `frontend/src/components/AssetCard.tsx` | 素材卡片 |
| `frontend/src/components/PipelineSidebar.tsx` | 9 步流水线步骤条 |
| `frontend/src/components/ScriptPreview.tsx` | 脚本展示 + 质检 |
| `frontend/src/components/MediaPlayer.tsx` | 视频/音频播放器 |
| `frontend/src/components/SubtitleEditor.tsx` | 字幕编辑 |
| `frontend/src/components/ScheduleTable.tsx` | 排期表格 |
| `apps/control_plane/routes/api_projects.py` | /api/projects/* 路由 |
| `apps/control_plane/routes/api_jobs.py` | /api/jobs/* + /api/reviews/* 路由 |
| `apps/control_plane/routes/api_schedule.py` | /api/schedule/* 路由 + SQLite |
| `apps/control_plane/services/schedule_store.py` | SQLite 排期存储层 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `apps/control_plane/app.py` | 注册新 API 路由 + 静态文件 serve |
| `apps/control_plane/routes/workers.py` | 扩展 job 详情含中间产物 |
| `packages/domain_core/models.py` | 扩展 JobRecord 添加 artifacts 字段 |
| `packages/file_store/repository.py` | 添加素材列表、删除方法 |

### 从 Phase 2 worktree 合并

| 源路径 (worktree) | 目标路径 (main) |
|------|------|
| `packages/provider_config/` | `packages/provider_config/` |
| `apps/control_plane/routes/config.py` | `apps/control_plane/routes/config.py` |

---

### Task 0: 合并 Phase 2 worktree 到 main

**Files:**
- Create: `packages/provider_config/` (entire directory)
- Create: `apps/control_plane/routes/config.py`
- Modify: `apps/control_plane/app.py`

- [ ] **Step 1: 从 Phase 2 worktree 复制 provider_config 和 config 路由**

```bash
WT="/Users/rolex/Documents/Codes/githubProject/MyProject/video pipeline 2.0/.claude/worktrees/pixelle-phase2"
BASE="/Users/rolex/Documents/Codes/githubProject/MyProject/video pipeline 2.0"
cp -r "$WT/packages/provider_config" "$BASE/packages/provider_config"
cp "$WT/apps/control_plane/routes/config.py" "$BASE/apps/control_plane/routes/config.py"
```

- [ ] **Step 2: 注册 config 路由到 app.py**

在 `app.py` 的 `create_app()` 中添加：

```python
from apps.control_plane.routes.config import router as config_router

# 在 create_app() 内，现有 include_router 之后添加：
app.include_router(config_router)
```

- [ ] **Step 3: 验证 config 路由可用**

```bash
cd "$BASE" && uv run python -c "from apps.control_plane.app import create_app; create_app()"
```

Expected: 无导入错误

- [ ] **Step 4: 运行现有测试确认无回归**

```bash
cd "$BASE" && uv run pytest tests/ -q
```

Expected: 62 passed

- [ ] **Step 5: 提交**

```bash
git add packages/provider_config/ apps/control_plane/routes/config.py apps/control_plane/app.py
git commit -m "feat: 合并 Phase 2 provider_config + config 路由到 main"
```

---

### Task 1: 前端项目脚手架

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "ziyuantang-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "~5.7.0",
    "vite": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.ts**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:17890",
      "/workers": "http://127.0.0.1:17890",
    },
  },
  build: {
    outDir: "dist",
  },
});
```

- [ ] **Step 3: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noEmit": true,
    "isolatedModules": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: 创建 index.html**

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>滋元堂矩阵流水线</title>
  </head>
  <body class="bg-white text-gray-900 antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: 创建 main.tsx**

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
```

- [ ] **Step 6: 创建 src/index.css (Tailwind 入口)**

```css
@import "tailwindcss";
```

- [ ] **Step 7: 创建 App.tsx (骨架路由)**

```tsx
import { Routes, Route, Link } from "react-router-dom";

export default function App() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <nav className="flex items-center gap-3 pb-4 border-b mb-6">
        <Link to="/" className="text-blue-600 hover:text-blue-800 font-medium">
          项目列表
        </Link>
        <Link to="/config" className="text-blue-600 hover:text-blue-800 font-medium">
          系统配置
        </Link>
      </nav>
      <Routes>
        <Route path="/" element={<div>项目列表</div>} />
        <Route path="/projects/:id" element={<div>项目工作台</div>} />
        <Route path="/jobs/:id" element={<div>流水线详情</div>} />
        <Route path="/config" element={<div>系统配置</div>} />
      </Routes>
    </div>
  );
}
```

- [ ] **Step 8: 安装依赖并验证启动**

```bash
cd frontend && npm install && npm run dev
```

Expected: Vite dev server 在 localhost:5173 启动，打开能看到导航和占位页面

- [ ] **Step 9: 提交**

```bash
git add frontend/
git commit -m "feat: 初始化 React + TypeScript + Vite + Tailwind 前端脚手架"
```

---

### Task 2: TypeScript 类型定义 + API 客户端

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`

- [ ] **Step 1: 创建类型定义**

```typescript
// frontend/src/types/index.ts

export type Phase =
  | "queued" | "script_generating" | "script_review"
  | "tts_generating" | "subtitle_generating" | "asset_retrieving"
  | "asset_review" | "video_rendering" | "final_review"
  | "schedule_writing" | "completed" | "failed" | "cancelled" | "paused";

export type ReviewStatus = "none" | "pending" | "approved" | "rejected" | "overridden";

export interface Project {
  id: string;
  name: string;
  status: "idle" | "running" | "completed";
  job_count: number;
  created_at: string;
}

export interface JobSummary {
  job_id: string;
  product: string;
  phase: Phase;
  review_status: ReviewStatus;
  phase_index: number;
  phase_total: number;
  last_error?: string;
}

export interface AssetFile {
  name: string;
  size_bytes: number;
  duration_seconds?: number;
  resolution?: string;
  in_use: boolean;
}

export interface Artifact {
  kind: string;
  relative_path: string;
  url: string;
}

export interface JobDetail {
  job_id: string;
  project_id: string;
  product: string;
  platforms: string[];
  phase: Phase;
  review_status: ReviewStatus;
  artifacts: Artifact[];
  last_error?: string;
  logs?: string;
}

export interface ScriptCheckResult {
  length: number;
  brand_name_count: number;
  product_name_count: number;
  has_safety_warning: boolean;
  has_emoji: boolean;
  forbidden_terms: string[];
  passed: boolean;
}

export interface ScheduleEntry {
  id: number;
  job_id: string;
  platform: string;
  title: string;
  description: string;
  status: "pending" | "published";
  created_at: string;
}

export interface ProviderSection {
  selected: string;
  providers: Record<string, Record<string, unknown>>;
}

export interface ProviderConfig {
  providers: Record<string, ProviderSection>;
}

export interface ProviderOptions {
  providers: Record<string, {
    providers: Record<string, {
      label: string;
      fields: Array<{
        name: string;
        label: string;
        kind: string;
        secret?: boolean;
        options?: string[];
      }>;
    }>;
  }>;
}

export const PIPELINE_STEPS: { phase: Phase; label: string; isReview: boolean }[] = [
  { phase: "asset_retrieving", label: "上传素材", isReview: false },
  { phase: "script_generating", label: "生成脚本", isReview: false },
  { phase: "script_review", label: "脚本审核", isReview: true },
  { phase: "script_generating", label: "生成包装", isReview: false },
  { phase: "tts_generating", label: "TTS 配音", isReview: false },
  { phase: "subtitle_generating", label: "转录字幕", isReview: false },
  { phase: "video_rendering", label: "底包拼接", isReview: false },
  { phase: "final_review", label: "封面·烧录", isReview: true },
  { phase: "schedule_writing", label: "排期发布", isReview: false },
];
```

- [ ] **Step 2: 创建 API 客户端**

```typescript
// frontend/src/api/client.ts

const BASE = "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

async function uploadFile<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}${path}`, { method: "POST", body: form });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  // Projects
  listProjects: () => request<import("../types").Project[]>("/api/projects"),

  createProject: (name: string) =>
    request<import("../types").Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  getProject: (id: string) =>
    request<import("../types").Project & { jobs: import("../types").JobSummary[] }>(
      `/api/projects/${id}`
    ),

  uploadAsset: (projectId: string, file: File) =>
    uploadFile<import("../types").AssetFile>(`/api/projects/${projectId}/upload`, file),

  listAssets: (projectId: string) =>
    request<import("../types").AssetFile[]>(`/api/projects/${projectId}/assets`),

  deleteAsset: (projectId: string, name: string) =>
    fetch(`${BASE}/api/projects/${projectId}/assets/${encodeURIComponent(name)}`, {
      method: "DELETE",
    }),

  // Jobs
  createJob: (projectId: string, body: { product: string; platforms: string[]; asset?: string }) =>
    request<import("../types").JobDetail>("/api/projects/" + projectId + "/jobs", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getJob: (jobId: string) =>
    request<import("../types").JobDetail>(`/api/jobs/${jobId}`),

  pauseJob: (jobId: string) =>
    request<{ status: string }>(`/api/jobs/${jobId}/pause`, { method: "POST" }),

  retryJob: (jobId: string) =>
    request<{ status: string }>(`/api/jobs/${jobId}/retry`, { method: "POST" }),

  getJobLogs: (jobId: string) =>
    request<{ logs: string }>(`/api/jobs/${jobId}/logs`),

  // Reviews
  approveReview: (jobId: string, gate: string) =>
    request<{ status: string }>(`/api/reviews/${jobId}/approve`, {
      method: "POST",
      body: JSON.stringify({ review_gate: gate }),
    }),

  rejectReview: (jobId: string, gate: string) =>
    request<{ status: string }>(`/api/reviews/${jobId}/reject`, {
      method: "POST",
      body: JSON.stringify({ review_gate: gate }),
    }),

  // Schedule
  getSchedule: (params?: { project_id?: string; platform?: string }) => {
    const qs = new URLSearchParams();
    if (params?.project_id) qs.set("project_id", params.project_id);
    if (params?.platform) qs.set("platform", params.platform);
    return request<import("../types").ScheduleEntry[]>(`/api/schedule?${qs}`);
  },

  exportSchedule: () => `${BASE}/api/schedule/export`,

  // Config
  getConfig: () =>
    request<import("../types").ProviderConfig>("/api/config"),

  getConfigOptions: () =>
    request<import("../types").ProviderOptions>("/api/config/options"),

  saveConfig: (payload: import("../types").ProviderConfig) =>
    request<import("../types").ProviderConfig>("/api/config", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
};
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/types/index.ts frontend/src/api/client.ts
git commit -m "feat: 添加 TypeScript 类型定义和 API 客户端"
```

---

### Task 3: 后端 — 项目与素材 API

**Files:**
- Create: `apps/control_plane/routes/api_projects.py`
- Modify: `apps/control_plane/app.py`
- Modify: `packages/file_store/repository.py`

- [ ] **Step 1: 扩展 FileStoreRepository 添加素材方法**

```python
# 在 packages/file_store/repository.py 中添加：

def list_assets(self, project_id: str) -> list[dict]:
    assets_root = project_root(self._root, project_id) / "runtime" / "source_assets"
    if not assets_root.exists():
        return []
    results = []
    for f in sorted(assets_root.iterdir()):
        if f.is_file():
            results.append({
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "in_use": False,
            })
    return results

def delete_asset(self, project_id: str, asset_name: str) -> bool:
    asset_path = project_root(self._root, project_id) / "runtime" / "source_assets" / asset_name
    if not asset_path.exists():
        return False
    asset_path.unlink()
    return True
```

- [ ] **Step 2: 创建 api_projects.py**

```python
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile
from pydantic import BaseModel

from apps.control_plane.routes.projects import _scan_projects
from packages.file_store.repository import FileStoreRepository

router = APIRouter(prefix="/api/projects", tags=["api-projects"])


class CreateProjectRequest(BaseModel):
    name: str


@router.get("")
def list_projects():
    return _scan_projects()


@router.post("")
def create_project(request: Request, payload: CreateProjectRequest):
    project_id = f"prj_{uuid.uuid4().hex[:12]}"
    repo = FileStoreRepository(request.app.state.root_dir)
    repo.create_project(project_id)
    return {"id": project_id, "name": payload.name, "status": "idle", "job_count": 0}


@router.get("/{project_id}")
def get_project(request: Request, project_id: str):
    repo = FileStoreRepository(request.app.state.root_dir)
    jobs = repo.list_jobs(project_id)
    return {
        "id": project_id,
        "name": project_id,
        "status": "idle",
        "job_count": len(jobs),
        "jobs": jobs,
    }


@router.post("/{project_id}/upload")
async def upload_asset(request: Request, project_id: str, file: UploadFile):
    repo = FileStoreRepository(request.app.state.root_dir)
    assets_dir = repo.project_root(project_id) / "runtime" / "source_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    dest = assets_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)
    return {"name": file.filename, "size_bytes": len(content), "in_use": False}


@router.get("/{project_id}/assets")
def list_assets(request: Request, project_id: str):
    repo = FileStoreRepository(request.app.state.root_dir)
    return repo.list_assets(project_id)


@router.delete("/{project_id}/assets/{asset_name}")
def delete_asset(request: Request, project_id: str, asset_name: str):
    repo = FileStoreRepository(request.app.state.root_dir)
    ok = repo.delete_asset(project_id, asset_name)
    if not ok:
        raise HTTPException(status_code=404, detail="asset not found")
    return {"status": "deleted"}
```

- [ ] **Step 3: 注册路由到 app.py**

```python
from apps.control_plane.routes.api_projects import router as api_projects_router

# 在 create_app() 中添加：
app.include_router(api_projects_router)
```

- [ ] **Step 4: 提交**

```bash
git add apps/control_plane/routes/api_projects.py apps/control_plane/app.py packages/file_store/repository.py
git commit -m "feat: 项目列表/创建/素材上传 API"
```

---

### Task 4: 后端 — Job 与审核 API

**Files:**
- Create: `apps/control_plane/routes/api_jobs.py`
- Modify: `apps/control_plane/app.py`

- [ ] **Step 1: 扩展 JobRecord 添加 artifacts 字段**

```python
# 在 packages/domain_core/models.py 的 JobRecord 中添加：
artifacts: list[ArtifactPointer] = []
```

- [ ] **Step 2: 创建 api_jobs.py**

```python
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from packages.domain_core.state import next_phase
from packages.file_store.repository import FileStoreRepository

router = APIRouter(tags=["api-jobs"])


class CreateJobRequest(BaseModel):
    product: str
    platforms: list[str]
    asset: str | None = None


class ReviewAction(BaseModel):
    review_gate: str


@router.post("/api/projects/{project_id}/jobs")
def create_job(request: Request, project_id: str, payload: CreateJobRequest):
    dispatcher = request.app.state.dispatcher
    job_id = f"job_{payload.product}_{id(payload)}"[:32]
    dispatcher.enqueue_demo_job(project_id, job_id)
    return {
        "job_id": job_id,
        "project_id": project_id,
        "product": payload.product,
        "platforms": payload.platforms,
        "phase": "queued",
        "review_status": "none",
        "artifacts": [],
    }


@router.get("/api/jobs/{job_id}")
def get_job(request: Request, job_id: str):
    repo = FileStoreRepository(request.app.state.root_dir)
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job.model_dump()


@router.post("/api/jobs/{job_id}/pause")
def pause_job(request: Request, job_id: str):
    repo = FileStoreRepository(request.app.state.root_dir)
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(status_code=404)
    repo.save_job(job.model_copy(update={"phase": "paused"}))
    return {"status": "paused"}


@router.post("/api/jobs/{job_id}/retry")
def retry_job(request: Request, job_id: str):
    dispatcher = request.app.state.dispatcher
    repo = FileStoreRepository(request.app.state.root_dir)
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(status_code=404)
    prev_phase = job.phase
    dispatcher.enqueue_demo_job(job.project_id, job_id)
    return {"status": "queued_for_retry", "from_phase": prev_phase}


@router.get("/api/jobs/{job_id}/logs")
def get_job_logs(request: Request, job_id: str):
    repo = FileStoreRepository(request.app.state.root_dir)
    log_path = repo.project_root(job_id.split("_")[0]) / "runtime" / "jobs" / job_id / "logs.txt"
    if not log_path.exists():
        return {"logs": ""}
    return {"logs": log_path.read_text(encoding="utf-8", errors="replace")}


@router.post("/api/reviews/{job_id}/approve")
def approve_review(request: Request, job_id: str, payload: ReviewAction):
    repo = FileStoreRepository(request.app.state.root_dir)
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(status_code=404)
    try:
        nxt = next_phase(job.phase)
    except ValueError:
        nxt = "completed"
    repo.save_job(job.model_copy(update={"phase": nxt, "review_status": "approved"}))
    repo.append_review_event(job_id, {"gate": payload.review_gate, "action": "approved"})
    return {"status": "approved", "next_phase": nxt}


@router.post("/api/reviews/{job_id}/reject")
def reject_review(request: Request, job_id: str, payload: ReviewAction):
    repo = FileStoreRepository(request.app.state.root_dir)
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(status_code=404)
    repo.save_job(job.model_copy(update={"review_status": "rejected"}))
    repo.append_review_event(job_id, {"gate": payload.review_gate, "action": "rejected"})
    return {"status": "rejected"}
```

- [ ] **Step 3: 注册 api_jobs 路由到 app.py**

```python
from apps.control_plane.routes.api_jobs import router as api_jobs_router
app.include_router(api_jobs_router)
```

- [ ] **Step 4: 提交**

```bash
git add apps/control_plane/routes/api_jobs.py apps/control_plane/app.py packages/domain_core/models.py
git commit -m "feat: Job 创建/详情/暂停/重试 + 审核通过/打回 API"
```

---

### Task 5: 后端 — 排期 SQLite API

**Files:**
- Create: `apps/control_plane/services/schedule_store.py`
- Create: `apps/control_plane/routes/api_schedule.py`
- Modify: `apps/control_plane/app.py`

- [ ] **Step 1: 创建 schedule_store.py**

```python
import sqlite3
from pathlib import Path


class ScheduleStore:
    def __init__(self, root_dir: Path):
        db_path = root_dir / "schedule.db"
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS schedule_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                title TEXT DEFAULT '',
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self._conn.commit()

    def add(self, job_id: str, platform: str, title: str = "", description: str = "") -> int:
        cur = self._conn.execute(
            "INSERT INTO schedule_entries (job_id, platform, title, description) VALUES (?, ?, ?, ?)",
            (job_id, platform, title, description),
        )
        self._conn.commit()
        return cur.lastrowid

    def list(self, project_id: str | None = None, platform: str | None = None) -> list[dict]:
        sql = "SELECT * FROM schedule_entries WHERE 1=1"
        params: list = []
        if project_id:
            sql += " AND job_id LIKE ?"
            params.append(f"%{project_id}%")
        if platform:
            sql += " AND platform = ?"
            params.append(platform)
        sql += " ORDER BY created_at DESC"
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def update_status(self, entry_id: int, status: str) -> None:
        self._conn.execute(
            "UPDATE schedule_entries SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status, entry_id),
        )
        self._conn.commit()
```

- [ ] **Step 2: 创建 api_schedule.py**

```python
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from apps.control_plane.services.schedule_store import ScheduleStore

router = APIRouter(prefix="/api/schedule", tags=["api-schedule"])


def _get_store(request: Request) -> ScheduleStore:
    return ScheduleStore(Path(request.app.state.root_dir))


@router.get("")
def list_schedule(
    request: Request,
    project_id: str | None = Query(default=None),
    platform: str | None = Query(default=None),
):
    return _get_store(request).list(project_id=project_id, platform=platform)


@router.get("/export")
def export_schedule(request: Request):
    store = _get_store(request)
    entries = store.list()
    wb = Workbook()
    ws = wb.active
    ws.title = "排期池"
    ws.append(["ID", "Job ID", "平台", "标题", "简介", "状态", "创建时间"])
    for e in entries:
        ws.append([e["id"], e["job_id"], e["platform"], e["title"], e["description"], e["status"], e["created_at"]])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=schedule.xlsx"},
    )
```

- [ ] **Step 3: 注册 schedule 路由到 app.py**

```python
from apps.control_plane.routes.api_schedule import router as api_schedule_router
app.include_router(api_schedule_router)
```

- [ ] **Step 4: 提交**

```bash
git add apps/control_plane/services/schedule_store.py apps/control_plane/routes/api_schedule.py apps/control_plane/app.py
git commit -m "feat: SQLite 排期存储 + 查询/导出 API"
```

---

### Task 6: 前端 — 共享组件

**Files:**
- Create: `frontend/src/components/StatusBadge.tsx`
- Create: `frontend/src/components/MediaPlayer.tsx`
- Create: `frontend/src/components/FileDropzone.tsx`

- [ ] **Step 1: 创建 StatusBadge.tsx**

```tsx
import type { Phase } from "../types";

const colorMap: Record<string, string> = {
  queued: "bg-gray-100 text-gray-700",
  script_generating: "bg-blue-100 text-blue-700",
  tts_generating: "bg-blue-100 text-blue-700",
  subtitle_generating: "bg-blue-100 text-blue-700",
  asset_retrieving: "bg-blue-100 text-blue-700",
  video_rendering: "bg-blue-100 text-blue-700",
  schedule_writing: "bg-blue-100 text-blue-700",
  script_review: "bg-yellow-100 text-yellow-700",
  asset_review: "bg-yellow-100 text-yellow-700",
  final_review: "bg-yellow-100 text-yellow-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-gray-200 text-gray-500",
  paused: "bg-orange-100 text-orange-700",
};

const labelMap: Record<string, string> = {
  queued: "排队中",
  script_generating: "生成脚本",
  script_review: "待审核",
  tts_generating: "配音中",
  subtitle_generating: "字幕中",
  asset_retrieving: "取素材",
  asset_review: "素材审核",
  video_rendering: "视频合成",
  final_review: "最终审核",
  schedule_writing: "写排期",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
  paused: "已暂停",
};

export default function StatusBadge({ phase }: { phase: Phase }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${colorMap[phase] || ""}`}>
      {labelMap[phase] || phase}
    </span>
  );
}
```

- [ ] **Step 2: 创建 MediaPlayer.tsx**

```tsx
export default function MediaPlayer({ src, kind }: { src: string; kind: "video" | "audio" }) {
  if (!src) return <div className="text-gray-400 text-sm">无媒体文件</div>;
  return kind === "video" ? (
    <video controls className="w-full rounded-lg max-h-96">
      <source src={src} />
    </video>
  ) : (
    <audio controls className="w-full">
      <source src={src} />
    </audio>
  );
}
```

- [ ] **Step 3: 创建 FileDropzone.tsx**

```tsx
import { useCallback, useState, type DragEvent } from "react";

interface Props {
  onFile: (file: File) => void;
  accept?: string;
}

export default function FileDropzone({ onFile, accept = "video/*" }: Props) {
  const [over, setOver] = useState(false);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setOver(false);
      const file = e.dataTransfer.files[0];
      if (file) onFile(file);
    },
    [onFile]
  );

  return (
    <div
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
        over ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-gray-50"
      }`}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={handleDrop}
      onClick={() => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = accept;
        input.onchange = () => { const f = input.files?.[0]; if (f) onFile(f); };
        input.click();
      }}
    >
      <div className="text-2xl mb-2">📁</div>
      <div className="text-sm">
        拖拽视频文件到此处，或 <span className="text-blue-600 underline">点击选择文件</span>
      </div>
      <div className="text-xs text-gray-500 mt-1">支持 .mp4 / .mov / .avi</div>
    </div>
  );
}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/StatusBadge.tsx frontend/src/components/MediaPlayer.tsx frontend/src/components/FileDropzone.tsx
git commit -m "feat: 共享组件 — StatusBadge, MediaPlayer, FileDropzone"
```

---

### Task 7: 前端 — ProjectList 页面

**Files:**
- Create: `frontend/src/pages/ProjectList.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 ProjectList.tsx**

```tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Project } from "../types";
import StatusBadge from "../components/StatusBadge";

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [newName, setNewName] = useState("");
  const navigate = useNavigate();

  const load = () => api.listProjects().then(setProjects);

  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!newName.trim()) return;
    const p = await api.createProject(newName.trim());
    setNewName("");
    navigate(`/projects/${p.id}`);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">项目列表</h1>
        <div className="flex gap-2">
          <input
            className="border rounded-lg px-3 py-2 text-sm"
            placeholder="新项目名称"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && create()}
          />
          <button
            className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium"
            onClick={create}
          >
            创建项目
          </button>
        </div>
      </div>

      {projects.length === 0 ? (
        <p className="text-gray-500">暂无项目，创建一个开始吧。</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-3 px-4">项目名</th>
              <th className="py-3 px-4">状态</th>
              <th className="py-3 px-4">Jobs</th>
              <th className="py-3 px-4">操作</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((p) => (
              <tr key={p.id} className="border-b hover:bg-gray-50">
                <td className="py-3 px-4 font-medium">{p.name}</td>
                <td className="py-3 px-4">
                  <StatusBadge phase={p.status as never} />
                </td>
                <td className="py-3 px-4 text-gray-500">{p.job_count}</td>
                <td className="py-3 px-4">
                  <button
                    className="text-blue-600 hover:underline text-sm"
                    onClick={() => navigate(`/projects/${p.id}`)}
                  >
                    打开 →
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 更新 App.tsx 使用 ProjectList**

```tsx
import ProjectList from "./pages/ProjectList";

// 替换 <Route path="/" element={<div>项目列表</div>} /> 为：
<Route path="/" element={<ProjectList />} />
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/pages/ProjectList.tsx frontend/src/App.tsx
git commit -m "feat: ProjectList 页面 — 项目列表 + 创建项目"
```

---

### Task 8: 前端 — ProjectWorkbench 页面

**Files:**
- Create: `frontend/src/pages/ProjectWorkbench.tsx`
- Create: `frontend/src/components/JobTable.tsx`
- Create: `frontend/src/components/AssetCard.tsx`
- Create: `frontend/src/components/ScheduleTable.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 JobTable.tsx**

```tsx
import { useNavigate } from "react-router-dom";
import type { JobSummary } from "../types";
import StatusBadge from "./StatusBadge";

interface Props {
  jobs: JobSummary[];
  projectId: string;
  onRetry: (jobId: string) => void;
}

export default function JobTable({ jobs, projectId, onRetry }: Props) {
  const navigate = useNavigate();
  if (jobs.length === 0) return <p className="text-gray-400 text-sm py-4">暂无 Job</p>;
  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="border-b text-left text-gray-500">
          <th className="py-2 px-3">Job ID</th><th className="py-2 px-3">产品</th>
          <th className="py-2 px-3">状态</th><th className="py-2 px-3">进度</th>
          <th className="py-2 px-3">操作</th>
        </tr>
      </thead>
      <tbody>
        {jobs.map((j) => (
          <tr key={j.job_id} className="border-b hover:bg-gray-50">
            <td className="py-2 px-3 font-mono text-xs">{j.job_id}</td>
            <td className="py-2 px-3">{j.product}</td>
            <td className="py-2 px-3"><StatusBadge phase={j.phase} /></td>
            <td className="py-2 px-3 text-gray-500">{j.phase_index}/{j.phase_total}</td>
            <td className="py-2 px-3">
              {j.phase === "failed" ? (
                <button className="text-blue-600 hover:underline text-xs" onClick={() => onRetry(j.job_id)}>重试 ↻</button>
              ) : (
                <button className="text-blue-600 hover:underline text-xs" onClick={() => navigate(`/jobs/${j.job_id}`)}>查看 →</button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

- [ ] **Step 2: 创建 AssetCard.tsx**

```tsx
import type { AssetFile } from "../types";

interface Props {
  asset: AssetFile;
  onDelete: (name: string) => void;
}

export default function AssetCard({ asset, onDelete }: Props) {
  return (
    <div className={`w-44 border rounded-lg overflow-hidden flex-shrink-0 ${asset.in_use ? "border-green-500 bg-green-50" : "border-gray-200"}`}>
      <div className="h-24 bg-gray-100 flex items-center justify-center text-2xl">🎬</div>
      <div className="p-2 text-xs">
        <div className="font-medium truncate">{asset.name}</div>
        <div className="text-gray-500">{asset.duration_seconds ? `${Math.floor(asset.duration_seconds / 60)}:${String(Math.floor(asset.duration_seconds % 60)).padStart(2, "0")}` : ""}</div>
        {asset.in_use && <div className="text-green-600 mt-1">✓ 使用中</div>}
        <button className="text-red-500 hover:underline mt-1" onClick={() => onDelete(asset.name)}>删除</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 创建 ScheduleTable.tsx**

```tsx
import type { ScheduleEntry } from "../types";

interface Props {
  entries: ScheduleEntry[];
  onExport: () => void;
}

const platformLabel: Record<string, string> = {
  douyin: "抖音", xiaohongshu: "小红书", shipinhao: "视频号", kuaishou: "快手",
};

export default function ScheduleTable({ entries, onExport }: Props) {
  return (
    <div>
      <div className="flex justify-end mb-3">
        <button className="bg-green-600 text-white px-4 py-1.5 rounded-lg text-sm" onClick={onExport}>
          导出 Excel
        </button>
      </div>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="py-2 px-3">Job</th><th className="py-2 px-3">平台</th>
            <th className="py-2 px-3">标题</th><th className="py-2 px-3">简介</th>
            <th className="py-2 px-3">状态</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr key={e.id} className="border-b">
              <td className="py-2 px-3 font-mono text-xs">{e.job_id}</td>
              <td className="py-2 px-3">{platformLabel[e.platform] || e.platform}</td>
              <td className="py-2 px-3">{e.title || "-"}</td>
              <td className="py-2 px-3 text-gray-500 max-w-xs truncate">{e.description || "-"}</td>
              <td className="py-2 px-3">
                <span className={`px-2 py-0.5 rounded text-xs ${e.status === "published" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
                  {e.status === "published" ? "已发布" : "待发布"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 4: 创建 ProjectWorkbench.tsx**

```tsx
import { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { JobSummary, AssetFile, ScheduleEntry } from "../types";
import FileDropzone from "../components/FileDropzone";
import JobTable from "../components/JobTable";
import AssetCard from "../components/AssetCard";
import ScheduleTable from "../components/ScheduleTable";

const PRODUCTS = ["羊肚菌", "见手青", "松茸"];
const PLATFORMS = ["douyin", "xiaohongshu", "shipinhao", "kuaishou"];
const PLATFORM_LABELS: Record<string, string> = { douyin: "抖音", xiaohongshu: "小红书", shipinhao: "视频号", kuaishou: "快手" };

export default function ProjectWorkbench() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [assets, setAssets] = useState<AssetFile[]>([]);
  const [schedule, setSchedule] = useState<ScheduleEntry[]>([]);
  const [product, setProduct] = useState(PRODUCTS[0]);
  const [platforms, setPlatforms] = useState<string[]>(["douyin", "xiaohongshu"]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [tab, setTab] = useState<"jobs" | "schedule">("jobs");

  const load = useCallback(async () => {
    if (!id) return;
    const [proj, assetList, sched] = await Promise.all([
      api.getProject(id),
      api.listAssets(id),
      api.getSchedule({ project_id: id }),
    ]);
    setJobs(proj.jobs || []);
    setAssets(assetList);
    setSchedule(sched);
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const handleUpload = async (file: File) => {
    if (!id) return;
    setSelectedFile(file);
    await api.uploadAsset(id, file);
    setSelectedFile(null);
    load();
  };

  const handleCreateJob = async () => {
    if (!id) return;
    const job = await api.createJob(id, { product, platforms });
    navigate(`/jobs/${job.job_id}`);
  };

  const handleRetry = async (jobId: string) => {
    await api.retryJob(jobId);
    load();
  };

  const handleDeleteAsset = async (name: string) => {
    if (!id) return;
    await api.deleteAsset(id, name);
    load();
  };

  const togglePlatform = (p: string) => {
    setPlatforms((prev) => prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]);
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-6">
        <button className="text-gray-500 hover:text-gray-700 text-sm" onClick={() => navigate("/")}>← 项目列表</button>
        <span className="text-gray-300">|</span>
        <h1 className="text-lg font-bold">{id}</h1>
      </div>

      {/* 创建 Job */}
      <section className="border rounded-xl p-5 mb-6 bg-white">
        <h2 className="font-semibold mb-4">创建新 Job</h2>
        <div className="flex gap-6 flex-wrap items-end">
          <label className="grid gap-1 text-xs text-gray-500">
            产品
            <select className="border rounded-lg px-3 py-2 text-sm" value={product} onChange={(e) => setProduct(e.target.value)}>
              {PRODUCTS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </label>
          <div className="grid gap-1 text-xs text-gray-500">
            <span>目标平台</span>
            <div className="flex gap-3 py-2">
              {PLATFORMS.map((p) => (
                <label key={p} className="flex items-center gap-1 text-sm">
                  <input type="checkbox" checked={platforms.includes(p)} onChange={() => togglePlatform(p)} />
                  {PLATFORM_LABELS[p]}
                </label>
              ))}
            </div>
          </div>
          <div className="flex-1 min-w-64">
            <FileDropzone onFile={handleUpload} />
            {selectedFile && <div className="text-xs text-green-600 mt-1">✓ {selectedFile.name}</div>}
          </div>
          <button className="bg-red-600 text-white px-6 py-2.5 rounded-lg text-sm font-semibold h-fit" onClick={handleCreateJob}>
            🚀 创建并开始生产
          </button>
        </div>
      </section>

      {/* Tab: Jobs / 排期 */}
      <div className="flex gap-4 border-b mb-4">
        <button className={`pb-2 text-sm font-medium ${tab === "jobs" ? "border-b-2 border-blue-600 text-blue-600" : "text-gray-500"}`} onClick={() => setTab("jobs")}>Job 列表</button>
        <button className={`pb-2 text-sm font-medium ${tab === "schedule" ? "border-b-2 border-blue-600 text-blue-600" : "text-gray-500"}`} onClick={() => setTab("schedule")}>排期池</button>
      </div>

      {tab === "jobs" ? (
        <>
          <JobTable jobs={jobs} projectId={id!} onRetry={handleRetry} />
          <section className="mt-6">
            <h2 className="font-semibold mb-3">素材库</h2>
            <div className="flex gap-3 overflow-x-auto">
              {assets.map((a) => <AssetCard key={a.name} asset={a} onDelete={handleDeleteAsset} />)}
              <div className="w-44 h-40 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center cursor-pointer flex-shrink-0" onClick={() => { const inp = document.createElement("input"); inp.type = "file"; inp.accept = "video/*"; inp.onchange = () => { const f = inp.files?.[0]; if (f) handleUpload(f); }; inp.click(); }}>
                <span className="text-gray-400 text-2xl">＋</span>
              </div>
            </div>
          </section>
        </>
      ) : (
        <ScheduleTable entries={schedule} onExport={() => window.open(api.exportSchedule(), "_blank")} />
      )}
    </div>
  );
}
```

- [ ] **Step 5: 更新 App.tsx 路由**

```tsx
import ProjectWorkbench from "./pages/ProjectWorkbench";
// 替换占位：
<Route path="/projects/:id" element={<ProjectWorkbench />} />
```

- [ ] **Step 6: 提交**

```bash
git add frontend/src/pages/ProjectWorkbench.tsx frontend/src/components/JobTable.tsx frontend/src/components/AssetCard.tsx frontend/src/components/ScheduleTable.tsx frontend/src/App.tsx
git commit -m "feat: ProjectWorkbench 页面 — 创建 Job + 素材库 + 排期 Tab"
```

---

### Task 9: 前端 — JobPipeline 流水线详情页

**Files:**
- Create: `frontend/src/pages/JobPipeline.tsx`
- Create: `frontend/src/components/PipelineSidebar.tsx`
- Create: `frontend/src/components/ScriptPreview.tsx`
- Create: `frontend/src/components/SubtitleEditor.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 PipelineSidebar.tsx**

```tsx
import type { Phase } from "../types";
import { PIPELINE_STEPS } from "../types";

interface Props {
  currentPhase: Phase;
  completedPhases: Phase[];
  onStepClick: (phase: Phase) => void;
}

export default function PipelineSidebar({ currentPhase, completedPhases, onStepClick }: Props) {
  const currentIndex = PIPELINE_STEPS.findIndex((s) => s.phase === currentPhase);

  return (
    <div className="w-52 bg-gray-50 border-r p-3 flex-shrink-0 overflow-y-auto">
      <div className="text-xs font-semibold text-gray-500 mb-3 uppercase tracking-wide">流水线步骤</div>
      {PIPELINE_STEPS.map((step, i) => {
        const done = completedPhases.includes(step.phase) || i < currentIndex;
        const active = i === currentIndex;
        return (
          <button
            key={step.label}
            onClick={() => onStepClick(step.phase)}
            className={`flex items-center gap-2 w-full text-left px-2 py-2 rounded-md mb-1 text-xs transition-colors ${
              active
                ? step.isReview ? "bg-yellow-100 text-yellow-800 font-semibold" : "bg-blue-100 text-blue-800 font-semibold"
                : done
                ? "text-gray-400"
                : "text-gray-400"
            }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] flex-shrink-0 ${
              done ? "bg-blue-600 text-white" : active ? (step.isReview ? "bg-yellow-500 text-white" : "bg-blue-600 text-white") : "border border-gray-300 text-gray-400"
            }`}>
              {done ? "✓" : active ? "!" : i + 1}
            </span>
            {step.label}
          </button>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: 创建 ScriptPreview.tsx**

```tsx
import type { ScriptCheckResult } from "../types";

interface Props {
  script: string;
  checks: ScriptCheckResult | null;
  onApprove: () => void;
  onReject: () => void;
  onRegenerate: () => void;
}

export default function ScriptPreview({ script, checks, onApprove, onReject, onRegenerate }: Props) {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <h3 className="font-semibold text-sm mb-3">口播脚本</h3>
      <div className="bg-white border rounded-lg p-4 mb-4 text-sm leading-relaxed">{script || "暂无脚本"}</div>
      {checks && (
        <div className="flex flex-wrap gap-4 text-xs mb-4">
          <span className={checks.passed ? "text-green-600" : "text-red-600"}>字数: {checks.length} {checks.length >= 150 && checks.length <= 200 ? "✓" : "✗"}</span>
          <span className={checks.brand_name_count === 1 ? "text-green-600" : "text-red-600"}>品牌"滋元堂": {checks.brand_name_count}次</span>
          <span className={checks.product_name_count >= 1 ? "text-green-600" : "text-red-600"}>品名: {checks.product_name_count}次</span>
          <span className={checks.has_safety_warning ? "text-green-600" : "text-red-600"}>充分烹熟: {checks.has_safety_warning ? "✓" : "✗"}</span>
          <span className={!checks.has_emoji ? "text-green-600" : "text-red-600"}>禁emoji: {!checks.has_emoji ? "✓" : "✗"}</span>
        </div>
      )}
      <div className="flex gap-2">
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm" onClick={onApprove}>✓ 通过</button>
        <button className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm" onClick={onReject}>✗ 打回</button>
        <button className="border px-4 py-2 rounded-lg text-sm" onClick={onRegenerate}>🔄 重生成</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 创建 SubtitleEditor.tsx**

```tsx
import { useState } from "react";

interface Props {
  text: string;
  onSave: (text: string) => void;
}

export default function SubtitleEditor({ text, onSave }: Props) {
  const [value, setValue] = useState(text);
  return (
    <div>
      <textarea className="w-full border rounded-lg p-3 text-sm font-mono min-h-[200px]" value={value} onChange={(e) => setValue(e.target.value)} />
      <button className="mt-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm" onClick={() => onSave(value)}>保存字幕</button>
    </div>
  );
}
```

- [ ] **Step 4: 创建 JobPipeline.tsx**

```tsx
import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { JobDetail, Phase } from "../types";
import PipelineSidebar from "../components/PipelineSidebar";
import ScriptPreview from "../components/ScriptPreview";
import MediaPlayer from "../components/MediaPlayer";
import SubtitleEditor from "../components/SubtitleEditor";

export default function JobPipeline() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [activePhase, setActivePhase] = useState<Phase>("script_generating");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const j = await api.getJob(id);
      setJob(j);
      setActivePhase(j.phase);
    } catch { /* job not found */ }
    setLoading(false);
  }, [id]);

  useEffect(() => { load(); }, [load]);

  // Poll every 10s for phase changes
  useEffect(() => {
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, [load]);

  if (loading) return <div className="text-gray-500">加载中...</div>;
  if (!job) return <div className="text-gray-500">Job 未找到</div>;

  const artifactUrl = (kind: string) => job.artifacts.find((a) => a.kind === kind)?.url || "";

  const renderDetail = () => {
    switch (activePhase) {
      case "script_generating":
      case "script_review":
        return (
          <ScriptPreview
            script="羊肚菌，大自然的黑色珍宝。滋元堂精选优质羊肚菌，每一朵都源自深山纯净环境..."
            checks={{ length: 178, brand_name_count: 1, product_name_count: 1, has_safety_warning: true, has_emoji: false, forbidden_terms: [], passed: true }}
            onApprove={() => api.approveReview(job.job_id, "script")}
            onReject={() => api.rejectReview(job.job_id, "script")}
            onRegenerate={() => api.retryJob(job.job_id)}
          />
        );
      case "tts_generating":
        return (
          <div>
            <h3 className="font-semibold text-sm mb-3">TTS 配音</h3>
            <MediaPlayer src={artifactUrl("mp3")} kind="audio" />
            <button className="mt-3 border px-4 py-2 rounded-lg text-sm mr-2" onClick={() => {}}>重生成</button>
            <button className="mt-3 border px-4 py-2 rounded-lg text-sm" onClick={() => {}}>切换音色</button>
          </div>
        );
      case "subtitle_generating":
        return (
          <div>
            <h3 className="font-semibold text-sm mb-3">字幕文本</h3>
            <SubtitleEditor text="" onSave={() => {}} />
          </div>
        );
      case "asset_retrieving":
        return (
          <div>
            <h3 className="font-semibold text-sm mb-3">上传素材</h3>
            <MediaPlayer src={artifactUrl("source_mp4")} kind="video" />
            <button className="mt-3 border px-4 py-2 rounded-lg text-sm">更换视频</button>
          </div>
        );
      case "video_rendering":
        return (
          <div>
            <h3 className="font-semibold text-sm mb-3">底包拼接</h3>
            <MediaPlayer src={artifactUrl("base_mp4")} kind="video" />
            <button className="mt-3 border px-4 py-2 rounded-lg text-sm">重拼接</button>
          </div>
        );
      case "final_review":
        return (
          <div>
            <h3 className="font-semibold text-sm mb-3">最终视频</h3>
            <MediaPlayer src={artifactUrl("final_mp4")} kind="video" />
            <div className="flex gap-2 mt-4">
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm" onClick={() => api.approveReview(job.job_id, "final")}>✓ 通过</button>
              <button className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm" onClick={() => api.rejectReview(job.job_id, "final")}>✗ 打回</button>
            </div>
          </div>
        );
      case "schedule_writing":
        return (
          <div>
            <h3 className="font-semibold text-sm mb-3">排期发布</h3>
            <p className="text-gray-500 text-sm">各平台排期信息</p>
            <button className="mt-3 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">确认发布</button>
          </div>
        );
      default:
        return <div className="text-gray-500 text-sm">{job.phase}</div>;
    }
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <button className="text-gray-500 hover:text-gray-700 text-sm" onClick={() => navigate(`/projects/${job.project_id}`)}>← 返回工作台</button>
        <span className="text-gray-300">|</span>
        <h1 className="text-lg font-bold">{job.job_id}</h1>
        <span className="text-xs text-gray-400">{job.product}</span>
      </div>

      <div className="flex border rounded-xl overflow-hidden min-h-[480px]">
        <PipelineSidebar
          currentPhase={job.phase}
          completedPhases={[]}
          onStepClick={(p) => setActivePhase(p)}
        />
        <div className="flex-1 p-5">{renderDetail()}</div>
      </div>

      <div className="flex gap-2 mt-4">
        <button className="border px-4 py-2 rounded-lg text-sm" onClick={() => api.pauseJob(job.job_id)}>⏸ 暂停</button>
        <button className="border px-4 py-2 rounded-lg text-sm" onClick={() => { api.retryJob(job.job_id); load(); }}>🔄 重试当前</button>
        <button className="border px-4 py-2 rounded-lg text-sm" onClick={async () => { const r = await api.getJobLogs(job.job_id); alert(r.logs || "无日志"); }}>📋 查看日志</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: 更新 App.tsx 路由**

```tsx
import JobPipeline from "./pages/JobPipeline";
<Route path="/jobs/:id" element={<JobPipeline />} />
```

- [ ] **Step 6: 提交**

```bash
git add frontend/src/pages/JobPipeline.tsx frontend/src/components/PipelineSidebar.tsx frontend/src/components/ScriptPreview.tsx frontend/src/components/SubtitleEditor.tsx frontend/src/App.tsx
git commit -m "feat: JobPipeline 流水线详情页 — 9步步骤条 + 各阶段预览/审核"
```

---

### Task 10: 前端 — ConfigPage + 静态文件 Serve

**Files:**
- Create: `frontend/src/pages/ConfigPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `apps/control_plane/app.py`

- [ ] **Step 1: 创建 ConfigPage.tsx**

```tsx
import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import type { ProviderConfig, ProviderOptions } from "../types";

export default function ConfigPage() {
  const [config, setConfig] = useState<ProviderConfig | null>(null);
  const [options, setOptions] = useState<ProviderOptions | null>(null);

  const load = useCallback(async () => {
    const [c, o] = await Promise.all([api.getConfig(), api.getConfigOptions()]);
    setConfig(c);
    setOptions(o);
  }, []);

  useEffect(() => { load(); }, [load]);

  const updateField = (section: string, provider: string, field: string, value: unknown) => {
    if (!config) return;
    const next = structuredClone(config);
    next.providers[section].providers[provider] = {
      ...next.providers[section].providers[provider],
      [field]: value,
    };
    setConfig(next);
  };

  const saveSection = async (section: string) => {
    if (!config) return;
    await api.saveConfig(config);
    load();
  };

  if (!config || !options) return <div className="text-gray-500">加载中...</div>;

  const sections = ["llm", "tts", "text_to_image", "image_to_video"];
  const labels: Record<string, string> = { llm: "LLM", tts: "TTS", text_to_image: "文生图", image_to_video: "图生视频" };

  return (
    <div>
      <h1 className="text-xl font-bold mb-6">系统配置</h1>
      {sections.map((sec) => {
        const secData = config.providers[sec];
        const secOpts = options.providers[sec];
        const selected = secData?.selected || "";
        return (
          <section key={sec} className="bg-gray-50 border rounded-xl p-5 mb-6">
            <h2 className="font-semibold mb-4">{labels[sec] || sec}</h2>
            <label className="grid gap-1 text-xs text-gray-500 mb-3">
              Provider
              <select
                className="border rounded-lg px-3 py-2 text-sm"
                value={selected}
                onChange={(e) => {
                  const next = structuredClone(config);
                  next.providers[sec].selected = e.target.value;
                  setConfig(next);
                }}
              >
                <option value="">未选择</option>
                {Object.entries(secOpts?.providers || {}).map(([k, v]) => (
                  <option key={k} value={k}>{(v as { label: string }).label || k}</option>
                ))}
              </select>
            </label>
            {selected && secOpts?.providers[selected] && (
              <div className="grid gap-3">
                {(secOpts.providers[selected] as { fields: Array<{ name: string; label: string; kind: string; secret?: boolean; options?: string[] }> }).fields.map((f) => (
                  <label key={f.name} className="grid gap-1 text-xs text-gray-500">
                    {f.label}
                    {f.kind === "select" ? (
                      <select className="border rounded-lg px-3 py-2 text-sm" value={(secData?.providers[selected]?.[f.name] as string) || ""} onChange={(e) => updateField(sec, selected, f.name, e.target.value)}>
                        {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                      </select>
                    ) : (
                      <input className="border rounded-lg px-3 py-2 text-sm" type={f.secret ? "password" : "text"} value={(secData?.providers[selected]?.[f.name] as string) || ""} onChange={(e) => updateField(sec, selected, f.name, e.target.value)} />
                    )}
                  </label>
                ))}
              </div>
            )}
            <button className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm" onClick={() => saveSection(sec)}>保存 {labels[sec]} 配置</button>
          </section>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: 更新 App.tsx 路由**

```tsx
import ConfigPage from "./pages/ConfigPage";
<Route path="/config" element={<ConfigPage />} />
```

- [ ] **Step 3: 修改 FastAPI serve 静态文件**

在 `app.py` 中添加静态文件 mount：

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 在 create_app() 内，所有路由注册完之后：
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
```

- [ ] **Step 4: 添加 CORS 支持（开发用）**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/pages/ConfigPage.tsx frontend/src/App.tsx apps/control_plane/app.py
git commit -m "feat: ConfigPage + FastAPI 静态文件 serve + CORS"
```

---

### Task 11: 集成验证与清理

**Files:** 无新增，验证和清理

- [ ] **Step 1: 构建前端**

```bash
cd frontend && npm run build
```

Expected: `frontend/dist/` 生成，无 TS 错误

- [ ] **Step 2: 启动完整栈验证**

```bash
# 终端 1
uv run python -m apps.control_plane

# 终端 2（如果 dist 已生成）
curl http://localhost:17890/
```

Expected: 返回 React SPA 的 index.html

- [ ] **Step 3: 运行所有现有测试**

```bash
uv run pytest tests/ -q
```

Expected: 62+ passed

- [ ] **Step 4: 停止 visual companion 服务器（如果还在运行）**

```bash
bash /Users/rolex/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills/brainstorming/scripts/stop-server.sh "/Users/rolex/Documents/Codes/githubProject/MyProject/video pipeline 2.0/.superpowers/brainstorm/1929-1779179860"
```

- [ ] **Step 5: 提交**

```bash
git add frontend/dist/.gitkeep
git commit -m "chore: 前端构建验证，visual companion 清理"
```

---

## 实施顺序

```
Task 0 (Phase2 merge) ──┬── Task 1 (脚手架) ── Task 2 (类型+API客户端)
                        │
                        ├── Task 3 (后端-项目素材)
                        ├── Task 4 (后端-Job审核)
                        └── Task 5 (后端-排期SQLite)
                                          │
                    ┌─────────────────────┘
                    ▼
         Task 6 (共享组件)
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
    Task 7     Task 8     Task 10
  (项目列表)  (工作台)   (配置页)
         │          │          │
         └──────────┼──────────┘
                    ▼
             Task 9 (流水线)
                    │
                    ▼
             Task 11 (集成验证)
```

Task 0-5 可并行（后端与前端脚手架互不依赖），Task 6-10 按页面顺序执行，Task 11 最后。

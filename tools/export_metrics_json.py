"""Export metrics.db → JSON files for static GitHub Pages deployment.

Usage:
    uv run python tools/export_metrics_json.py [--db PATH] [--out DIR]
    uv run python tools/export_metrics_json.py --current YYYY-MM-DD --previous YYYY-MM-DD [--out DIR]

This reads the same metrics.db used by the control plane and writes
overview.json, videos.json, and topics.json consumable by the
standalone AnalyticsStaticPage on GitHub Pages.

When ``--current`` and ``--previous`` are both provided, it writes
``increment.json`` and ``increment-detail.json`` instead.
"""

from __future__ import annotations

import json
import sqlite3
from argparse import ArgumentParser
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from apps.control_plane.services.metrics import MetricsStore

_INT_FIELDS = {
    "plays",
    "likes",
    "comments",
    "shares",
    "followers_gained",
    "exposure",
    "favorites",
    "danmaku",
    "forward_count",
}
_REAL_FIELDS = {"completion_rate", "avg_watch_duration", "cover_click_rate"}


def export_all(db_path: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        _export_overview(conn, out_dir)
        _export_videos(conn, out_dir)
        _export_topics(conn, out_dir)
    finally:
        conn.close()

    print(f"Exported to {out_dir}/")
    for f in sorted(out_dir.iterdir()):
        size = f.stat().st_size
        print(f"  {f.name}  ({size / 1024:.1f} KB)")


# ── Row helpers ──────────────────────────────────────────────


def _row_dict(r: sqlite3.Row) -> dict:
    d = dict(r)
    for k in list(d.keys()):
        if k in _INT_FIELDS:
            d[k] = d[k] if d[k] is not None else 0
        elif k in _REAL_FIELDS:
            d[k] = d[k] if d[k] is not None else 0
        elif k in ("title", "publish_date", "platform_id", "job_id"):
            d[k] = d[k] or ""
    # Parse JSON fields
    for field in ("used_asset_ids", "extra"):
        raw = d.get(field)
        if isinstance(raw, str):
            try:
                d[field] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                d[field] = [] if field == "used_asset_ids" else None
        elif field == "used_asset_ids" and raw is None:
            d[field] = []
    return d


# ── Overview ─────────────────────────────────────────────────


def _export_overview(conn: sqlite3.Connection, out_dir: Path) -> None:
    """Write overview.json — all daily data; frontend computes range."""
    daily_rows = conn.execute(
        """SELECT
                publish_date,
                COALESCE(SUM(plays), 0)            AS plays,
                COALESCE(SUM(likes), 0)            AS likes,
                COALESCE(SUM(followers_gained), 0)  AS followers,
                COALESCE(AVG(completion_rate), 0)   AS avg_completion
            FROM video_metrics
            GROUP BY publish_date
            ORDER BY publish_date""",
    ).fetchall()

    overview = {
        "total_plays": 0,
        "total_likes": 0,
        "total_followers": 0,
        "avg_completion": 0,
        "video_count": 0,
        "daily": [dict(r) for r in daily_rows],
    }
    (out_dir / "overview.json").write_text(
        json.dumps(overview, ensure_ascii=False, indent=2)
    )


# ── Videos ───────────────────────────────────────────────────


def _export_videos(conn: sqlite3.Connection, out_dir: Path) -> None:
    """Write videos.json — all records, no pagination."""
    rows = conn.execute(
        "SELECT * FROM video_metrics ORDER BY publish_date DESC"
    ).fetchall()
    items = [_row_dict(r) for r in rows]
    (out_dir / "videos.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2)
    )


# ── Topics ───────────────────────────────────────────────────


def _export_topics(conn: sqlite3.Connection, out_dir: Path) -> None:
    """Write topics.json — top 10 keywords by total plays (last 30 days)."""
    cutoff = (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%d")

    rows = conn.execute(
        "SELECT title, plays, completion_rate FROM video_metrics WHERE publish_date >= ?",
        (cutoff,),
    ).fetchall()

    agg: dict[str, dict] = {}
    for r in rows:
        for kw in _extract_keywords(r["title"]):
            bucket = agg.setdefault(
                kw, {"total_plays": 0, "video_count": 0, "_sum_cr": 0.0, "_count_cr": 0}
            )
            bucket["total_plays"] += r["plays"] or 0
            bucket["video_count"] += 1
            if r["completion_rate"] is not None:
                bucket["_sum_cr"] += r["completion_rate"]
                bucket["_count_cr"] += 1

    topics = []
    for kw, v in agg.items():
        avg_cr = round(v["_sum_cr"] / v["_count_cr"], 2) if v["_count_cr"] else 0.0
        topics.append(
            {
                "keyword": kw,
                "total_plays": v["total_plays"],
                "video_count": v["video_count"],
                "avg_completion": avg_cr,
            }
        )

    topics.sort(key=lambda x: x["total_plays"], reverse=True)
    (out_dir / "topics.json").write_text(
        json.dumps(topics[:10], ensure_ascii=False, indent=2)
    )


_STOPWORDS: set[str] = {
    "的",
    "了",
    "在",
    "是",
    "我",
    "有",
    "和",
    "就",
    "不",
    "人",
    "都",
    "一",
    "一个",
    "上",
    "也",
    "很",
    "到",
    "说",
    "要",
    "去",
    "你",
    "会",
    "着",
    "没有",
    "看",
    "好",
    "自己",
    "这",
    "他",
    "她",
    "它",
    "们",
    "那",
    "这个",
    "那个",
    "什么",
    "怎么",
    "可以",
    "没",
    "还",
    "把",
    "让",
    "跟",
    "从",
    "被",
    "用",
    "对",
    "做",
    "来",
    "给",
    "吗",
    "吧",
    "啊",
    "呢",
    "哦",
    "嗯",
    "啦",
    "哈",
    "呀",
    "嘛",
    "而",
    "但",
    "可是",
    "但是",
    "因为",
    "所以",
    "如果",
    "虽然",
    "不过",
    "或者",
    "还是",
    "就是",
    "已经",
    "非常",
    "比较",
    "可能",
    "而且",
    "然后",
    "其实",
    "只是",
    "真是",
    "真的",
    "一下",
    "出来",
    "起来",
    "下来",
    "上去",
    "过来",
    "过去",
}


def _extract_keywords(title: str) -> list[str]:
    import re

    tokens = re.split(r"[#，,。！？、\s]+", title.strip())
    return [t for t in tokens if len(t) >= 2 and t not in _STOPWORDS]


# ── CLI ──────────────────────────────────────────────────────


def main() -> None:
    parser = ArgumentParser(description="Export metrics.db to static JSON files")
    parser.add_argument("--db", default=None, help="Path to metrics.db (auto-detect)")
    parser.add_argument(
        "--out", default="dist", help="Output directory (default: dist/)"
    )
    parser.add_argument(
        "--current",
        default=None,
        help="Current snapshot date (YYYY-MM-DD) for increment export",
    )
    parser.add_argument(
        "--previous",
        default=None,
        help="Previous snapshot date (YYYY-MM-DD) for increment export",
    )
    args = parser.parse_args()

    out_dir = Path(args.out)

    # Auto-detect db path
    if args.db:
        db_path = args.db
    else:
        # Try common locations relative to this script
        here = Path(__file__).resolve().parent.parent
        candidates = [
            here / "data" / "metrics.db",
            here / "workspace" / "data" / "metrics.db",
        ]
        found = [p for p in candidates if p.exists()]
        if not found:
            parser.error(
                "Cannot find metrics.db. Specify --db or create data/metrics.db "
                "in the project root."
            )
        db_path = str(found[0])

    # Increment mode
    if args.current and args.previous:
        store = MetricsStore(db_path=db_path)
        increment = store.compute_increment(
            args.current, args.previous, include_detail=True
        )

        out_dir.mkdir(parents=True, exist_ok=True)

        # increment.json — summary + top_gainers + daily_trend
        inc_out: dict[str, Any] = {
            "snapshot_date": increment["snapshot_date"],
            "previous_snapshot": increment["previous_snapshot"],
            "summary": increment["summary"],
            "top_gainers": increment["top_gainers"],
            "daily_trend": increment["daily_trend"],
        }
        (out_dir / "increment.json").write_text(
            json.dumps(inc_out, ensure_ascii=False, indent=2)
        )

        # increment-detail.json — full detail array
        (out_dir / "increment-detail.json").write_text(
            json.dumps(increment["detail"], ensure_ascii=False, indent=2)
        )

        print(f"Exported increment data to {out_dir}/")
        for f in sorted(out_dir.iterdir()):
            size = f.stat().st_size
            print(f"  {f.name}  ({size / 1024:.1f} KB)")
        return

    export_all(db_path, out_dir)


if __name__ == "__main__":
    main()

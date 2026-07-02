"""Tests for MetricsStore.compute_increment() — day-over-day delta computation."""

from __future__ import annotations

import pytest

from apps.control_plane.services.metrics import MetricsStore


def _create_increment_table(store: MetricsStore) -> None:
    """Recreate the video_metrics table WITHOUT the UNIQUE constraint.

    The production table has UNIQUE(platform, title, publish_date) preventing
    two records for the same video key. For increment testing we need both
    the PREVIOUS and CURRENT snapshot versions of the same video to coexist.
    """
    conn = store._conn()
    try:
        conn.executescript("""
            DROP TABLE IF EXISTS video_metrics;
            CREATE TABLE video_metrics (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                platform        TEXT NOT NULL,
                title           TEXT NOT NULL,
                publish_date    TEXT NOT NULL,
                content_type    TEXT DEFAULT 'video',
                plays           INTEGER DEFAULT 0,
                likes           INTEGER DEFAULT 0,
                comments        INTEGER DEFAULT 0,
                shares          INTEGER DEFAULT 0,
                followers_gained INTEGER DEFAULT 0,
                completion_rate REAL,
                avg_watch_duration REAL,
                exposure        INTEGER DEFAULT 0,
                cover_click_rate REAL,
                favorites       INTEGER DEFAULT 0,
                danmaku         INTEGER DEFAULT 0,
                forward_count   INTEGER DEFAULT 0,
                extra           TEXT,
                job_id          TEXT,
                used_asset_ids  TEXT,
                imported_at     TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_metrics_platform ON video_metrics(platform);
            CREATE INDEX IF NOT EXISTS idx_metrics_date ON video_metrics(publish_date);
            CREATE INDEX IF NOT EXISTS idx_metrics_job ON video_metrics(job_id);
        """)
        conn.commit()
    finally:
        conn.close()


def _seed(
    store: MetricsStore,
    records: list[dict],
) -> None:
    """Insert raw records for increment tests.

    Each dict must include at minimum:
        platform, title, publish_date, imported_at
    """
    conn = store._conn()
    try:
        for rec in records:
            conn.execute(
                """INSERT INTO video_metrics
                   (platform, title, publish_date, plays, likes, comments,
                    shares, followers_gained, imported_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    rec["platform"],
                    rec["title"],
                    rec.get("publish_date"),
                    rec.get("plays", 0),
                    rec.get("likes", 0),
                    rec.get("comments", 0),
                    rec.get("shares", 0),
                    rec.get("followers_gained", 0),
                    rec["imported_at"],
                ),
            )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def store(tmp_path):
    s = MetricsStore(db_path=str(tmp_path / "test_metrics.db"))
    _create_increment_table(s)
    return s


CURRENT = "2026-07-02T12:00:00+00:00"
PREVIOUS = "2026-07-01T12:00:00+00:00"
CURRENT_DATE = "2026-07-02"
PREVIOUS_DATE = "2026-07-01"


class TestIncrementUpdated:
    """test_increment_updated — same video in both snapshots with different numbers."""

    def test_increment_updated(self, store):
        _seed(store, [
            {
                "platform": "weixin",
                "title": "相同视频",
                "publish_date": "2026-07-01",
                "plays": 100,
                "likes": 10,
                "followers_gained": 1,
                "shares": 2,
                "comments": 0,
                "imported_at": PREVIOUS,
            },
            {
                "platform": "weixin",
                "title": "相同视频",
                "publish_date": "2026-07-01",
                "plays": 150,
                "likes": 15,
                "followers_gained": 3,
                "shares": 5,
                "comments": 1,
                "imported_at": CURRENT,
            },
        ])

        result = store.compute_increment(CURRENT_DATE, PREVIOUS_DATE)

        assert result["summary"]["updated_videos"] == 1
        assert result["summary"]["new_videos"] == 0
        assert result["summary"]["disappeared_videos"] == 0
        assert result["summary"]["plays_delta"] == 50
        assert result["summary"]["likes_delta"] == 5
        assert result["summary"]["followers_delta"] == 2
        assert result["summary"]["shares_delta"] == 3
        assert result["summary"]["comments_delta"] == 1


class TestIncrementNew:
    """test_increment_new — video only in the current snapshot."""

    def test_increment_new(self, store):
        _seed(store, [
            {
                "platform": "xiaohongshu",
                "title": "全新视频",
                "publish_date": "2026-07-02",
                "plays": 200,
                "likes": 20,
                "followers_gained": 5,
                "shares": 10,
                "comments": 3,
                "imported_at": CURRENT,
            },
        ])

        result = store.compute_increment(CURRENT_DATE, PREVIOUS_DATE)

        assert result["summary"]["new_videos"] == 1
        assert result["summary"]["updated_videos"] == 0
        assert result["summary"]["disappeared_videos"] == 0
        assert result["summary"]["plays_delta"] == 200
        assert result["summary"]["likes_delta"] == 20
        assert result["summary"]["followers_delta"] == 5
        assert result["summary"]["shares_delta"] == 10
        assert result["summary"]["comments_delta"] == 3

        # Top gainers should include it
        assert len(result["top_gainers"]) == 1
        assert result["top_gainers"][0]["title"] == "全新视频"
        assert result["top_gainers"][0]["plays_delta"] == 200


class TestIncrementDisappeared:
    """test_increment_disappeared — video only in the previous snapshot."""

    def test_increment_disappeared(self, store):
        _seed(store, [
            {
                "platform": "weixin",
                "title": "消失的视频",
                "publish_date": "2026-06-30",
                "plays": 50,
                "imported_at": PREVIOUS,
            },
        ])

        result = store.compute_increment(CURRENT_DATE, PREVIOUS_DATE)

        assert result["summary"]["disappeared_videos"] == 1
        assert result["summary"]["new_videos"] == 0
        assert result["summary"]["updated_videos"] == 0
        assert result["summary"]["plays_delta"] == 0
        assert result["summary"]["likes_delta"] == 0
        assert result["summary"]["followers_delta"] == 0
        assert result["summary"]["shares_delta"] == 0
        assert result["summary"]["comments_delta"] == 0


class TestIncrementMixed:
    """test_increment_mixed — 3 new + 5 updated + 1 disappeared."""

    def test_increment_mixed(self, store):
        records = []

        # 1 disappeared — only in previous
        records.append({
            "platform": "weixin",
            "title": "消失视频",
            "publish_date": "2026-06-29",
            "plays": 30,
            "imported_at": PREVIOUS,
        })

        # 5 updated — same titles in both snapshots
        for i in range(1, 6):
            records.append({
                "platform": "weixin",
                "title": f"更新视频{i}",
                "publish_date": f"2026-07-0{i}",
                "plays": 100 * i,
                "likes": 10 * i,
                "imported_at": PREVIOUS,
            })
            records.append({
                "platform": "weixin",
                "title": f"更新视频{i}",
                "publish_date": f"2026-07-0{i}",
                "plays": 100 * i + 10,
                "likes": 10 * i + 1,
                "imported_at": CURRENT,
            })

        # 3 new — only in current
        for i in range(1, 4):
            records.append({
                "platform": "weixin",
                "title": f"新视频{i}",
                "publish_date": "2026-07-02",
                "plays": 50 * i,
                "likes": 5 * i,
                "imported_at": CURRENT,
            })

        _seed(store, records)

        result = store.compute_increment(CURRENT_DATE, PREVIOUS_DATE)

        assert result["summary"]["new_videos"] == 3
        assert result["summary"]["updated_videos"] == 5
        assert result["summary"]["disappeared_videos"] == 1

        # Updated plays: each 10 plays delta = 5 * 10 = 50
        # New plays: 50 + 100 + 150 = 300
        assert result["summary"]["plays_delta"] == 350

        # Updated likes: each 1 like delta = 5 * 1 = 5
        # New likes: 5 + 10 + 15 = 30
        assert result["summary"]["likes_delta"] == 35


class TestIncrementEmpty:
    """test_increment_empty — no records in either snapshot."""

    def test_increment_empty(self, store):
        result = store.compute_increment(CURRENT_DATE, PREVIOUS_DATE)

        assert result["summary"]["new_videos"] == 0
        assert result["summary"]["updated_videos"] == 0
        assert result["summary"]["disappeared_videos"] == 0
        assert result["summary"]["plays_delta"] == 0
        assert result["summary"]["likes_delta"] == 0
        assert result["summary"]["followers_delta"] == 0
        assert result["summary"]["shares_delta"] == 0
        assert result["summary"]["comments_delta"] == 0
        assert result["top_gainers"] == []
        assert result["daily_trend"] == []


class TestIncrementPlatformFilter:
    """test_increment_platform_filter — filter by specific platform."""

    def test_increment_platform_filter(self, store):
        _seed(store, [
            # weixin — only in previous (will show as disappeared when filtered)
            {
                "platform": "weixin",
                "title": "微信视频",
                "publish_date": "2026-07-01",
                "plays": 100,
                "imported_at": PREVIOUS,
            },
            # xiaohongshu — both snapshots (will show as updated when filtered)
            {
                "platform": "xiaohongshu",
                "title": "小红书视频",
                "publish_date": "2026-07-01",
                "plays": 200,
                "imported_at": PREVIOUS,
            },
            {
                "platform": "xiaohongshu",
                "title": "小红书视频",
                "publish_date": "2026-07-01",
                "plays": 250,
                "imported_at": CURRENT,
            },
        ])

        # Only weixin records
        result_weixin = store.compute_increment(
            CURRENT_DATE, PREVIOUS_DATE, platform="weixin"
        )
        assert result_weixin["summary"]["disappeared_videos"] == 1
        assert result_weixin["summary"]["new_videos"] == 0
        assert result_weixin["summary"]["updated_videos"] == 0
        assert result_weixin["summary"]["plays_delta"] == 0

        # Only xiaohongshu records
        result_xhs = store.compute_increment(
            CURRENT_DATE, PREVIOUS_DATE, platform="xiaohongshu"
        )
        assert result_xhs["summary"]["updated_videos"] == 1
        assert result_xhs["summary"]["plays_delta"] == 50
        assert result_xhs["summary"]["new_videos"] == 0
        assert result_xhs["summary"]["disappeared_videos"] == 0
